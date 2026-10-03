"""Live appearance editor with validated, serializable theme values."""
import re
import tkinter as tk
from tkinter import ttk,colorchooser,font

COLORS={'background':'#060b15','panels':'#0d1727','header':'#0d1727','text':'#c7d3e9','muted':'#6a83a6','button':'#24354b','button_text':'#d7fff6','button_hover':'#345571','fields':'#13243a','field_text':'#d7fff6','face_background':'#060b15','grid':'#0e192a','scan_line':'#14263b','eye_shadow':'#13243a','pupils':'#071220','eye_highlight':'#d7fff6','cheeks':'#e992b8'}
DEFAULTS={**COLORS,'ui_font':'Sans','ui_size':11,'text_font':'Monospace','text_size':11,'face_font':'Monospace'}

def validate(data):
    if not isinstance(data,dict):return {}
    result={}
    for key in COLORS:
        if isinstance(data.get(key),str) and re.fullmatch(r'#[0-9a-fA-F]{6}',data[key]):result[key]=data[key]
    for key in ('ui_font','text_font','face_font'):
        if isinstance(data.get(key),str) and 0<len(data[key])<100:result[key]=data[key]
    for key in ('ui_size','text_size'):
        if type(data.get(key)) is int and 8<=data[key]<=24:result[key]=data[key]
    return result

class Appearance:
    def __init__(self,app):
        self.app=app;self.values=dict(DEFAULTS);self.window=None;self.variables={}
    def load(self,data):self.values={**DEFAULTS,**validate(data)};self.apply()
    def apply(self):
        v=self.values;r=self.app.root;s=ttk.Style(r)
        r.configure(bg=v['background'])
        ui=(v['ui_font'],v['ui_size'])
        for name in ('TFrame','TLabelframe','TLabelframe.Label','TLabel','TCheckbutton'):
            s.configure(name,background=v['panels'])
        for name in ('TLabel','TLabelframe.Label','TCheckbutton'):
            s.configure(name,foreground=v['text'],font=ui)
        s.configure('Header.TFrame',background=v['header']);s.configure('Header.TLabel',background=v['header'],foreground=v['text'])
        s.configure('TButton',background=v['button'],foreground=v['button_text'],font=ui)
        s.map('TButton',background=[('active',v['button_hover']),('disabled',v['panels'])],foreground=[('disabled',v['muted'])])
        for name in ('TCombobox','TSpinbox','TEntry'):
            s.configure(name,fieldbackground=v['fields'],foreground=v['field_text'],background=v['button'],font=ui)
            s.map(name,fieldbackground=[('readonly',v['fields'])],foreground=[('readonly',v['field_text'])])
        s.configure('Vertical.TScrollbar',background=v['button'],troughcolor=v['panels'])
        s.map('TCheckbutton',background=[('active',v['panels'])],foreground=[('active',v['text'])])
        def walk(widget):
            for child in widget.winfo_children():
                if isinstance(child,tk.Text):child.configure(bg=v['fields'],fg=v['field_text'],insertbackground=v['field_text'],selectbackground=v['button_hover'],font=(v['text_font'],v['text_size']))
                elif isinstance(child,tk.Canvas):child.configure(bg=v['panels'])
                elif isinstance(child,ttk.Label):
                    try:weight=font.Font(font=child.cget('font')).actual('weight')
                    except tk.TclError:weight='normal'
                    child.configure(font=(v['ui_font'],v['ui_size'],weight))
                walk(child)
        walk(r)
        self.app.canvas.configure(bg=v['face_background'])
        r.option_add('*TCombobox*Listbox.background',v['fields']);r.option_add('*TCombobox*Listbox.foreground',v['field_text']);r.option_add('*TCombobox*Listbox.font',ui)
    def open(self):
        if self.window is not None and self.window.winfo_exists():self.window.lift();return
        self.window=tk.Toplevel(self.app.root);self.window.title('BRO · Look Editor');self.window.geometry('520x710')
        container=ttk.Frame(self.window,padding=10);container.pack(fill='both',expand=True)
        canvas=tk.Canvas(container,highlightthickness=0);scroll=ttk.Scrollbar(container,orient='vertical',command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set);scroll.pack(side='right',fill='y');canvas.pack(fill='both',expand=True)
        rows=ttk.Frame(canvas);item=canvas.create_window(0,0,window=rows,anchor='nw')
        rows.bind('<Configure>',lambda _:canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.bind('<Configure>',lambda e:canvas.itemconfigure(item,width=e.width))
        self.variables={}
        for key in COLORS:
            row=ttk.Frame(rows,padding=3);row.pack(fill='x')
            ttk.Label(row,text=key.replace('_',' ').title(),width=19).pack(side='left')
            var=tk.StringVar(value=self.values[key]);self.variables[key]=var
            ttk.Entry(row,textvariable=var,width=10).pack(side='left',padx=5)
            ttk.Button(row,text='Pick',command=lambda k=key:self.pick(k)).pack(side='right')
        families=sorted(set(font.families(self.app.root)))
        for key in ('ui_font','text_font','face_font','ui_size','text_size'):
            row=ttk.Frame(rows,padding=3);row.pack(fill='x');ttk.Label(row,text=key.replace('_',' ').title(),width=19).pack(side='left')
            var=tk.StringVar(value=str(self.values[key]));self.variables[key]=var
            if key.endswith('size'):ttk.Spinbox(row,from_=8,to=24,textvariable=var,width=8).pack(side='left')
            else:ttk.Combobox(row,textvariable=var,values=families,width=25).pack(side='left')
        self.notice=tk.StringVar(value='Eye accents follow speaker colors; the COLOR control adjusts them.')
        ttk.Label(container,textvariable=self.notice,wraplength=460).pack(fill='x')
        bar=ttk.Frame(container);bar.pack(fill='x')
        ttk.Button(bar,text='Apply',command=self.update).pack(side='left')
        ttk.Button(bar,text='Save',command=self.save).pack(side='left',padx=5)
        ttk.Button(bar,text='Reset look',command=self.reset).pack(side='left')
        ttk.Button(bar,text='Close',command=self.window.destroy).pack(side='right')
        self.apply()
    def pick(self,key):
        value=colorchooser.askcolor(color=self.variables[key].get(),parent=self.window,title=key.replace('_',' ').title())[1]
        if value:self.variables[key].set(value);self.update()
    def update(self):
        data={k:var.get() for k,var in self.variables.items()}
        try:
            for key in ('ui_size','text_size'):data[key]=int(data[key])
        except ValueError:self.notice.set('Font sizes must be whole numbers from 8 to 24.');return False
        clean=validate(data)
        if len(clean)!=len(DEFAULTS):self.notice.set('Use six-digit hex colors and font sizes 8–24.');return False
        self.values=clean;self.apply();self.notice.set('Look applied');return True
    def save(self):
        if self.update():self.app.save_preferences();self.notice.set('Look saved' if not self.app.demo else 'Demo preview only')
    def reset(self):
        self.values=dict(DEFAULTS)
        for key,var in self.variables.items():var.set(str(self.values[key]))
        self.apply();self.notice.set('Default look restored; Save to keep it')
