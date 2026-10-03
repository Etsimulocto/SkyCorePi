"""Local hand recognition and deliberate, one-shot gesture actions."""
from pathlib import Path
import time
import tkinter as tk
from tkinter import ttk
from gamepad import ACTIONS

GESTURES=('Open_Palm','Closed_Fist','Thumb_Up','Thumb_Down','Victory','Pointing_Up','ILoveYou')
MODEL=Path.home()/'.cache'/'skycorepi'/'gesture_recognizer.task'
RUNTIME=Path.home()/'.local'/'share'/'skycorepi'/'vision-venv'/'bin'/'python'

class GestureGate:
    def __init__(self):self.reset()
    def reset(self):
        self.candidate=None;self.since=0;self.latched=False;self.release_at=None;self.last_seen=None
    def update(self,name,score,now,threshold=.7,hold=.6):
        # Missing/stalled frames must not count toward a hold or release.
        if self.last_seen is not None and now-self.last_seen>.6:
            self.candidate=None;self.release_at=None
        self.last_seen=now
        valid=name in GESTURES and score>=threshold
        if self.latched:
            if valid:self.release_at=None
            elif self.release_at is None:self.release_at=now
            elif now-self.release_at>=.4:self.reset()
            return None
        if not valid:self.candidate=None;return None
        if name!=self.candidate:self.candidate=name;self.since=now;return None
        if now-self.since>=hold:self.latched=True;return name
        return None

class HandRecognizer:
    def __init__(self):
        import mediapipe as mp
        if not MODEL.is_file():raise FileNotFoundError('Gesture model missing; run bash apps/BRO/install_vision.sh')
        self.mp=mp
        options=mp.tasks.vision.GestureRecognizerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=str(MODEL)),
            running_mode=mp.tasks.vision.RunningMode.VIDEO,num_hands=1)
        self.recognizer=mp.tasks.vision.GestureRecognizer.create_from_options(options)
        self.timestamp=0
    def detect(self,rgb):
        self.timestamp=max(self.timestamp+1,int(time.monotonic()*1000))
        result=self.recognizer.recognize_for_video(self.mp.Image(image_format=self.mp.ImageFormat.SRGB,data=rgb),self.timestamp)
        name=None;score=0
        if result.gestures and result.gestures[0]:
            category=result.gestures[0][0];name=category.category_name;score=float(category.score)
        landmarks=result.hand_landmarks[0] if result.hand_landmarks else []
        points=[(p.x,p.y) for p in landmarks]
        return name,score,points
    def close(self):self.recognizer.close()

class GesturePanel:
    def __init__(self,feed):
        self.feed=feed;self.app=feed.app;self.gate=GestureGate()
        self.bindings={g:'None' for g in GESTURES}
        self.enabled=tk.BooleanVar(value=False)
        self.threshold=tk.DoubleVar(value=.7);self.hold=tk.DoubleVar(value=.6)
        frame=ttk.LabelFrame(feed.frame,text='Hand signals / assign actions',padding=4);frame.pack(fill='x')
        ttk.Checkbutton(frame,text='Enable gesture actions',variable=self.enabled,command=self.changed).pack(anchor='w')
        self.status=tk.StringVar(value='Select Hands mode to recognize signals')
        ttk.Label(frame,textvariable=self.status,wraplength=290).pack(fill='x')
        self.signal=tk.StringVar(value='Victory');self.action=tk.StringVar(value='None')
        selector=ttk.Combobox(frame,textvariable=self.signal,values=GESTURES,state='readonly');selector.pack(fill='x')
        selector.bind('<<ComboboxSelected>>',lambda _:self.action.set(self.bindings[self.signal.get()]))
        ttk.Combobox(frame,textvariable=self.action,values=ACTIONS,state='readonly').pack(fill='x')
        ttk.Button(frame,text='Assign signal → action',command=self.assign).pack(fill='x')
        for text,var,lo,hi in [('Confidence',self.threshold,.5,.95),('Hold seconds',self.hold,.3,2)]:
            ttk.Label(frame,text=text).pack(anchor='w')
            ttk.Scale(frame,variable=var,from_=lo,to=hi,command=lambda _:self.changed()).pack(fill='x')
        ttk.Label(frame,text='Hold signal, then lower your hand to re-arm. None unassigns. Recognition stays local.',wraplength=290).pack(fill='x')
    def changed(self):
        self.gate.reset();self.app.save_preferences()
    def assign(self):
        self.bindings[self.signal.get()]=self.action.get();self.changed()
        self.app.log('Gesture assigned: '+self.signal.get()+' → '+self.action.get())
    def observation(self,value):
        error=value.get('error','')
        name=value.get('gesture');score=value.get('confidence',0)
        self.status.set(error or f'{name or "No recognized signal"} · {score:.0%}')
        if error or not self.enabled.get() or not self.app.console.active:
            self.gate.reset();return
        fired=self.gate.update(name,score,time.monotonic(),self.threshold.get(),self.hold.get())
        if fired:
            action=self.bindings.get(fired,'None')
            self.app.log('Gesture '+fired+' → '+action)
            self.app.console.gamepad.dispatch(action)
        if self.gate.latched:self.status.set((name or 'No signal')+' · lower hand to re-arm')
