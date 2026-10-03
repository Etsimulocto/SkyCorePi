"""Local webcam preview; capture lives in a stoppable child process."""
import glob
import multiprocessing as mp
import os
import queue
import sys
from gestures import GesturePanel, RUNTIME
import tkinter as tk
from tkinter import ttk
import time


def candidates():
    if os.name=='posix':
        return sorted(glob.glob('/dev/video*'),key=lambda p:int(p.removeprefix('/dev/video')) if p.removeprefix('/dev/video').isdigit() else 999)
    return list(range(4))


def capture_worker(messages,stop,source,vision_mode=None,vision_overlay=None):
    cap=None;tracker=None
    def send(kind,value):
        try:messages.put_nowait((kind,value))
        except queue.Full:pass
    try:
        from vision_runtime import restore_packages
        restore_packages()
        import cv2
        sources=candidates() if source=='Auto' else [int(source) if source.isdigit() else source]
        for device in sources:
            if stop.is_set():return
            cap=cv2.VideoCapture(device,cv2.CAP_V4L2 if os.name=='posix' else cv2.CAP_ANY)
            if cap.isOpened():
                cap.set(cv2.CAP_PROP_FRAME_WIDTH,640);cap.set(cv2.CAP_PROP_FRAME_HEIGHT,480)
                ok,frame=cap.read()
                if ok:break
            cap.release();cap=None
        else:
            send('error','No readable webcam. Check USB, permissions, or another camera app.');return
        send('status','Live camera: '+str(device))
        from vision import Tracker
        tracker=Tracker(cv2);last_frame=time.monotonic();fps=0
        while not stop.is_set():
            if vision_mode is not None:
                h,w=frame.shape[:2];scale=min(320/w,240/h)
                small=cv2.resize(frame,(max(1,int(w*scale)),max(1,int(h*scale))))
                observation=tracker.process(small,vision_mode.value,bool(vision_overlay.value))
                if observation is not None:
                    observation['fps']=round(fps,1);send('tracking',observation)
                frame=small
            now=time.monotonic();fps=.8*fps+.2/max(.001,now-last_frame);last_frame=now
            rgb=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
            h,w=rgb.shape[:2];scale=min(320/w,180/h)
            rgb=cv2.resize(rgb,(max(1,int(w*scale)),max(1,int(h*scale))))
            h,w=rgb.shape[:2]
            send('frame',f'P6\n{w} {h}\n255\n'.encode()+rgb.tobytes())
            if stop.wait(0.08):break
            ok,frame=cap.read()
            if not ok:
                send('error','Camera disconnected or stopped sending frames. Rescan to retry.');break
    except ImportError:
        send('error','Install python3-opencv, then restart the app.')
    except Exception as exc:
        send('error','Camera error: '+str(exc))
    finally:
        if tracker is not None:tracker.close()
        if cap is not None:cap.release()


class CameraPanel:
    def __init__(self,parent,app):
        self.app=app;self.process=None;self.messages=None;self.stop_event=None;self.photo=None;self.started=0;self.received=False
        self.frame=ttk.LabelFrame(parent,text='Camera preview · local',padding=6)
        self.source=tk.StringVar(value='Auto')
        self.selector=ttk.Combobox(self.frame,textvariable=self.source,state='readonly',width=14)
        self.selector.pack(fill='x');self.selector.bind('<<ComboboxSelected>>',lambda _:self.start())
        buttons=ttk.Frame(self.frame);buttons.pack(fill='x')
        ttk.Button(buttons,text='Detect / rescan',command=self.start).pack(side='left')
        ttk.Button(buttons,text='Stop',command=self.stop).pack(side='right')
        self.status=tk.StringVar(value='Preview stopped')
        ttk.Label(self.frame,textvariable=self.status,wraplength=290).pack(fill='x')
        ttk.Button(self.frame,text='Copy camera / vision status',command=self.copy_status).pack(fill='x')
        self.mode=tk.StringVar(value='Off');self.overlay=tk.BooleanVar(value=True)
        self.invert_x=tk.BooleanVar(value=True)
        self.follow=tk.BooleanVar(value=True);self.target=None;self.target_at=0;self.gaze_y=0;self.last_tracking=None
        self.vision_mode=None;self.vision_overlay=None
        self.smoothing=tk.DoubleVar(value=.12);self.gaze_range=tk.DoubleVar(value=1.0);self.center_delay=tk.DoubleVar(value=1.0)
        self.vision_status=tk.StringVar(value='Vision off')
        mode=ttk.Combobox(self.frame,textvariable=self.mode,values=('Off','Face','Motion','Hands'),state='readonly',width=14);mode.pack(fill='x')
        mode.bind('<<ComboboxSelected>>',lambda _:self.configure_vision())
        ttk.Checkbutton(self.frame,text='Tracking overlay',variable=self.overlay,command=self.configure_vision).pack(anchor='w')
        ttk.Checkbutton(self.frame,text='Eyes follow target',variable=self.follow,command=self.settings_changed).pack(anchor='w')
        ttk.Checkbutton(self.frame,text='Invert gaze X (left / right)',variable=self.invert_x,command=self.direction_changed).pack(anchor='w')
        ttk.Label(self.frame,textvariable=self.vision_status,wraplength=290).pack(fill='x')
        for text,var,lo,hi in [('Eye response (smooth → fast)',self.smoothing,.02,.5),('Eye movement range',self.gaze_range,.2,1),('Center after lost target (seconds)',self.center_delay,0,5)]:
            ttk.Label(self.frame,text=text).pack(anchor='w')
            ttk.Scale(self.frame,variable=var,from_=lo,to=hi,command=lambda _:self.settings_changed()).pack(fill='x')
        self.tracking_values=tk.StringVar()
        ttk.Label(self.frame,textvariable=self.tracking_values,wraplength=290).pack(fill='x')
        self.update_values()
        self.gestures=GesturePanel(self)
        self.image=ttk.Label(self.frame,anchor='center');self.image.pack(fill='x')

    def copy_status(self):
        text=self.status.get()+'\n'+self.vision_status.get()+'\n'+self.gestures.status.get()
        self.app.root.clipboard_clear();self.app.root.clipboard_append(text)
        self.app.log('Camera / vision status copied')

    def start(self):
        if not self.app.console.active:return
        self.stop(log=False)
        self.started=time.monotonic();self.received=False
        self.selector['values']=['Auto']+[str(x) for x in candidates()]
        self.status.set('Detecting camera…')
        context=mp.get_context('spawn')
        self.messages=context.Queue(maxsize=6);self.stop_event=context.Event()
        self.vision_mode=context.Value('i',('Off','Face','Motion','Hands').index(self.mode.get()));self.vision_overlay=context.Value('i',int(self.overlay.get()))
        self.process=context.Process(target=capture_worker,args=(self.messages,self.stop_event,self.source.get(),self.vision_mode,self.vision_overlay),daemon=True)
        if self.mode.get()=='Hands' and RUNTIME.is_file():mp.set_executable(str(RUNTIME))
        try:self.process.start()
        finally:mp.set_executable(sys.executable)
        self.app.log('Camera detection started: '+self.source.get())

    def update_values(self):
        self.tracking_values.set(f'Response {self.smoothing.get():.2f} · range {self.gaze_range.get():.0%} · center delay {self.center_delay.get():.1f}s')

    def settings_changed(self):
        self.update_values();self.app.save_preferences()

    def configure_vision(self,save=True):
        if self.vision_mode is not None:self.vision_mode.value=('Off','Face','Motion','Hands').index(self.mode.get())
        if self.vision_overlay is not None:self.vision_overlay.value=int(self.overlay.get())
        self.target=None;self.last_tracking=None
        self.gestures.gate.reset()
        if save:self.app.save_preferences()
        if self.process and self.mode.get()=='Hands':
            self.start();return
        self.vision_status.set('Vision '+self.mode.get())
        self.app.log('Vision mode: '+self.mode.get())

    def direction_changed(self):
        self.app.log('Camera gaze X inverted: '+str(self.invert_x.get()))
        self.app.save_preferences()

    def observation(self,value):
        self.target=value['target'];self.target_at=time.monotonic() if self.target is not None else self.target_at
        if self.mode.get()=='Hands':self.gestures.observation(value)
        state='tracking' if self.target is not None else 'searching'
        if value.get('error'):state=value['error']
        self.vision_status.set(f'{self.mode.get()}: {state} · {value["count"]} targets · {value["ms"]} ms · {value.get("fps",0)} FPS')
        if state!=self.last_tracking:self.app.log(self.vision_status.get());self.last_tracking=state

    def poll(self):
        if self.process and self.mode.get()!='Off' and self.follow.get() and self.app.console.active:
            x,y=self.target if self.target is not None and time.monotonic()-self.target_at<max(.6,self.center_delay.get()) else (None,None)
            if x is None and time.monotonic()-self.target_at>=self.center_delay.get():x,y=0,0
            if x is not None:
                x=-x if self.invert_x.get() else x
                x*=self.gaze_range.get();y*=self.gaze_range.get()
                self.app.face.gaze+=(x-self.app.face.gaze)*self.smoothing.get()
                self.gaze_y+=(y-self.gaze_y)*self.smoothing.get()
        else:self.gaze_y=0
        if not self.process:return
        for _ in range(4):
            try:kind,value=self.messages.get_nowait()
            except queue.Empty:break
            self.received=True
            if kind=='tracking':self.observation(value)
            elif kind=='frame':
                self.photo=tk.PhotoImage(data=value,format='PPM');self.image.configure(image=self.photo)
            else:
                self.status.set(value);self.app.log(value)
                if kind=='error':self.stop(log=False,clear=False);return
        if time.monotonic()-self.started>12 and not self.received:
            self.stop(log=False);self.status.set('Camera detection timed out. Select a device and rescan.');self.app.log(self.status.get())
        elif not self.process.is_alive() and self.received:
            self.stop(log=False,clear=False)

    def stop(self,log=True,clear=True):
        if self.process:
            self.stop_event.set();self.process.join(timeout=0.15)
            if self.process.is_alive():self.process.terminate();self.process.join(timeout=0.2)
            self.messages.close();self.process=None
            self.vision_mode=None;self.vision_overlay=None
            if log:self.app.log('Camera stopped')
        self.gestures.gate.reset()
        self.target=None;self.last_tracking=None;self.gaze_y=0;self.vision_status.set("Vision stopped")
        if clear:
            self.image.configure(image='');self.photo=None;self.status.set('Preview stopped')
