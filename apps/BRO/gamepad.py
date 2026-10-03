"""Linux joydev adapter and action assigner. No controller output/rumble."""
import glob
import json
import os
from pathlib import Path
import struct
import time
import tkinter as tk
from tkinter import ttk

ACTIONS=('None','Look left','Look right','Center gaze','Turn left','Turn right','Next control','Weird burst','Previous speaker','Next speaker','Toggle camera','Fullscreen','Clear speaker chat')
DEFAULTS={'axis0-':'Look left','axis0+':'Look right','button0':'Next control','button1':'Weird burst','button4':'Previous speaker','button5':'Next speaker'}

class Decoder:
    def __init__(self):self.states={}
    def event(self,data):
        _,value,kind,number=struct.unpack('<IhBB',data)
        base=kind&0x7f
        if base==1:
            key='button'+str(number);state=bool(value)
        elif base==2:
            key='axis'+str(number);state=1 if value>16000 else -1 if value<-16000 else 0
        else:return None
        old=self.states.get(key,0);self.states[key]=state
        if kind&0x80 or state==old or not state:return None
        return key+('+' if state>0 else '-') if base==2 else key

class Gamepad:
    def __init__(self,console):
        self.console=console;self.app=console.app;self.fd=None;self.decoder=Decoder();self.next_scan=0;self.learning=False;self.learn_until=0
        self.path=Path.home()/'.config'/'skycorepi'/'gamepad.json'
        self.bindings=dict(DEFAULTS)
        try:
            data=json.loads(self.path.read_text())
            if isinstance(data,dict):self.bindings={k:v for k,v in data.items() if isinstance(k,str) and v in ACTIONS}
        except (OSError,ValueError):pass
        self.frame=ttk.LabelFrame(console.dev,text='Gamepad / assign actions',padding=6)
        self.frame.pack(fill='x',before=console.draft)
        self.status=tk.StringVar(value='Looking for gamepad…')
        ttk.Label(self.frame,textvariable=self.status,wraplength=290).pack(fill='x')
        self.device=tk.StringVar(value='Auto')
        self.devices=ttk.Combobox(self.frame,textvariable=self.device,state='readonly',values=['Auto'],width=24);self.devices.pack(fill='x')
        self.devices.bind('<<ComboboxSelected>>',lambda _:self.close())
        self.action=tk.StringVar(value='Next control')
        ttk.Combobox(self.frame,textvariable=self.action,values=ACTIONS,state='readonly',width=24).pack(fill='x')
        ttk.Button(self.frame,text='Learn next button / direction',command=self.learn).pack(fill='x')
        ttk.Button(self.frame,text='Cancel learn',command=self.cancel).pack(fill='x')
        ttk.Button(self.frame,text='Show bindings in log',command=lambda:self.app.log('Gamepad bindings: '+json.dumps(self.bindings))).pack(fill='x')
        ttk.Button(self.frame,text='Restore defaults',command=self.reset).pack(fill='x')

    def save(self):
        try:
            self.path.parent.mkdir(parents=True,exist_ok=True)
            temp=self.path.with_suffix('.tmp');temp.write_text(json.dumps(self.bindings,indent=2));temp.replace(self.path)
            self.app.log('Gamepad bindings saved')
        except OSError as exc:self.app.log('Gamepad save error: '+str(exc))

    def learn(self):
        if not self.console.active:return
        self.learning=True;self.learn_until=time.monotonic()+15
        self.status.set('Release stick, then press/move an input (15 s)')
    def cancel(self):self.learning=False;self.status.set('Learning cancelled')
    def reset(self):self.bindings=dict(DEFAULTS);self.save();self.cancel()

    def handle(self,key):
        if not self.console.active:return
        if self.learning:
            self.bindings[key]=self.action.get();self.learning=False;self.save()
            self.status.set(key+' → '+self.bindings[key]);self.app.log('Assigned '+key+' → '+self.bindings[key]);return
        action=self.bindings.get(key,'None')
        if action=='None':return
        self.status.set(key+' → '+action);self.app.log('Gamepad '+key+' → '+action)
        self.dispatch(action)

    def dispatch(self,action):
        if not self.console.active:return
        app=self.app
        commands={'Look left':lambda:setattr(app.face,'gaze',-1.0),'Look right':lambda:setattr(app.face,'gaze',1.0),'Center gaze':lambda:setattr(app.face,'gaze',0.0),'Turn left':lambda:app.turn(-1),'Turn right':lambda:app.turn(1),'Next control':app.tap,'Weird burst':app.weird,'Fullscreen':app.toggle_fullscreen,'Clear speaker chat':self.console.chat.clear_selected}
        if action in commands:commands[action]()
        elif action in ('Previous speaker','Next speaker'):
            from console import SPEAKERS
            i=SPEAKERS.index(self.console.speaker.get());self.console.speaker.set(SPEAKERS[(i+(-1 if action=='Previous speaker' else 1))%len(SPEAKERS)])
        elif action=='Toggle camera':
            self.console.camera_visible.set(not self.console.camera_visible.get());self.console.toggle_camera()

    def poll(self):
        now=time.monotonic()
        if not self.console.active:
            self.close();return
        if self.learning and now>self.learn_until:self.cancel()
        if self.fd is None and now>=self.next_scan:
            self.next_scan=now+2
            paths=sorted(glob.glob('/dev/input/js*'));self.devices['values']=['Auto']+paths
            target=paths[0] if paths and self.device.get()=='Auto' else self.device.get()
            if target=='Auto':self.status.set('No gamepad · connect USB controller');return
            try:
                self.fd=os.open(target,os.O_RDONLY|os.O_NONBLOCK);self.decoder=Decoder()
                self.status.set('Connected '+target);self.app.log('Gamepad connected: '+target)
            except OSError as exc:self.status.set('Gamepad: '+str(exc));return
        if self.fd is not None:
            try:
                for _ in range(64):
                    data=os.read(self.fd,8)
                    if not data:raise OSError('Gamepad disconnected')
                    if len(data)!=8:continue
                    key=self.decoder.event(data)
                    if key:self.handle(key)
            except BlockingIOError:pass
            except OSError as exc:self.app.log(str(exc));self.close();self.status.set('Disconnected · retrying')

    def close(self):
        if self.fd is not None:os.close(self.fd);self.fd=None
        self.learning=False
