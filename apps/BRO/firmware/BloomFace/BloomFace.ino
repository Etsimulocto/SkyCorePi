#include <Arduino.h>
#include <Wire.h>
#include <esp_system.h>
#if !defined(CONFIG_IDF_TARGET_ESP32S3)
#error BloomFace requires ESP32-S3
#endif

// ============================================================
// BLOOMFACE / BRO BOARD MAP
// ============================================================
// Rotary encoder:
//   GPIO7 = CLK
//   GPIO8 = DT
//   GPIO9 = SW
//
// Local service OLED (SSD1306-class, 128x64, I2C):
//   GPIO5 = SDA
//   GPIO6 = SCL
//   VCC   = 3V3
//   GND   = GND
//
// OLED is diagnostic-only. If it is absent or fails, the encoder/USB
// protocol continues working normally.
// ============================================================

constexpr int CLK_PIN=7, DT_PIN=8, SW_PIN=9;
constexpr int OLED_SDA=5, OLED_SCL=6;
constexpr uint8_t OLED_W=128, OLED_H=64;
uint8_t oledAddress=0;
bool oledReady=false;
uint32_t oledLast=0;

portMUX_TYPE encoderMux=portMUX_INITIALIZER_UNLOCKED;
volatile int32_t quarters=0;
volatile uint8_t previousAB=0;
DRAM_ATTR const int8_t transitions[16]={0,-1,1,0,1,0,0,-1,-1,0,0,1,0,1,-1,0};
uint32_t taps=0,holds=0,session=0,lastSend=0,lastHost=0;
bool rawButton=true,stableButton=true,longSent=false;
uint32_t changedAt=0,pressedAt=0;
String command;

// 5x7 font, ASCII 32..90. Lowercase is rendered as uppercase.
const uint8_t FONT5X7[][5] PROGMEM={
{0,0,0,0,0},{0,0,95,0,0},{0,7,0,7,0},{20,127,20,127,20},{36,42,127,42,18},{35,19,8,100,98},{54,73,85,34,80},{0,5,3,0,0},{0,28,34,65,0},{0,65,34,28,0},{20,8,62,8,20},{8,8,62,8,8},{0,80,48,0,0},{8,8,8,8,8},{0,96,96,0,0},{32,16,8,4,2},
{62,81,73,69,62},{0,66,127,64,0},{66,97,81,73,70},{33,65,69,75,49},{24,20,18,127,16},{39,69,69,69,57},{60,74,73,73,48},{1,113,9,5,3},{54,73,73,73,54},{6,73,73,41,30},{0,54,54,0,0},{0,86,54,0,0},{8,20,34,65,0},{20,20,20,20,20},{0,65,34,20,8},{2,1,81,9,6},{50,73,121,65,62},
{126,17,17,17,126},{127,73,73,73,54},{62,65,65,65,34},{127,65,65,34,28},{127,73,73,73,65},{127,9,9,9,1},{62,65,73,73,122},{127,8,8,8,127},{0,65,127,65,0},{32,64,65,63,1},{127,8,20,34,65},{127,64,64,64,64},{127,2,12,2,127},{127,4,8,16,127},{62,65,65,65,62},{127,9,9,9,6},{62,65,81,33,94},{127,9,25,41,70},{70,73,73,73,49},{1,1,127,1,1},{63,64,64,64,63},{31,32,64,32,31},{63,64,56,64,63},{99,20,8,20,99},{3,4,120,4,3},{97,81,73,69,67}
};

void oledCmd(uint8_t c){
  if(!oledReady)return;
  Wire.beginTransmission(oledAddress);Wire.write(0x00);Wire.write(c);
  if(Wire.endTransmission()!=0)oledReady=false;
}
void oledData(const uint8_t* data,size_t n){
  if(!oledReady)return;
  while(n){
    size_t chunk=min((size_t)16,n);
    Wire.beginTransmission(oledAddress);Wire.write(0x40);
    for(size_t i=0;i<chunk;i++)Wire.write(data[i]);
    if(Wire.endTransmission()!=0){oledReady=false;return;}
    data+=chunk;n-=chunk;
  }
}
void oledInit(){
  Wire.begin(OLED_SDA,OLED_SCL,400000);
  for(uint8_t a: { (uint8_t)0x3C,(uint8_t)0x3D }){
    Wire.beginTransmission(a);
    if(Wire.endTransmission()==0){oledAddress=a;break;}
  }
  if(!oledAddress)return;
  oledReady=true;
  const uint8_t init[]={0xAE,0xD5,0x80,0xA8,0x3F,0xD3,0x00,0x40,0x8D,0x14,0x20,0x00,0xA1,0xC8,0xDA,0x12,0x81,0x7F,0xD9,0xF1,0xDB,0x40,0xA4,0xA6,0xAF};
  for(uint8_t c:init)oledCmd(c);
}
void oledClear(){
  if(!oledReady)return;
  oledCmd(0x21);oledCmd(0);oledCmd(127);oledCmd(0x22);oledCmd(0);oledCmd(7);
  uint8_t zeros[16]={0};
  for(int i=0;i<64;i++)oledData(zeros,sizeof(zeros));
}
void oledPos(uint8_t x,uint8_t page){
  oledCmd(0x21);oledCmd(x);oledCmd(127);oledCmd(0x22);oledCmd(page);oledCmd(page);
}
void oledChar(char c){
  if(c>='a'&&c<='z')c-=32;
  uint8_t out[6]={0,0,0,0,0,0};
  if(c>=32&&c<=90){
    uint8_t idx=(uint8_t)c-32;
    for(int i=0;i<5;i++)out[i]=pgm_read_byte(&FONT5X7[idx][i]);
  }
  oledData(out,6);
}
void oledText(uint8_t x,uint8_t page,const String& s){
  if(!oledReady)return;
  oledPos(x,page);
  for(size_t i=0;i<s.length() && x+6<=128;i++,x+=6)oledChar(s[i]);
}
void oledRefresh(){
  if(!oledReady)return;
  int32_t q;portENTER_CRITICAL(&encoderMux);q=quarters;portEXIT_CRITICAL(&encoderMux);
  bool host=(millis()-lastHost)<3000;
  oledClear();
  oledText(0,0,"BRO / BLOOMFACE");
  oledText(0,2,"FW 0.2.0");
  oledText(0,3,String("USB ")+(host?"ONLINE":"WAIT"));
  oledText(0,4,String("ENC ")+q);
  oledText(0,5,String("TAP ")+taps+" HOLD "+holds);
  oledText(0,7,String("OLED ")+String(oledAddress,HEX));
}

void ARDUINO_ISR_ATTR rotate(){
  uint8_t ab=(digitalRead(CLK_PIN)<<1)|digitalRead(DT_PIN);
  portENTER_CRITICAL_ISR(&encoderMux);
  quarters+=transitions[(previousAB<<2)|ab];previousAB=ab;
  portEXIT_CRITICAL_ISR(&encoderMux);
}
void report(const char* type){
  int32_t q;portENTER_CRITICAL(&encoderMux);q=quarters;portEXIT_CRITICAL(&encoderMux);
  Serial.printf("{\"type\":\"%s\",\"device\":\"BloomFace\",\"version\":\"0.2.0\",\"protocol\":1,\"session\":%lu,\"quarters\":%ld,\"taps\":%lu,\"holds\":%lu,\"button\":%s,\"oled\":%s}\n",type,(unsigned long)session,(long)q,(unsigned long)taps,(unsigned long)holds,stableButton?"false":"true",oledReady?"true":"false");
}
void setup(){
  Serial.begin(115200);command.reserve(40);session=esp_random();
  pinMode(CLK_PIN,INPUT_PULLUP);pinMode(DT_PIN,INPUT_PULLUP);pinMode(SW_PIN,INPUT_PULLUP);
  previousAB=(digitalRead(CLK_PIN)<<1)|digitalRead(DT_PIN);
  rawButton=stableButton=digitalRead(SW_PIN);
  if(!stableButton)pressedAt=millis();
  attachInterrupt(digitalPinToInterrupt(CLK_PIN),rotate,CHANGE);
  attachInterrupt(digitalPinToInterrupt(DT_PIN),rotate,CHANGE);
  oledInit();
  if(oledReady)oledRefresh();
}
void loop(){
  while(Serial.available()){
    char c=Serial.read();
    if(c=='\n'){
      command.trim();
      if(command=="HELLO"){lastHost=millis();report("hello");}
      else if(command=="KEEP")lastHost=millis();
      command="";
    }else if(command.length()<40)command+=c;else command="";
  }
  uint32_t now=millis();bool b=digitalRead(SW_PIN);
  if(b!=rawButton){rawButton=b;changedAt=now;}
  if(now-changedAt>=25 && stableButton!=rawButton){
    stableButton=rawButton;
    if(!stableButton){pressedAt=now;longSent=false;}
    else if(!longSent){taps++;}
  }
  if(!stableButton && !longSent && now-pressedAt>=700){holds++;longSent=true;}
  // Only stream to an active host. This firmware never drives any motor/output GPIO.
  if(now-lastHost<3000 && now-lastSend>=30){lastSend=now;report("input");}
  if(oledReady && now-oledLast>=500){oledLast=now;oledRefresh();}
  delay(1);
}
