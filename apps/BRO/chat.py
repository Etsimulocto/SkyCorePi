"""Tk chat adapter; workers return data, and only the UI thread touches widgets."""
import queue
import threading
import tkinter as tk
from tkinter import ttk
from backend import Backend

class ChatPanel:
    def __init__(self,console):
        self.console=console;self.app=console.app;self.backend=Backend();self.events=queue.Queue();self.epoch=0;self.busy=False
        frame=ttk.LabelFrame(console.dev,text='Local conversation',padding=6)
        frame.pack(fill='x',before=console.draft)
        self.model=tk.StringVar(value='qwen2.5:0.5b')
        self.models=ttk.Combobox(frame,textvariable=self.model,state='readonly',width=24);self.models.pack(fill='x')
        ttk.Button(frame,text='Detect models / diagnostics',command=self.detect).pack(fill='x')
        self.archive=tk.BooleanVar(value=False)
        ttk.Checkbutton(frame,text='Use local Spiralside archive',variable=self.archive).pack(anchor='w')
        self.entry=tk.Text(frame,height=3,width=28,wrap='word',bg='#13243a',fg='#d7fff6',insertbackground='white');self.entry.pack(fill='x',pady=4)
        self.send_button=ttk.Button(frame,text='Send to selected speaker',command=self.send);self.send_button.pack(fill='x')
        self.status=tk.StringVar(value='Detecting local models…');ttk.Label(frame,textvariable=self.status,wraplength=290).pack(fill='x')
        self.detect()

    def worker(self,kind,fn,epoch):
        def run():
            try:self.events.put((epoch,kind,fn(),None))
            except Exception as exc:self.events.put((epoch,kind,None,str(exc)))
        threading.Thread(target=run,daemon=True).start()

    def detect(self):
        if not self.console.active:return
        self.status.set('Checking local Ollama…')
        self.worker('models',self.backend.models,self.epoch)
        from diagnostics import report
        self.worker('diagnostics',report,self.epoch)

    def send(self):
        if self.busy or not self.console.active:return
        text=self.entry.get('1.0','end').strip()[:4000]
        if not text:return
        speaker=self.console.speaker.get();model=self.model.get()
        self.busy=True;self.send_button.configure(state='disabled');self.status.set(speaker+' is thinking…')
        self.console.show_output('BRO',f'Architect → {speaker}: {text}',source='input')
        self.entry.delete('1.0','end');self.app.log('Chat request: '+speaker+' / '+model)
        archive=self.archive.get()
        def request():
            messages,sources=self.backend.prepare(speaker,text,archive)
            return speaker,text,self.backend.ask(model,messages),sources
        self.worker('reply',request,self.epoch)

    def invalidate(self):
        self.epoch+=1;self.busy=False;self.send_button.configure(state='normal');self.status.set('Session ended; pending replies discarded')

    def poll(self):
        for _ in range(10):
            try:epoch,kind,result,error=self.events.get_nowait()
            except queue.Empty:break
            if epoch!=self.epoch or not self.console.active:continue
            if error:
                self.status.set('Local AI error: '+error);self.app.log(self.status.get())
            elif kind=='models':
                self.models['values']=result
                if result and self.model.get() not in result:self.model.set(result[0])
                self.status.set('Ollama ready · '+str(len(result))+' models' if result else 'No models installed')
                self.app.log(self.status.get())
            elif kind=='diagnostics':self.app.log(result)
            elif kind=='reply':
                speaker,text,reply,sources=result
                self.backend.commit(speaker,text,reply)
                self.console.show_output(speaker,reply,source='local AI')
                self.status.set('Reply received: '+speaker)
                if sources:self.app.log('Archive sources: '+', '.join(sources))
            if kind=='reply':self.busy=False;self.send_button.configure(state='normal')
