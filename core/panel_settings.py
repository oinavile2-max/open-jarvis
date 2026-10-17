"""Validated, atomic panel preferences; contains no service credentials."""
from __future__ import annotations
import json
import math
import os
import re
from copy import deepcopy
from pathlib import Path
DEFAULTS={'accent':'#ff874b','opacity':.96,'animations':True,'quality':'balanced',
          'city':'','latitude':None,'longitude':None,'cards':{},'commands':[],
          'auto_overlay':True}
CARDS={'weather':(.025,.13,.25,.36),'clock':(.025,.53,.25,.29),
       'system':(.725,.13,.25,.30),'home':(.725,.47,.25,.35),
       'automation':(.30,.77,.40,.20)}
class PanelSettings:
    def __init__(self,path=None):
        self.path=Path(path) if path else Path(__file__).resolve().parents[1]/'config'/'premium_panel.json'
        self.data=deepcopy(DEFAULTS)
        try:
            raw=json.loads(self.path.read_text(encoding='utf-8'))
            if isinstance(raw,dict):self.data.update({k:v for k,v in raw.items() if k in DEFAULTS})
        except (OSError,ValueError):pass
        if not re.fullmatch(r'#[0-9a-fA-F]{6}',str(self.data['accent'])):self.data['accent']=DEFAULTS['accent']
        self.data['opacity']=self.number(self.data['opacity'],.60,1.,.96)
        if self.data['quality'] not in ('economy','balanced','premium'):self.data['quality']='balanced'
        self.data['animations']=bool(self.data['animations'])
        if not isinstance(self.data['cards'],dict):self.data['cards']={}
        if not isinstance(self.data['commands'],list):self.data['commands']=[]
        self.data['commands']=[c for c in self.data['commands'][:8] if isinstance(c,dict) and
                               isinstance(c.get('name'),str) and isinstance(c.get('text'),str)]
    @staticmethod
    def number(value,low,high,default):
        try:
            value=float(value)
            return max(low,min(high,value)) if math.isfinite(value) else default
        except (TypeError,ValueError):return default
    def card(self,key):
        default=CARDS[key]; saved=self.data['cards'].get(key,{})
        if not isinstance(saved,dict):saved={}
        values=saved.get('rect',default)
        if not isinstance(values,(list,tuple)) or len(values)!=4:values=default
        rect=[self.number(v,0,1,d) for v,d in zip(values,default)]
        rect[2]=max(.18,min(.7,rect[2]));rect[3]=max(.18,min(.7,rect[3]))
        rect[0]=min(rect[0],1.-rect[2]);rect[1]=max(.10,min(rect[1],1.-rect[3]))
        return rect,bool(saved.get('visible',True))
    def save(self):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        tmp=self.path.with_suffix('.tmp')
        try:
            tmp.write_text(json.dumps(self.data,ensure_ascii=False,indent=2),encoding='utf-8')
            os.replace(tmp,self.path)
        finally:
            tmp.unlink(missing_ok=True)
