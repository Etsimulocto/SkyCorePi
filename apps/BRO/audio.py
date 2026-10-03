"""Stoppable subprocess audio adapter and Tk controls; no always-on capture."""
import json
import os
from pathlib import Path
import queue
import subprocess
import tempfile
import threading
import time
import tkinter as tk
from tkinter import ttk

RUNTIME=Path.home()/'.local'/'share'/'skycorepi'/'audio-venv'/'bin'/'python'
WORKER=Path(__file__).with_name('audio_worker.py')

class AudioEngine:
    def __init__(self):
        self.events=queue.Queue();self.lock=threading.Lock();self.process=None;self.epoch=0;self.finish_requested=False
    def run(self,request):
        self.cancel()
        epoch=self.epoch
        self.finish_requested=False
        def work():
            proc=None
            try:
                if not RUNTIME.is_file():raise RuntimeError('Audio runtime missing; run bash apps/BRO/install_audio.sh')
                with tempfile.TemporaryFile(mode='w+') as errors:
                    with self.lock:
                        if epoch!=self.epoch:return
                        proc=subprocess.Popen([str(RUNTIME),str(WORKER)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=errors,text=True,env=dict(os.environ,ORT_DISABLE_TELEMETRY="1"))
                        self.process=proc
                        proc.stdin.write(json.dumps(request)+'\n');proc.stdin.flush()
                        if self.finish_requested:proc.stdin.write('stop\n');proc.stdin.flush()
                    timeout=35 if request['operation']=='listen' else 120 if request['operation']=='speak' else 15
                    timed_out=threading.Event()
                    def expire():
                        if proc.poll() is None:timed_out.set();proc.kill()
                    timer=threading.Timer(timeout,expire);timer.start()
                    reported=False
                    try:
                        for line in proc.stdout:
                            event=json.loads(line)
                            if event['kind']=='error':reported=True
                            self.events.put((epoch,event))
                        code=proc.wait()
                        if code and not reported:
                            errors.seek(0);self.events.put((epoch,dict(kind='error',text=(f'Audio timed out after {timeout} seconds: ' if timed_out.is_set() else 'Audio worker stopped: ')+errors.read()[-2000:])))
                    finally:timer.cancel()
            except Exception as exc:self.events.put((epoch,dict(kind='error',text=str(exc))))
            finally:
                if proc is not None:
                    if proc.poll() is None:proc.kill();proc.wait()
                    for pipe in (proc.stdin,proc.stdout):
                        if pipe:pipe.close()
                with self.lock:
                    if self.process is proc:self.process=None
                self.events.put((epoch,dict(kind='exit')))
        threading.Thread(target=work,daemon=True).start()
    def finish(self):
        with self.lock:
            self.finish_requested=True
            if self.process and self.process.poll() is None:
                try:self.process.stdin.write('stop\n');self.process.stdin.flush()
                except (BrokenPipeError,OSError):pass
    def cancel(self):
        with self.lock:
            self.epoch+=1;proc=self.process;self.process=None
            if proc and proc.poll() is None:
                proc.terminate()
                try:proc.wait(timeout=.15)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    try:proc.wait(timeout=.15)
                    except subprocess.TimeoutExpired:pass

class AudioPanel:
    def __init__(self,console):
        self.console=console;self.app=console.app;self.engine=AudioEngine();self.busy=None;self.rows=[];self.next_scan=time.monotonic()+10;self.background_scan=False
        self.voices={s:'en_US-lessac-medium' for s in ('BRO','Sky','Cold','Monday','GRIT')}
        self.voice=tk.StringVar(value='en_US-lessac-medium');self.input=tk.StringVar(value='Auto');self.output=tk.StringVar(value='Auto')
        self.volume=tk.DoubleVar(value=.7);self.speed=tk.DoubleVar(value=1);self.muted=tk.BooleanVar(value=False);self.auto=tk.BooleanVar(value=False)
        self.status=tk.StringVar(value='Audio not checked');self.level=tk.DoubleVar(value=0)
        frame=ttk.LabelFrame(console.dev,text='Voice / microphone · local',padding=6);frame.pack(fill='x',before=console.draft)
        for text,var,attr in [('Microphone (Auto prefers USB)',self.input,'inputs'),('Output (Auto uses system default)',self.output,'outputs'),('Voice for selected character',self.voice,'voice_selector')]:
            ttk.Label(frame,text=text).pack(anchor='w')
            combo=ttk.Combobox(frame,textvariable=var,values=['Auto'] if attr!='voice_selector' else ['en_US-lessac-medium'],state='readonly');combo.pack(fill='x')
            combo.bind('<<ComboboxSelected>>',lambda _:self.changed());setattr(self,attr,combo)
        ttk.Button(frame,text='Detect / rescan audio',command=self.scan).pack(fill='x')
        for text,var,lo,hi in [('Volume',self.volume,0,1),('Speech speed',self.speed,.6,1.6)]:
            ttk.Label(frame,text=text).pack(anchor='w')
            ttk.Scale(frame,variable=var,from_=lo,to=hi,command=lambda _:self.changed()).pack(fill='x')
        ttk.Checkbutton(frame,text='Mute speech',variable=self.muted,command=self.mute).pack(anchor='w')
        ttk.Checkbutton(frame,text='Speak AI replies automatically',variable=self.auto,command=self.changed).pack(anchor='w')
        ttk.Button(frame,text='Test selected voice',command=lambda:self.speak(self.console.speaker.get(),'Hello Architect. Voice online.')).pack(fill='x')
        ttk.Button(frame,text='Read latest reply',command=self.read_latest).pack(fill='x')
        ttk.Button(frame,text='Stop speaking / cancel microphone',command=self.stop).pack(fill='x')
        ttk.Button(frame,text='Start listening (20 seconds max)',command=self.listen).pack(fill='x')
        ttk.Button(frame,text='Finish listening → chat draft',command=self.finish).pack(fill='x')
        ttk.Progressbar(frame,variable=self.level,maximum=.3).pack(fill='x')
        ttk.Label(frame,text='Input level while listening. Transcript goes to the draft; review it before Send.',wraplength=290).pack(fill='x')
        ttk.Label(frame,textvariable=self.status,wraplength=290).pack(fill='x')
        ttk.Button(frame,text='Copy audio diagnostics',command=self.copy).pack(fill='x')
        console.speaker.trace_add('write',lambda *_:self.voice.set(self.voices.get(console.speaker.get(),'en_US-lessac-medium')))
        if not self.app.demo:self.app.root.after(700,self.scan)
    def changed(self):
        self.voices[self.console.speaker.get()]=self.voice.get()
        if hasattr(self.app,'preferences'):self.app.save_preferences()
    def mute(self):
        if self.muted.get() and self.busy=='speak':self.stop()
        self.changed()
    def scan(self,background=False):
        if self.busy:return
        if not self.console.active:return
        self.background_scan=background;self.busy='devices'
        if not background:self.status.set('Detecting audio inputs / outputs…')
        self.engine.run(dict(operation='devices'))
    def speak(self,speaker,text):
        if not self.console.active or self.muted.get() or self.busy=='listen':return
        self.busy='speak';self.status.set('Preparing voice…')
        self.engine.run(dict(operation='speak',text=text,voice=self.voices.get(speaker,'en_US-lessac-medium'),output=self.output.get(),volume=self.volume.get(),speed=self.speed.get()))
    def read_latest(self):
        for message in reversed(self.console.messages):
            header,_,text=message.partition(': ')
            if '[input]' not in header:
                self.speak(header.split(' [',1)[0],text);return
        self.status.set('No reply to read')
    def listen(self):
        if not self.console.active or self.busy=='listen':return
        self.busy='listen';self.level.set(0);self.status.set('Opening selected microphone…')
        self.engine.run(dict(operation='listen',input=self.input.get()))
    def finish(self):
        if self.busy=='listen':self.engine.finish();self.status.set('Finishing transcript…')
    def stop(self):
        self.engine.cancel();self.busy=None;self.level.set(0);self.status.set('Audio stopped · microphone released')
    def summary(self):
        return f'Audio: {self.status.get()}\nInput={self.input.get()} Output={self.output.get()}\nVoice={self.voice.get()} mute={self.muted.get()} auto={self.auto.get()}\nDevices: '+json.dumps(self.rows)
    def copy(self):
        self.app.log(self.summary());self.app.root.clipboard_clear();self.app.root.clipboard_append(self.summary())
    def poll(self):
        now=time.monotonic()
        if now>=self.next_scan:
            self.next_scan=now+10
            if not self.busy and RUNTIME.is_file() and not self.app.demo:self.scan(background=True)
        for _ in range(20):
            try:epoch,event=self.engine.events.get_nowait()
            except queue.Empty:break
            if epoch!=self.engine.epoch or not self.console.active:continue
            kind=event['kind']
            if kind=='devices':
                changed=self.rows!=event['rows'];self.rows=event['rows']
                for field,combo in [('inputs',self.inputs),('outputs',self.outputs)]:
                    combo['values']=['Auto']+[str(d['index'])+': '+d['name'] for d in self.rows if d[field]>0]
                self.voice_selector['values']=event['voices']
                count=sum(d['inputs']>0 for d in self.rows)
                if not self.background_scan or changed:
                    self.status.set(f'Audio detected · {count} input devices · {len(event["voices"])} voices'+(' · no microphone found' if not count else ''))
                    self.app.log(self.summary())
            elif kind=='level':self.level.set(event['value'])
            elif kind=='transcript':
                text=event['text']
                if text:
                    entry=self.console.chat.entry
                    if entry.get('1.0','end').strip():entry.insert('end','\n')
                    entry.insert('end',text)
                    self.status.set('Transcript added to chat draft · review before Send')
                    self.app.log('Microphone transcript added to draft')
                else:self.status.set('No speech recognized · check input level / microphone selection')
            elif kind in ('status','done','error'):
                self.status.set(event['text'])
                if kind!='status' or self.busy!='listen':self.app.log('Audio: '+event['text'])
            elif kind=='exit':self.busy=None;self.level.set(0)
