#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <esp_system.h>

#if !defined(CONFIG_IDF_TARGET_ESP32S3)
#error BloomFace requires ESP32-S3
#endif

// ============================================================
// SKYCOREPI BRO — OLED-FIRST BENCH FIRMWARE
// ============================================================
// Proven Happy Jarz OLED wiring:
//   OLED VCC -> 3V3
//   OLED GND -> GND
//   OLED SDA -> GPIO8
//   OLED SCL -> GPIO6
//   I2C address 0x3C
//
// IMPORTANT: GPIO8 was previously the rotary encoder DT pin.
// The rotary is intentionally DISABLED in this firmware so the OLED owns
// GPIO8 cleanly. Unplug the rotary while testing this build.
//
// USB protocol remains BloomFace protocol 1 so SkyCorePi BRO can still
// identify/connect to this board. Encoder counters stay at zero until the
// rotary is moved to a new pin map in a later build.
// ============================================================

static constexpr uint8_t OLED_SDA_PIN = 8;
static constexpr uint8_t OLED_SCL_PIN = 6;
static constexpr uint8_t OLED_ADDR = 0x3C;
static constexpr int OLED_WIDTH = 128;
static constexpr int OLED_HEIGHT = 64;
static constexpr int OLED_RESET = -1;

static Adafruit_SSD1306 display(OLED_WIDTH, OLED_HEIGHT, &Wire, OLED_RESET);
static bool oledReady = false;
static uint32_t oledLast = 0;
static bool oledLastHost = false;

static uint32_t session = 0;
static uint32_t lastSend = 0;
static uint32_t lastHost = 0;
static String command;

static void drawStatus(bool force = false) {
  if (!oledReady) return;
  const uint32_t now = millis();
  const bool host = (now - lastHost) < 3000;
  if (!force && host == oledLastHost && now - oledLast < 1000) return;

  oledLast = now;
  oledLastHost = host;

  display.clearDisplay();
  display.setTextColor(SSD1306_WHITE);
  display.setTextSize(1);

  display.setCursor(0, 0);
  display.println("SKYCOREPI BRO");
  display.drawLine(0, 10, 127, 10, SSD1306_WHITE);

  display.setCursor(0, 16);
  display.println("BOARD: ESP32-S3");
  display.print("FW: 0.3.0  OLED: 0x");
  display.println(OLED_ADDR, HEX);
  display.print("USB: ");
  display.println(host ? "ONLINE" : "WAITING");
  display.println("SDA: GPIO8 SCL: GPIO6");
  display.print("UP: ");
  display.print(now / 1000UL);
  display.println("s");

  display.display();
}

static void initOled() {
  Wire.begin(OLED_SDA_PIN, OLED_SCL_PIN);
  oledReady = display.begin(SSD1306_SWITCHCAPVCC, OLED_ADDR);
  if (!oledReady) {
    Serial.println("BRO|WARN|message=OLED init failed");
    return;
  }
  drawStatus(true);
}

static void report(const char *type) {
  // Protocol-1 shape is preserved for the existing SkyCorePi BRO host app.
  // Rotary is disabled in this OLED-first bench build, so counters are zero.
  Serial.printf(
    "{\"type\":\"%s\",\"device\":\"BloomFace\",\"version\":\"0.3.0\",\"protocol\":1,"
    "\"session\":%lu,\"quarters\":0,\"taps\":0,\"holds\":0,\"button\":false,\"oled\":%s}\n",
    type,
    (unsigned long)session,
    oledReady ? "true" : "false"
  );
}

void setup() {
  Serial.begin(115200);
  command.reserve(40);
  session = esp_random();

  // OLED init follows the exact known-good Happy Jarz stack:
  // Wire.begin(SDA, SCL) + Adafruit_SSD1306 at 0x3C.
  initOled();
}

void loop() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') {
      command.trim();
      if (command == "HELLO") {
        lastHost = millis();
        report("hello");
        drawStatus(true);
      } else if (command == "KEEP") {
        lastHost = millis();
      }
      command = "";
    } else if (command.length() < 40) {
      command += c;
    } else {
      command = "";
    }
  }

  const uint32_t now = millis();
  if (now - lastHost < 3000 && now - lastSend >= 250) {
    lastSend = now;
    report("input");
  }

  drawStatus();
  delay(5);
}
