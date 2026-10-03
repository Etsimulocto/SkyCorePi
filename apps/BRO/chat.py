"""Tk chat adapter; workers return data, and only the UI thread touches widgets."""
import queue
import threading
import time
import tkinter as tk
from tkinter import ttk
from backend import Backend

class ChatPanel:
    def __init__(self,console):
        self.console=console;self.app=console.app;self.backend=Backend();self.events=queue.Queue();self.epoch=0;self.busy=False;self.pending=None;self.phase="IDLE";self.phase_until=0;self.last_request=None
        frame=ttk.LabelFrame(console.dev,text='Local conversation',padding=6)
        frame.pack(fill='x',before=console.draft)
        self.model=tk.StringVar(value='qwen2.5:0.5b')
        self.models=ttk.Combobox(frame,textvariable=self.model,state='readonly',width=24);self.models.pack(fill='x')
        ttk.Button(frame,text='Detect models / diagnostics',command=self.detect).pack(fill='x')
        self.archive=tk.BooleanVar(value=False)
        ttk.Checkbutton(frame,text='Use local Spiralside archive',variable=self.archive).pack(anchor='w')
        self.entry=tk.Text(frame,height=3,width=28,wrap='word',bg='#13243a',fg='#d7fff6',insertbackground='white');self.entry.pack(fill='x',pady=4)
        self.send_button=ttk.Button(frame,text='Send to selected speaker',command=self.send);self.send_button.pack(fill='x')
        ttk.Button(frame,text='Clear selected speaker chat',command=self.clear_selected).pack(fill='x')
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
        self.pending=speaker;self.phase='THINKING';self.phase_until=0
        self.last_request={'speaker':speaker,'model':model,'started':time.monotonic()}
        self.busy=True;self.send_button.configure(state='disabled');self.status.set(speaker+' is thinking…')
        self.console.show_output('BRO',f'Architect → {speaker}: {text}',source='input')
        self.entry.delete('1.0','end');self.app.log('Chat request: '+speaker+' / '+model)
        archive=self.archive.get()
        def request():
            messages,sources=self.backend.prepare(speaker,text,archive)
            return speaker,text,self.backend.ask(model,messages),sources
        self.worker('reply',request,self.epoch)

    def invalidate(self):
        self.epoch+=1;self.busy=False;self.pending=None;self.phase="IDLE";self.phase_until=0;self.send_button.configure(state='normal');self.status.set('Session ended; pending replies discarded')

    def clear_selected(self):
        speaker=self.console.speaker.get()
        if self.pending==speaker:self.invalidate()
        self.backend.histories[speaker]=[]
        self.console.messages=[m for m in self.console.messages if not (m.startswith(speaker+' [') and not m.startswith('BRO [input]:')) and not m.startswith('BRO [input]: Architect → '+speaker+':')]
        self.console.set_text(self.console.speech,"\n\n".join(self.console.messages))
        self.status.set('Cleared conversation: '+speaker)
        self.app.log('Chat cleared: '+speaker+' (other histories retained)')

    def diagnostic_summary(self):
        r=self.last_request or {}
        return f"Chat diagnostics: selected speaker={self.console.speaker.get()} model={self.model.get()} phase={self.phase} endpoint={self.backend.url} last={r}"

    def poll(self):
        if self.phase=='REPLYING' and time.monotonic()>=self.phase_until:self.phase='IDLE'

        for _ in range(10):
            try:epoch,kind,result,error=self.events.get_nowait()
            except queue.Empty:break
            if epoch!=self.epoch or not self.console.active:continue
            if error:
                self.status.set('Local AI error: '+error);self.app.log(self.status.get())
                if kind=='reply':
                    self.phase='ERROR';self.last_request['elapsed_s']=round(time.monotonic()-self.last_request['started'],2);self.last_request['error']=error
                    self.app.log(self.diagnostic_summary())
            elif kind=='models':
                self.models['values']=result
                if result and self.model.get() not in result:self.model.set(result[0])
                self.status.set('Ollama ready · '+str(len(result))+' models' if result else 'No models installed')
                self.app.log(self.status.get())
            elif kind=='diagnostics':
                self.app.log(result);self.app.log(self.diagnostic_summary())
            elif kind=='reply':
                speaker,text,reply,sources=result
                self.backend.commit(speaker,text,reply)
                self.console.show_output(speaker,reply,source='local AI')
                self.phase='REPLYING';self.phase_until=time.monotonic()+3
                self.last_request['elapsed_s']=round(time.monotonic()-self.last_request['started'],2)
                self.status.set(f'Reply received: {speaker} · {self.last_request["elapsed_s"]} s')
                self.app.log(self.diagnostic_summary())
                if sources:self.app.log('Archive sources: '+', '.join(sources))
            if kind=='reply':self.busy=False;self.pending=None;self.send_button.configure(state='normal')
