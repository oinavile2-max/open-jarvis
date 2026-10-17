from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / "config"

def load_json(name, default):
    p = CONFIG / name
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default.copy()

def save_json(name, data):
    p = CONFIG / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

class Panel(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("JARVIS — Painel de Configurações")
        self.geometry("1020x740")
        self.minsize(940, 680)

        ttk.Label(self, text="PAINEL DE CONFIGURAÇÕES DO JARVIS",
                  font=("Segoe UI", 20, "bold")).pack(pady=(16, 4))
        ttk.Label(self, text="Tudo em um único lugar — sem editar arquivos.").pack()

        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=16, pady=16)

        self.tabs = {}
        for name in [
            "Geral","IA","Voz","Ativação","Visual","Wallpaper",
            "Localização","Casa Inteligente","Device Link","Memória",
            "Plugins","Proatividade"
        ]:
            f = ttk.Frame(self.nb)
            self.nb.add(f, text=name)
            self.tabs[name] = f

        self._build_general()
        self._build_ai()
        self._build_voice()
        self._build_wake()
        self._build_visual()
        self._build_wallpaper()
        self._build_location()
        self._build_smart_home()
        self._build_device_link()
        self._build_memory()
        self._build_plugins()
        self._build_proactive()

        bar = ttk.Frame(self)
        bar.pack(fill="x", padx=16, pady=(0,16))
        ttk.Button(bar, text="SALVAR TUDO", command=self.save_all).pack(side="right")
        ttk.Button(bar, text="FECHAR", command=self.destroy).pack(side="right", padx=8)

    def section(self, parent, title, desc=""):
        ttk.Label(parent, text=title, font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=16, pady=(16,4))
        if desc:
            ttk.Label(parent, text=desc, wraplength=850).pack(anchor="w", padx=16)

    def row(self, parent, label, var, values=None, secret=False):
        f = ttk.Frame(parent); f.pack(fill="x", padx=16, pady=6)
        ttk.Label(f, text=label, width=30).pack(side="left")
        if values is None:
            w = ttk.Entry(f, textvariable=var, show="*" if secret else "")
        else:
            w = ttk.Combobox(f, textvariable=var, values=values, state="readonly")
        w.pack(side="left", fill="x", expand=True)
        return w

    def _build_general(self):
        p=self.tabs["Geral"]; self.section(p,"Geral","Perfil e inicialização.")
        cfg=load_json("user_setup.json",{})
        self.user_name=tk.StringVar(value=cfg.get("user_name",""))
        self.assistant_name=tk.StringVar(value=cfg.get("assistant_name","JARVIS"))
        self.language=tk.StringVar(value=cfg.get("language","pt-BR"))
        self.start_windows=tk.BooleanVar(value=cfg.get("start_with_windows",True))
        self.row(p,"Nome do usuário",self.user_name)
        self.row(p,"Nome do assistente",self.assistant_name)
        self.row(p,"Idioma",self.language,["pt-BR"])
        ttk.Checkbutton(p,text="Iniciar com o Windows",variable=self.start_windows).pack(anchor="w",padx=16,pady=8)

    def _build_ai(self):
        p=self.tabs["IA"]; self.section(p,"Inteligência Artificial","Groq e Gemini.")
        cfg=load_json("api_keys.json",{})
        self.ai_provider=tk.StringVar(value=cfg.get("fast_brain_provider","groq"))
        self.groq_key=tk.StringVar(value=cfg.get("groq_api_key",""))
        self.gemini_key=tk.StringVar(value=cfg.get("gemini_api_key","") or cfg.get("api_key",""))
        self.row(p,"Provedor principal",self.ai_provider,["groq","gemini"])
        self.row(p,"Chave Groq",self.groq_key,secret=True)
        self.row(p,"Chave Gemini",self.gemini_key,secret=True)
        f=ttk.Frame(p); f.pack(anchor="w",padx=16,pady=10)
        ttk.Button(f,text="TESTAR GROQ",command=self.test_groq).pack(side="left")
        ttk.Button(f,text="TESTAR GEMINI",command=self.test_gemini).pack(side="left",padx=8)

    def _build_voice(self):
        p=self.tabs["Voz"]; self.section(p,"Voz e Áudio","10 perfis prontos para escolher.")
        cfg=load_json("user_setup.json",{})
        api=load_json("api_keys.json",{})
        self.voice_enabled=tk.BooleanVar(value=cfg.get("voice_enabled",True))
        self.voice_profile=tk.StringVar(value=api.get("voice_profile","jarvis_official"))
        self.tts_rate=tk.StringVar(value=str(api.get("tts_rate","-6%")))
        self.tts_pitch=tk.StringVar(value=str(api.get("tts_pitch","-4Hz")))
        ttk.Checkbutton(p,text="Ativar respostas por voz",variable=self.voice_enabled).pack(anchor="w",padx=16,pady=8)
        self.row(p,"Perfil de voz",self.voice_profile,[
            "jarvis_official","jarvis_cinema","jarvis_classic","jarvis_fast","jarvis_deep","jarvis_soft",
            "jarvis_tactical","luxury","natural_br","assistant_light","night_mode"
        ])
        ttk.Button(p,text="APLICAR PERFIL DE VOZ",command=self.apply_voice_profile).pack(anchor="w",padx=16,pady=(4,8))
        self.row(p,"Velocidade",self.tts_rate,["-16%","-14%","-12%","-10%","-6%","-4%","0%","+3%","+4%","+8%"])
        self.row(p,"Grave / agudo",self.tts_pitch,["-8Hz","-7Hz","-6Hz","-5Hz","-4Hz","-2Hz","0Hz","+2Hz"])
        ttk.Button(p,text="ABRIR CONFIGURAÇÃO DE ÁUDIO",command=lambda:self.run("configurar_jarvis.py")).pack(anchor="w",padx=16,pady=8)

    def _build_wake(self):
        p=self.tabs["Ativação"]; self.section(p,"Ativação","Palma e palavra 'Jarvis'.")
        cfg=load_json("ux.json",{})
        self.clap=tk.BooleanVar(value=cfg.get("clap_wake",True))
        self.namewake=tk.BooleanVar(value=cfg.get("name_wake",True))
        ttk.Checkbutton(p,text="Acordar com 1 palma",variable=self.clap).pack(anchor="w",padx=16,pady=8)
        ttk.Checkbutton(p,text='Acordar ao ouvir "Jarvis"',variable=self.namewake).pack(anchor="w",padx=16,pady=8)

    def _build_visual(self):
        p=self.tabs["Visual"]; self.section(p,"Visual","Cara e efeitos neon.")
        cfg=load_json("ux.json",{})
        self.face=tk.StringVar(value=cfg.get("face","nebula"))
        self.neon=tk.BooleanVar(value=cfg.get("neon_multicolor",True))
        self.row(p,"Cara do JARVIS",self.face,["nebula","particle","reactor","orb","minimal"])
        ttk.Checkbutton(p,text="Usar cores neon por estado",variable=self.neon).pack(anchor="w",padx=16,pady=8)

    def _build_wallpaper(self):
        p=self.tabs["Wallpaper"]; self.section(p,"Wallpaper","Integração com o desktop do Windows.")
        cfg=load_json("wallpaper.json",{})
        self.wall_enabled=tk.BooleanVar(value=cfg.get("enabled",True))
        self.clickthrough=tk.BooleanVar(value=cfg.get("click_through",True))
        ttk.Checkbutton(p,text="Ativar modo wallpaper",variable=self.wall_enabled).pack(anchor="w",padx=16,pady=8)
        ttk.Checkbutton(p,text="Permitir clique através",variable=self.clickthrough).pack(anchor="w",padx=16,pady=8)

    def _build_location(self):
        p=self.tabs["Localização"]; self.section(p,"Localização","Windows, aproximada ou manual.")
        cfg=load_json("location.json",{})
        self.loc_enabled=tk.BooleanVar(value=cfg.get("enabled",False))
        self.loc_mode=tk.StringVar(value=cfg.get("mode","auto"))
        self.city=tk.StringVar(value=cfg.get("manual_city",""))
        self.region=tk.StringVar(value=cfg.get("manual_region",""))
        ttk.Checkbutton(p,text="Ativar localização",variable=self.loc_enabled).pack(anchor="w",padx=16,pady=8)
        self.row(p,"Modo",self.loc_mode,["auto","windows","approximate","manual"])
        self.row(p,"Cidade manual",self.city)
        self.row(p,"Estado/região manual",self.region)
        ttk.Button(p,text="TESTAR LOCALIZAÇÃO",command=self.test_location).pack(anchor="w",padx=16,pady=10)

    def _build_smart_home(self):
        p=self.tabs["Casa Inteligente"]; self.section(p,"Casa Inteligente","eWeLink, Home Assistant e Smart Life/Tuya.")
        ttk.Button(p,text="CONFIGURAR CASA INTELIGENTE",command=lambda:self.run("configurar_casa_inteligente.py")).pack(anchor="w",padx=16,pady=12)

    def _build_device_link(self):
        p=self.tabs["Device Link"]; self.section(p,"Device Link","Conecte a futura versão Android.")
        cfg=load_json("device_link.json",{})
        self.dl_enabled=tk.BooleanVar(value=cfg.get("enabled",True))
        self.dl_port=tk.StringVar(value=str(cfg.get("port",8767)))
        ttk.Checkbutton(p,text="Ativar Device Link",variable=self.dl_enabled).pack(anchor="w",padx=16,pady=8)
        self.row(p,"Porta local",self.dl_port)
        ttk.Label(p,text="F8 abre o pareamento no JARVIS.").pack(anchor="w",padx=16,pady=8)

    def _build_memory(self):
        p=self.tabs["Memória"]; self.section(p,"Memória","Perfis, histórico e Obsidian.")
        ttk.Button(p,text="ABRIR PASTA DE MEMÓRIA",command=self.open_memory).pack(anchor="w",padx=16,pady=12)

    def _build_plugins(self):
        p=self.tabs["Plugins"]; self.section(p,"Plugins","Integrações extras.")
        ttk.Label(p,text="Plugins avançados continuam disponíveis no JARVIS.").pack(anchor="w",padx=16,pady=8)

    def _build_proactive(self):
        p=self.tabs["Proatividade"]; self.section(p,"Chamadas Proativas","Como o JARVIS interrompe quando algo importante acontece.")
        cfg=load_json("proactive_call.json",{})
        self.pro_enabled=tk.BooleanVar(value=cfg.get("enabled",True))
        self.driving=tk.BooleanVar(value=cfg.get("driving_safe_mode",True))
        self.urgent=tk.BooleanVar(value=cfg.get("speak_urgent_only_while_driving",True))
        ttk.Checkbutton(p,text="Ativar chamadas proativas",variable=self.pro_enabled).pack(anchor="w",padx=16,pady=8)
        ttk.Checkbutton(p,text="Ativar modo direção seguro",variable=self.driving).pack(anchor="w",padx=16,pady=8)
        ttk.Checkbutton(p,text="Em direção, interromper só em alta prioridade",variable=self.urgent).pack(anchor="w",padx=16,pady=8)

    def apply_voice_profile(self):
        profiles = load_json("voice_profiles.json",{}).get("profiles",{})
        prof = profiles.get(self.voice_profile.get(),{})
        if not prof:
            return
        self.tts_rate.set(str(prof.get("rate","0%")))
        self.tts_pitch.set(str(prof.get("pitch","0Hz")))
        messagebox.showinfo(
            "JARVIS",
            f'{prof.get("label","Perfil")}\n\n{prof.get("description","")}\n\nClique em SALVAR TUDO para confirmar.'
        )

    def run(self, script):
        p=ROOT/script
        if p.exists():
            subprocess.Popen([sys.executable,str(p)],cwd=str(ROOT))
        else:
            messagebox.showerror("JARVIS",f"Arquivo não encontrado: {script}")

    def open_memory(self):
        p=ROOT/"memory"
        if p.exists():
            subprocess.Popen(["explorer",str(p)])

    def test_groq(self):
        import requests
        try:
            r=requests.get("https://api.groq.com/openai/v1/models",
                headers={"Authorization":f"Bearer {self.groq_key.get().strip()}"},
                timeout=8)
            r.raise_for_status()
            messagebox.showinfo("Groq","Conexão OK.")
        except Exception as e:
            messagebox.showerror("Groq",str(e))

    def test_gemini(self):
        import requests
        try:
            key=self.gemini_key.get().strip()
            r=requests.get(f"https://generativelanguage.googleapis.com/v1beta/models?key={key}",timeout=8)
            r.raise_for_status()
            messagebox.showinfo("Gemini","Conexão OK.")
        except Exception as e:
            messagebox.showerror("Gemini",str(e))

    def test_location(self):
        save_json("location.json",{
            "enabled":self.loc_enabled.get(),
            "mode":self.loc_mode.get(),
            "manual_city":self.city.get().strip(),
            "manual_region":self.region.get().strip(),
        })
        try:
            from core.location_service import get_location
            messagebox.showinfo("Localização",str(get_location()))
        except Exception as e:
            messagebox.showerror("Localização",str(e))

    def save_all(self):
        u=load_json("user_setup.json",{})
        u.update({
            "user_name":self.user_name.get().strip(),
            "assistant_name":self.assistant_name.get().strip() or "JARVIS",
            "language":self.language.get(),
            "voice_enabled":self.voice_enabled.get(),
            "start_with_windows":self.start_windows.get(),
        })
        save_json("user_setup.json",u)
        save_json("startup.json", {'start_with_windows':bool(self.start_windows.get())})

        a=load_json("api_keys.json",{})
        _profiles = load_json("voice_profiles.json",{}).get("profiles",{})
        _vp = _profiles.get(self.voice_profile.get(),{})
        a.update({
            "fast_brain_provider":self.ai_provider.get(),
            "groq_api_key":self.groq_key.get().strip(),
            "gemini_api_key":self.gemini_key.get().strip(),
            "voice_profile":self.voice_profile.get(),
            "voice_name":_vp.get("gemini_live_voice","Charon"),
            "tts_engine":"edgetts",
            "tts_voice":_vp.get("fallback_tts_voice","pt-BR-AntonioNeural"),
            "tts_rate":self.tts_rate.get(),
            "tts_pitch":self.tts_pitch.get(),
        })
        save_json("api_keys.json",a)

        ux=load_json("ux.json",{})
        ux.update({
            "clap_wake":self.clap.get(),
            "name_wake":self.namewake.get(),
            "face":self.face.get(),
            "neon_multicolor":self.neon.get(),
        })
        save_json("ux.json",ux)

        save_json("wallpaper.json",{
            "enabled":self.wall_enabled.get(),
            "click_through":self.clickthrough.get(),
            "hide_from_taskbar":True,
            "hotkey_toggle_window":"F10"
        })

        save_json("location.json",{
            "enabled":self.loc_enabled.get(),
            "mode":self.loc_mode.get(),
            "manual_city":self.city.get().strip(),
            "manual_region":self.region.get().strip(),
        })

        dl=load_json("device_link.json",{})
        dl.update({"enabled":self.dl_enabled.get(),"port":int(self.dl_port.get() or 8767)})
        save_json("device_link.json",dl)

        pro=load_json("proactive_call.json",{})
        pro.update({
            "enabled":self.pro_enabled.get(),
            "driving_safe_mode":self.driving.get(),
            "speak_urgent_only_while_driving":self.urgent.get(),
        })
        save_json("proactive_call.json",pro)

        messagebox.showinfo("JARVIS","Todas as configurações foram salvas.")

if __name__=="__main__":
    Panel().mainloop()
