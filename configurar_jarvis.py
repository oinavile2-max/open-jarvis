from __future__ import annotations
import json
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox
import requests
import subprocess
import sys
import os

ROOT = Path(__file__).resolve().parent
API_CFG = ROOT / "config" / "api_keys.json"
USER_CFG = ROOT / "config" / "user_setup.json"

def load_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default.copy()

def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def detect_audio():
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        ins, outs = [], []
        for i, d in enumerate(devices):
            name = d.get("name", f"Dispositivo {i}")
            if d.get("max_input_channels", 0) > 0:
                ins.append((i, name))
            if d.get("max_output_channels", 0) > 0:
                outs.append((i, name))
        return ins, outs
    except Exception:
        return [], []

class Wizard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Configuração inicial do JARVIS")
        self.geometry("860x640")
        self.minsize(820, 600)

        self.user_cfg = load_json(USER_CFG, {
            "completed": False,
            "user_name": "",
            "assistant_name": "JARVIS",
            "language": "pt-BR",
            "ai_provider": "groq",
            "voice_enabled": True,
            "wake_word_enabled": True,
            "wake_word": "jarvis",
            "wallpaper_enabled": True,
            "location_enabled": False,
            "smart_home_enabled": False,
            "start_with_windows": True,
        })
        self.api_cfg = load_json(API_CFG, {})

        ttk.Label(self, text="BEM-VINDO AO JARVIS", font=("Segoe UI", 22, "bold")).pack(pady=(18,4))
        ttk.Label(self, text="Configuração guiada para deixar tudo pronto sem editar arquivos.").pack()

        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=18, pady=18)

        self.pages = {}
        for name in ("Perfil", "Inteligência Artificial", "Áudio", "Integrações", "Finalizar"):
            f = ttk.Frame(self.nb)
            self.nb.add(f, text=name)
            self.pages[name] = f

        self._profile()
        self._ai()
        self._audio()
        self._integrations()
        self._finish()

    def row(self, parent, label, value="", secret=False):
        f = ttk.Frame(parent)
        f.pack(fill="x", padx=18, pady=8)
        ttk.Label(f, text=label, width=26).pack(side="left")
        var = tk.StringVar(value=value)
        ent = ttk.Entry(f, textvariable=var, show="*" if secret else "")
        ent.pack(side="left", fill="x", expand=True)
        return var

    def _profile(self):
        p = self.pages["Perfil"]
        ttk.Label(p, text="Seu perfil", font=("Segoe UI", 15, "bold")).pack(anchor="w", padx=18, pady=(18,4))
        ttk.Label(p, text="O JARVIS usa essas informações para personalizar respostas e memória.").pack(anchor="w", padx=18)
        self.user_name = self.row(p, "Seu nome", self.user_cfg.get("user_name",""))
        self.assistant_name = self.row(p, "Nome do assistente", self.user_cfg.get("assistant_name","JARVIS"))

        self.wallpaper = tk.BooleanVar(value=self.user_cfg.get("wallpaper_enabled", True))
        self.start_win = tk.BooleanVar(value=self.user_cfg.get("start_with_windows", True))
        ttk.Checkbutton(p, text="Usar JARVIS como wallpaper do Windows", variable=self.wallpaper).pack(anchor="w", padx=18, pady=(18,4))
        ttk.Checkbutton(p, text="Iniciar automaticamente com o Windows", variable=self.start_win).pack(anchor="w", padx=18)

    def _ai(self):
        p = self.pages["Inteligência Artificial"]
        ttk.Label(p, text="Cérebro do JARVIS", font=("Segoe UI", 15, "bold")).pack(anchor="w", padx=18, pady=(18,4))
        ttk.Label(p, text="Escolha o provedor principal. Você pode trocar depois.").pack(anchor="w", padx=18)

        f = ttk.Frame(p); f.pack(fill="x", padx=18, pady=14)
        ttk.Label(f, text="Provedor", width=26).pack(side="left")
        self.provider = tk.StringVar(value=self.user_cfg.get("ai_provider","groq"))
        cb = ttk.Combobox(f, textvariable=self.provider, values=["groq","gemini"], state="readonly")
        cb.pack(side="left", fill="x", expand=True)

        self.groq_key = self.row(p, "Chave Groq", self.api_cfg.get("groq_api_key",""), True)
        self.gemini_key = self.row(p, "Chave Gemini", self.api_cfg.get("gemini_api_key","") or self.api_cfg.get("api_key",""), True)

        btns = ttk.Frame(p); btns.pack(pady=12)
        ttk.Button(btns, text="TESTAR GROQ", command=self.test_groq).pack(side="left", padx=6)
        ttk.Button(btns, text="TESTAR GEMINI", command=self.test_gemini).pack(side="left", padx=6)
        self.ai_status = ttk.Label(p, text="Nenhuma conexão testada ainda.")
        self.ai_status.pack()

    def _audio(self):
        p = self.pages["Áudio"]
        ttk.Label(p, text="Voz e microfone", font=("Segoe UI", 15, "bold")).pack(anchor="w", padx=18, pady=(18,4))
        ttk.Label(p, text="O JARVIS pode detectar automaticamente os dispositivos de áudio.").pack(anchor="w", padx=18)

        self.voice_on = tk.BooleanVar(value=self.user_cfg.get("voice_enabled", True))
        self.wake_on = tk.BooleanVar(value=self.user_cfg.get("wake_word_enabled", True))
        ttk.Checkbutton(p, text="Ativar respostas por voz", variable=self.voice_on).pack(anchor="w", padx=18, pady=(14,4))
        ttk.Checkbutton(p, text='Ativar palavra de ativação "Jarvis"', variable=self.wake_on).pack(anchor="w", padx=18)

        ins, outs = detect_audio()
        self.input_map = ins
        self.output_map = outs

        f1 = ttk.Frame(p); f1.pack(fill="x", padx=18, pady=(18,8))
        ttk.Label(f1, text="Microfone", width=26).pack(side="left")
        self.mic = tk.StringVar(value=ins[0][1] if ins else "Padrão do Windows")
        ttk.Combobox(f1, textvariable=self.mic, values=[n for _,n in ins] or ["Padrão do Windows"], state="readonly").pack(side="left", fill="x", expand=True)

        f2 = ttk.Frame(p); f2.pack(fill="x", padx=18, pady=8)
        ttk.Label(f2, text="Saída de áudio", width=26).pack(side="left")
        self.spk = tk.StringVar(value=outs[0][1] if outs else "Padrão do Windows")
        ttk.Combobox(f2, textvariable=self.spk, values=[n for _,n in outs] or ["Padrão do Windows"], state="readonly").pack(side="left", fill="x", expand=True)

        ttk.Button(p, text="TESTAR MICROFONE", command=self.test_mic).pack(pady=14)
        self.audio_status = ttk.Label(p, text="Dispositivos detectados automaticamente.")
        self.audio_status.pack()

    def _integrations(self):
        p = self.pages["Integrações"]
        ttk.Label(p, text="Integrações opcionais", font=("Segoe UI", 15, "bold")).pack(anchor="w", padx=18, pady=(18,4))

        self.location = tk.BooleanVar(value=self.user_cfg.get("location_enabled", False))
        self.smart = tk.BooleanVar(value=self.user_cfg.get("smart_home_enabled", False))

        ttk.Checkbutton(p, text="Usar localização para clima e contexto local", variable=self.location).pack(anchor="w", padx=18, pady=(12,4))
        ttk.Checkbutton(p, text="Ativar Casa Inteligente", variable=self.smart).pack(anchor="w", padx=18, pady=4)

        ttk.Button(p, text="CONFIGURAR CASA INTELIGENTE", command=self.open_smart_home).pack(anchor="w", padx=18, pady=(18,8))
        ttk.Label(p, text="Você pode pular estas integrações e configurar depois.").pack(anchor="w", padx=18)

    def _finish(self):
        p = self.pages["Finalizar"]
        ttk.Label(p, text="Tudo quase pronto", font=("Segoe UI", 15, "bold")).pack(anchor="w", padx=18, pady=(18,4))
        ttk.Label(p, text="O instalador salva suas preferências e prepara o JARVIS para uso diário.").pack(anchor="w", padx=18)
        ttk.Button(p, text="SALVAR E FINALIZAR CONFIGURAÇÃO", command=self.finish).pack(pady=30)
        self.finish_status = ttk.Label(p, text="")
        self.finish_status.pack()

    def test_groq(self):
        key = self.groq_key.get().strip()
        if not key:
            messagebox.showwarning("Groq", "Informe a chave do Groq.")
            return
        try:
            r = requests.get("https://api.groq.com/openai/v1/models",
                             headers={"Authorization":f"Bearer {key}"}, timeout=8)
            r.raise_for_status()
            count = len(r.json().get("data",[]))
            self.ai_status.config(text=f"Groq conectado. {count} modelo(s) disponível(is).")
        except Exception as e:
            messagebox.showerror("Groq", str(e))

    def test_gemini(self):
        key = self.gemini_key.get().strip()
        if not key:
            messagebox.showwarning("Gemini", "Informe a chave do Gemini.")
            return
        try:
            r = requests.get(
                f"https://generativelanguage.googleapis.com/v1beta/models?key={key}",
                timeout=8
            )
            r.raise_for_status()
            count = len(r.json().get("models",[]))
            self.ai_status.config(text=f"Gemini conectado. {count} modelo(s) disponível(is).")
        except Exception as e:
            messagebox.showerror("Gemini", str(e))

    def test_mic(self):
        try:
            import sounddevice as sd
            import numpy as np
            dur = 1.0
            rec = sd.rec(int(16000*dur), samplerate=16000, channels=1, dtype="float32")
            sd.wait()
            level = float(np.abs(rec).mean())
            self.audio_status.config(text=f"Microfone OK. Nível detectado: {level:.4f}")
        except Exception as e:
            messagebox.showerror("Microfone", str(e))

    def open_smart_home(self):
        script = ROOT / "configurar_casa_inteligente.py"
        if script.exists():
            subprocess.Popen([sys.executable, str(script)], cwd=str(ROOT))
        else:
            messagebox.showinfo("Casa Inteligente", "Módulo não encontrado nesta instalação.")

    def finish(self):
        name = self.user_name.get().strip()
        if not name:
            messagebox.showwarning("Perfil", "Informe seu nome.")
            return

        provider = self.provider.get().strip()
        if provider == "groq" and not self.groq_key.get().strip():
            messagebox.showwarning("IA", "Para usar Groq, informe a chave do Groq.")
            return
        if provider == "gemini" and not self.gemini_key.get().strip():
            messagebox.showwarning("IA", "Para usar Gemini, informe a chave do Gemini.")
            return

        user = {
            "completed": True,
            "user_name": name,
            "assistant_name": self.assistant_name.get().strip() or "JARVIS",
            "language": "pt-BR",
            "ai_provider": provider,
            "voice_enabled": self.voice_on.get(),
            "wake_word_enabled": self.wake_on.get(),
            "wake_word": "jarvis",
            "wallpaper_enabled": self.wallpaper.get(),
            "location_enabled": self.location.get(),
            "smart_home_enabled": self.smart.get(),
            "start_with_windows": self.start_win.get(),
        }
        save_json(USER_CFG, user)

        api = self.api_cfg
        api["groq_api_key"] = self.groq_key.get().strip()
        api["gemini_api_key"] = self.gemini_key.get().strip()
        api["fast_brain_provider"] = provider
        save_json(API_CFG, api)

        # Only one autostart mechanism: ui.MainWindow registers HKCU Run at
        # startup, so the wizard must NOT also create a Startup .lnk (otherwise
        # two JARVIS processes launch and grab the microphone simultaneously).
        save_json(ROOT / 'config' / 'startup.json',
                  {'start_with_windows': bool(self.start_win.get())})
        self.finish_status.config(text="Configuração concluída.")
        messagebox.showinfo("JARVIS", "Configuração concluída. O JARVIS está pronto para iniciar.")
        self.destroy()

if __name__ == "__main__":
    Wizard().mainloop()
