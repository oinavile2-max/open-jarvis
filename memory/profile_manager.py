from __future__ import annotations
import json, re, sys
from pathlib import Path
from datetime import datetime


def _base() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent

BASE = _base()
CFG = BASE / 'config' / 'api_keys.json'
PROFILES_DIR = BASE / 'memory' / 'profiles'
INDEX = PROFILES_DIR / 'profiles.json'


def _slug(name: str) -> str:
    s = re.sub(r'[^a-zA-Z0-9_-]+', '-', (name or '').strip()).strip('-').lower()
    return s or 'usuario'


def _load_cfg() -> dict:
    try: return json.loads(CFG.read_text(encoding='utf-8'))
    except Exception: return {}


def _save_cfg(data: dict) -> None:
    CFG.parent.mkdir(parents=True, exist_ok=True)
    CFG.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def list_profiles() -> list[dict]:
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    try:
        data = json.loads(INDEX.read_text(encoding='utf-8'))
        if isinstance(data, list) and data: return data
    except Exception: pass
    cfg = _load_cfg()
    name = (cfg.get('user_name') or 'Usuário').strip()
    p = {'id': _slug(name), 'name': name, 'language': 'pt-BR', 'city': '', 'created': datetime.now().isoformat(timespec='seconds')}
    INDEX.write_text(json.dumps([p], ensure_ascii=False, indent=2), encoding='utf-8')
    return [p]


def create_profile(name: str, **fields) -> dict:
    profiles = list_profiles()
    base = _slug(name); pid = base; n = 2
    ids = {p.get('id') for p in profiles}
    while pid in ids:
        pid=f'{base}-{n}'; n+=1
    p={'id':pid,'name':name.strip(),'language':'pt-BR','city':'','voice_style':'jarvis-br','created':datetime.now().isoformat(timespec='seconds')}
    p.update({k:v for k,v in fields.items() if v is not None})
    profiles.append(p)
    INDEX.write_text(json.dumps(profiles,ensure_ascii=False,indent=2),encoding='utf-8')
    (PROFILES_DIR/pid).mkdir(parents=True,exist_ok=True)
    return p


def get_active_profile_id() -> str:
    cfg=_load_cfg(); profiles=list_profiles(); ids={p.get('id') for p in profiles}
    pid=cfg.get('active_profile')
    return pid if pid in ids else profiles[0]['id']


def active_profile() -> dict:
    pid=get_active_profile_id()
    return next((p for p in list_profiles() if p.get('id')==pid), {'id':pid,'name':'Usuário','language':'pt-BR'})


def set_active_profile(profile_id: str) -> None:
    if profile_id not in {p.get('id') for p in list_profiles()}:
        raise ValueError('Perfil não encontrado')
    cfg=_load_cfg(); cfg['active_profile']=profile_id
    p=next(p for p in list_profiles() if p.get('id')==profile_id)
    cfg['user_name']=p.get('name','')
    _save_cfg(cfg)


def memory_path() -> Path:
    pid=get_active_profile_id()
    d=PROFILES_DIR/pid; d.mkdir(parents=True,exist_ok=True)
    return d/'long_term.json'
