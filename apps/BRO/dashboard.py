"""Live device status and explicit reconnect controls."""
import tkinter as tk
from tkinter import ttk

class Dashboard:
    def __init__(self,console):
        self.console=console;self.app=console.app
        frame=ttk.LabelFrame(console.dev,text='Devices / settings',padding=6)
        frame.pack(fill='x',before=console.draft)
        self.status=tk.StringVar()
        ttk.Label(frame,textvariable=self.status,wraplength=290,justify='left').pack(fill='x')
        for name,command in [('Reconnect USB',self.app.connect),('Reconnect gamepad',self.gamepad),('Detect / preview camera',self.camera),('Check Ollama',console.chat.detect),('Stop local AI',lambda:console.chat.power('stop')),('Start local AI',lambda:console.chat.power('start')),('Copy device diagnostics',self.copy),('Save settings',self.app.save_preferences)]:
            ttk.Button(frame,text=name,command=command).pack(fill='x')
    def gamepad(self):
        self.console.gamepad.close();self.console.gamepad.next_scan=0
    def camera(self):
        if not self.console.active:return
        if not self.console.camera_visible.get():self.console.camera_visible.set(True);self.console.toggle_camera()
        else:self.console.camera_feed.start()
    def summary(self):
        c=self.console;a=self.app
        return '\n'.join(['Session: '+('active' if c.active else 'ended'),
            'USB: '+(('connected '+a.port.get()) if a.ready else ('connecting '+a.port.get()) if a.usb.port else 'disconnected'),
            'Gamepad: '+('connected '+c.gamepad.device_path if c.gamepad.fd is not None else 'disconnected'),
            'Camera: '+c.camera_feed.status.get(),
            'Vision: '+c.camera_feed.vision_status.get(),
            'Gestures: '+('enabled' if c.camera_feed.gestures.enabled.get() else 'disabled')+' · '+c.camera_feed.gestures.status.get(),
            'Audio: '+c.audio.status.get(),
            'Ollama: '+c.chat.connection_status,
            'Model: '+c.chat.model.get()+' / Speaker: '+c.speaker.get()])
    def poll(self):self.status.set(self.summary())
    def copy(self):
        import json
        feed=self.console.camera_feed
        self.app.log('Camera controls: '+feed.tracking_values.get()+' · inverted='+str(feed.invert_x.get()))
        self.app.log('Gesture bindings: '+json.dumps(feed.gestures.bindings))
        self.app.log(self.console.audio.summary())
        self.app.log(self.summary());self.app.log(self.console.chat.diagnostic_summary());self.app.copy_log()
