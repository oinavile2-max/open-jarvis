from __future__ import annotations
import json
from pathlib import Path
import requests

BASE = Path(__file__).resolve().parent.parent
CFG = BASE / "config" / "api_keys.json"
BASE_URL = "https://api.groq.com/openai/v1"

PREFERRED = [
    "llama-3.1-8b-instant",
    "openai/gpt-oss-20b",
    "qwen/qwen3-32b",
    "llama-3.3-70b-versatile",
]

def _cfg():
    try:
        return json.loads(CFG.read_text(encoding="utf-8"))
    except Exception:
        return {}

def api_key() -> str:
    return str(_cfg().get("groq_api_key") or "").strip()

def configured_model() -> str:
    return str(_cfg().get("groq_model") or "").strip()

def list_models(timeout=8) -> list[str]:
    key = api_key()
    if not key:
        return []
    r = requests.get(
        f"{BASE_URL}/models",
        headers={"Authorization": f"Bearer {key}"},
        timeout=timeout,
    )
    r.raise_for_status()
    return sorted(
        str(x.get("id"))
        for x in (r.json().get("data") or [])
        if x.get("id")
    )

def choose_model() -> str:
    chosen = configured_model()
    if chosen:
        return chosen
    models = list_models()
    for name in PREFERRED:
        if name in models:
            return name
    # Prefer small/instant/flash-like text models when available.
    for token in ("instant", "8b", "20b", "flash"):
        for m in models:
            low = m.lower()
            if token in low and "whisper" not in low and "guard" not in low:
                return m
    for m in models:
        low = m.lower()
        if "whisper" not in low and "guard" not in low and "tts" not in low:
            return m
    return ""

def chat(text: str, system: str = "", max_tokens: int = 220, timeout: int = 10) -> str:
    key = api_key()
    if not key:
        raise RuntimeError("Chave do Groq não configurada.")
    model = choose_model()
    if not model:
        raise RuntimeError("Nenhum modelo Groq compatível encontrado.")
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": text})
    r = requests.post(
        f"{BASE_URL}/chat/completions",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": messages,
            "temperature": 0.25,
            "max_tokens": max_tokens,
            "stream": False,
        },
        timeout=timeout,
    )
    r.raise_for_status()
    data = r.json()
    return ((data.get("choices") or [{}])[0].get("message") or {}).get("content", "").strip()
