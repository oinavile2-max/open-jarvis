from __future__ import annotations

import json
import threading
import webbrowser
from pathlib import Path
import tkinter as tk
from tkinter import messagebox

BASE = Path(__file__).resolve().parent
CFG_DIR = BASE / "config"
CFG_FILE = CFG_DIR / "api_keys.json"
AI_STUDIO = "https://aistudio.google.com/app/apikey"


def load_cfg():
    try:
        return json.loads(CFG_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_cfg(data):
    CFG_DIR.mkdir(parents=True, exist_ok=True)
    CFG_FILE.write_text(json.dumps(data, indent=4, ensure_ascii=False), encoding="utf-8")


def _clean_model_name(name: str) -> str:
    name = (name or "").strip()
    return name[7:] if name.startswith("models/") else name


def _looks_like_text_model(name: str) -> bool:
    n = name.lower()
    if "gemini" not in n:
        return False
    blocked = (
        "live", "audio", "tts", "image", "embedding", "embed", "robotics",
        "transcribe", "vision", "aqa", "learnlm", "veo", "imagen",
    )
    return not any(x in n for x in blocked)


def _score_model(name: str) -> tuple:
    """Prefer cheap/fast text models, but never rely on guessed names."""
    n = name.lower()
    score = 100
    if "flash-lite" in n:
        score -= 50
    elif "flash" in n:
        score -= 40
    if "latest" in n:
        score -= 5
    if "preview" in n or "experimental" in n or "exp" in n:
        score += 20
    if "pro" in n:
        score += 30
    return (score, n)


def discover_models(client) -> list[str]:
    found: list[str] = []
    try:
        models = client.models.list()
        for m in models:
            name = _clean_model_name(str(getattr(m, "name", "") or ""))
            if not name or not _looks_like_text_model(name):
                continue

            # SDK versions expose capabilities under different attribute names.
            # If present, only keep models that can generate content.
            actions = (
                getattr(m, "supported_actions", None)
                or getattr(m, "supported_generation_methods", None)
                or getattr(m, "supported_methods", None)
            )
            if actions:
                normalized = " ".join(str(x).lower() for x in actions)
                if "generate" not in normalized:
                    continue
            found.append(name)
    except Exception:
        pass

    # De-duplicate while preserving discovery, then sort by a conservative
    # preference for Flash/Lite models. These are only fallbacks if listing is
    # unavailable; every candidate is actually tested before being saved.
    fallback = [
        "gemini-flash-lite-latest",
        "gemini-flash-latest",
    ]
    for name in fallback:
        if name not in found:
            found.append(name)

    return sorted(dict.fromkeys(found), key=_score_model)


def test_key(key: str):
    try:
        from google import genai

        client = genai.Client(api_key=key)
        candidates = discover_models(client)
        if not candidates:
            return False, "A chave respondeu, mas nenhum modelo Gemini de texto foi encontrado.", "", []

        errors: list[str] = []
        for model in candidates[:20]:
            try:
                r = client.models.generate_content(
                    model=model,
                    contents="Responda somente: OK",
                )
                txt = (getattr(r, "text", "") or "").strip()
                return True, txt or "Conexão realizada.", model, candidates
            except Exception as e:
                compact = " ".join(str(e).split())
                errors.append(f"{model}: {compact[:220]}")

        detail = "Nenhum dos modelos disponíveis respondeu ao teste.\n\n" + "\n".join(errors[:8])
        return False, detail, "", candidates
    except Exception as e:
        return False, str(e), "", []


class GeminiSetup(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Jarvis — Configurar Gemini (FIX 2)")
        self.geometry("680x430")
        self.resizable(False, False)

        self.columnconfigure(0, weight=1)
        outer = tk.Frame(self, padx=24, pady=22)
        outer.grid(sticky="nsew")
        outer.columnconfigure(0, weight=1)

        tk.Label(outer, text="JARVIS", font=("Segoe UI", 24, "bold")).grid(row=0, column=0, sticky="w")
        tk.Label(
            outer,
            text="Configurar Gemini para teste gratuito — detecção automática de modelo",
            font=("Segoe UI", 11),
        ).grid(row=1, column=0, sticky="w", pady=(0, 18))

        tk.Button(
            outer,
            text="1. Abrir Google AI Studio para criar/copiar a chave",
            command=lambda: webbrowser.open(AI_STUDIO),
            height=2,
        ).grid(row=2, column=0, sticky="ew")

        tk.Label(outer, text="2. Cole sua Gemini API key:", font=("Segoe UI", 10, "bold")).grid(
            row=3, column=0, sticky="w", pady=(18, 6)
        )

        keyrow = tk.Frame(outer)
        keyrow.grid(row=4, column=0, sticky="ew")
        keyrow.columnconfigure(0, weight=1)

        self.key_var = tk.StringVar()
        self.entry = tk.Entry(keyrow, textvariable=self.key_var, show="•", font=("Consolas", 11))
        self.entry.grid(row=0, column=0, sticky="ew")
        self.entry.bind("<Control-v>", self._paste_event)
        self.entry.bind("<Control-V>", self._paste_event)

        tk.Button(keyrow, text="COLAR", width=9, command=self.paste).grid(row=0, column=1, padx=(8, 0))
        self.show_var = tk.BooleanVar(value=False)
        tk.Checkbutton(keyrow, text="Mostrar", variable=self.show_var, command=self.toggle_show).grid(
            row=0, column=2, padx=(8, 0)
        )

        self.status = tk.Label(
            outer,
            text="A chave fica salva somente neste PC. O modelo será detectado automaticamente.",
            anchor="w",
            justify="left",
            wraplength=620,
        )
        self.status.grid(row=5, column=0, sticky="ew", pady=(12, 10))

        self.btn = tk.Button(
            outer,
            text="3. SALVAR, DETECTAR MODELO E TESTAR",
            command=self.save_and_test,
            height=2,
        )
        self.btn.grid(row=6, column=0, sticky="ew")

        self.model_label = tk.Label(
            outer,
            text="Modelo selecionado: ainda não testado",
            anchor="w",
            font=("Segoe UI", 9, "bold"),
        )
        self.model_label.grid(row=7, column=0, sticky="ew", pady=(12, 0))

        tk.Button(outer, text="Fechar", command=self.destroy).grid(row=8, column=0, pady=(18, 0))
        self.entry.focus_set()

        cfg = load_cfg()
        old = cfg.get("gemini_api_key", "")
        if old:
            self.key_var.set(old)
            old_model = cfg.get("gemini_text_model", "")
            if old_model:
                self.model_label.config(text=f"Modelo salvo: {old_model}")
            self.status.config(text="Já existe uma chave salva. Você pode testar novamente sem criar outra.")

    def _paste_event(self, event=None):
        self.paste()
        return "break"

    def paste(self):
        try:
            txt = self.clipboard_get().strip()
            if txt:
                self.key_var.set(txt)
                self.entry.icursor(tk.END)
                self.status.config(text="Chave colada. Agora clique em SALVAR, DETECTAR MODELO E TESTAR.")
        except tk.TclError:
            messagebox.showwarning("Área de transferência", "Não encontrei texto copiado. Copie a chave primeiro.")

    def toggle_show(self):
        self.entry.config(show="" if self.show_var.get() else "•")

    def save_and_test(self):
        key = self.key_var.get().strip()
        if len(key) < 20:
            messagebox.showerror("Chave inválida", "Cole uma Gemini API key válida antes de continuar.")
            return

        cfg = load_cfg()
        cfg["gemini_api_key"] = key
        cfg.setdefault("os_system", "windows")
        cfg["ai_provider"] = "gemini"
        save_cfg(cfg)

        self.btn.config(state=tk.DISABLED)
        self.status.config(text="Consultando os modelos disponíveis para sua própria chave e testando automaticamente...")
        self.model_label.config(text="Modelo selecionado: procurando...")
        threading.Thread(target=self._test_worker, args=(key,), daemon=True).start()

    def _test_worker(self, key):
        ok, msg, model, candidates = test_key(key)
        self.after(0, lambda: self._finish_test(ok, msg, model, candidates))

    def _finish_test(self, ok, msg, model, candidates):
        self.btn.config(state=tk.NORMAL)
        if ok:
            cfg = load_cfg()
            cfg["gemini_text_model"] = model
            cfg["gemini_model"] = model  # compatibility alias for future modules
            save_cfg(cfg)
            self.status.config(text="✓ Chave válida e modelo compatível encontrado automaticamente.")
            self.model_label.config(text=f"Modelo selecionado: {model}")
            messagebox.showinfo(
                "Sucesso",
                f"Gemini conectado com sucesso!\n\nModelo detectado: {model}\n\nAgora abra INICIAR_JARVIS.bat.",
            )
        else:
            self.status.config(text="A chave foi salva, mas nenhum modelo respondeu ao teste.")
            self.model_label.config(text=f"Modelos detectados: {len(candidates)}")
            messagebox.showerror(
                "Falha no teste",
                "A chave foi salva. O configurador consultou os modelos disponíveis em vez de usar um nome fixo.\n\n"
                + msg[:2200],
            )


if __name__ == "__main__":
    GeminiSetup().mainloop()
