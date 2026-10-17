from __future__ import annotations
import json
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox
import requests

ROOT = Path(__file__).resolve().parent
CFG = ROOT / "config" / "api_keys.json"
URL = "https://api.groq.com/openai/v1"

def load():
    try:
        return json.loads(CFG.read_text(encoding="utf-8"))
    except Exception:
        return {}

def save(data):
    CFG.parent.mkdir(parents=True, exist_ok=True)
    CFG.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("JARVIS BR — Configurar Groq")
        self.geometry("680x390")
        self.resizable(False, False)
        cfg = load()

        ttk.Label(self, text="GROQ — CÉREBRO RÁPIDO", font=("Segoe UI", 18, "bold")).pack(pady=(20, 4))
        ttk.Label(self, text="A chave fica somente no seu computador. Não envie a chave no chat.").pack()

        box = ttk.Frame(self)
        box.pack(fill="x", padx=24, pady=22)

        ttk.Label(box, text="API Key").grid(row=0, column=0, sticky="w", pady=8)
        self.key = tk.StringVar(value=cfg.get("groq_api_key", ""))
        ent = ttk.Entry(box, textvariable=self.key, show="*", width=62)
        ent.grid(row=0, column=1, sticky="ew", padx=(12,0))

        self.show = tk.BooleanVar(value=False)
        ttk.Checkbutton(box, text="Mostrar chave", variable=self.show,
                        command=lambda: ent.configure(show="" if self.show.get() else "*")).grid(row=1,column=1,sticky="w")

        ttk.Label(box, text="Modelo").grid(row=2, column=0, sticky="w", pady=12)
        self.model = tk.StringVar(value=cfg.get("groq_model", ""))
        self.combo = ttk.Combobox(box, textvariable=self.model, width=59, state="readonly")
        self.combo.grid(row=2, column=1, sticky="ew", padx=(12,0))
        box.columnconfigure(1, weight=1)

        self.status = ttk.Label(self, text="Cole a chave e clique em DETECTAR MODELOS.")
        self.status.pack(pady=8)

        buttons = ttk.Frame(self)
        buttons.pack(pady=10)
        ttk.Button(buttons, text="DETECTAR MODELOS", command=self.detect).pack(side="left", padx=6)
        ttk.Button(buttons, text="SALVAR E TESTAR", command=self.test).pack(side="left", padx=6)

    def detect(self):
        key = self.key.get().strip()
        if not key:
            messagebox.showwarning("Chave", "Cole sua chave Groq.")
            return
        try:
            self.status.configure(text="Consultando modelos disponíveis...")
            self.update_idletasks()
            r = requests.get(f"{URL}/models", headers={"Authorization":f"Bearer {key}"}, timeout=8)
            r.raise_for_status()
            models = sorted(str(x.get("id")) for x in r.json().get("data", []) if x.get("id"))
            text_models = [m for m in models if not any(x in m.lower() for x in ("whisper","guard","tts"))]
            self.combo["values"] = text_models
            preferred = ["llama-3.1-8b-instant","openai/gpt-oss-20b","qwen/qwen3-32b","llama-3.3-70b-versatile"]
            pick = next((m for m in preferred if m in text_models), text_models[0] if text_models else "")
            self.model.set(pick)
            self.status.configure(text=f"{len(text_models)} modelo(s) de texto detectado(s).")
        except Exception as e:
            self.status.configure(text="Falha.")
            messagebox.showerror("Erro", str(e))

    def test(self):
        key = self.key.get().strip()
        model = self.model.get().strip()
        if not key or not model:
            messagebox.showwarning("Configuração", "Detecte os modelos primeiro.")
            return
        try:
            self.status.configure(text="Testando resposta...")
            self.update_idletasks()
            r = requests.post(
                f"{URL}/chat/completions",
                headers={"Authorization":f"Bearer {key}","Content-Type":"application/json"},
                json={"model":model,"messages":[{"role":"user","content":"Responda somente: JARVIS OK"}],"max_tokens":12,"temperature":0},
                timeout=10,
            )
            r.raise_for_status()
            answer = (((r.json().get("choices") or [{}])[0].get("message") or {}).get("content") or "").strip()
            cfg = load()
            cfg["groq_api_key"] = key
            cfg["groq_model"] = model
            cfg["fast_brain_provider"] = "groq"
            save(cfg)
            self.status.configure(text=f"Conectado — {model}")
            messagebox.showinfo("Sucesso", f"Groq configurado.\nModelo: {model}\nResposta: {answer}")
        except Exception as e:
            self.status.configure(text="Falha no teste.")
            messagebox.showerror("Erro", str(e))

if __name__ == "__main__":
    App().mainloop()
