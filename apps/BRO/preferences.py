"""Validated local UI preferences; conversation text is never persisted here."""
import json
import math
from pathlib import Path
import re

class Preferences:
    def __init__(self,path=None):self.path=Path(path) if path else Path.home()/'.config'/'skycorepi'/'settings.json'
    def load(self):
        try:data=json.loads(self.path.read_text())
        except (OSError,ValueError):return {}
        if not isinstance(data,dict):return {}
        clean={}
        for key in ('model','camera','gamepad','port','speaker'):
            if isinstance(data.get(key),str) and len(data[key])<256:clean[key]=data[key]
        if data.get('detent') in ('2','4'):clean['detent']=data['detent']
        for key in ('reverse','camera_invert_x','camera_overlay','camera_follow'):
            if type(data.get(key)) is bool:clean[key]=data[key]
        if data.get('camera_mode') in ('Off','Face','Motion','Hands'):clean['camera_mode']=data['camera_mode']
        for key,lo,hi in [('camera_smoothing',.02,.5),('camera_range',.2,1),('camera_center_delay',0,5),('gesture_confidence',.5,.95),('gesture_hold',.3,2)]:
            v=data.get(key)
            if type(v) in (int,float) and math.isfinite(v) and lo<=v<=hi:clean[key]=v
        from gestures import GESTURES
        from gamepad import ACTIONS
        if isinstance(data.get('gesture_bindings'),dict):clean['gesture_bindings']={k:v for k,v in data['gesture_bindings'].items() if k in GESTURES and v in ACTIONS}
        if isinstance(data.get('geometry'),str) and re.fullmatch(r'\d{3,4}x\d{3,4}(?:[+-]\d+[+-]\d+)?',data['geometry']):clean['geometry']=data['geometry']
        from appearance import validate
        clean["appearance"]=validate(data.get("appearance",{}))
        hues=data.get('hues',{})
        if isinstance(hues,dict):clean['hues']={k:v for k,v in hues.items() if k in ('BRO','Sky','Cold','Monday','GRIT') and type(v) in (int,float) and math.isfinite(v) and 0<=v<1}
        return clean
    def save(self,data):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        temp=self.path.with_suffix('.tmp');temp.write_text(json.dumps(data,indent=2));temp.replace(self.path)
