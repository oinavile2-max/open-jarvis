from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CFG = ROOT / "config" / "user_setup.json"

DEFAULT = {
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
}

def load() -> dict:
    data = dict(DEFAULT)
    if CFG.exists():
        try:
            raw = json.loads(CFG.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                data.update(raw)
        except Exception:
            pass
    return data

def save(data: dict) -> None:
    CFG.parent.mkdir(parents=True, exist_ok=True)
    merged = dict(DEFAULT)
    merged.update(data or {})
    CFG.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")

def is_complete() -> bool:
    return bool(load().get("completed"))
