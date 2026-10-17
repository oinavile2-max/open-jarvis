from __future__ import annotations
from dataclasses import dataclass, asdict
from enum import Enum
from time import time
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE_FILE = ROOT / "config" / "proactive_call.json"

class Priority(str, Enum):
    LOW = "baixa"
    NORMAL = "normal"
    HIGH = "alta"
    CRITICAL = "crítica"

@dataclass
class ProactiveEvent:
    title: str
    message: str
    priority: Priority = Priority.NORMAL
    category: str = "geral"
    source: str = "jarvis"
    created_at: float = 0.0
    requires_confirmation: bool = False

    def __post_init__(self):
        if not self.created_at:
            self.created_at = time()

def load_settings() -> dict:
    default = {
        "enabled": True,
        "call_style_enabled": True,
        "driving_safe_mode": True,
        "speak_urgent_only_while_driving": True,
        "auto_answer_from_jarvis": True,
        "call_timeout_seconds": 25,
        "allowed_categories": [
            "segurança", "agenda", "trânsito", "casa", "sistema", "emergência"
        ],
    }
    try:
        if STATE_FILE.exists():
            data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                default.update(data)
    except Exception:
        pass
    return default

def save_settings(data: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

def should_interrupt(event: ProactiveEvent, driving: bool = False) -> bool:
    cfg = load_settings()
    if not cfg.get("enabled", True):
        return False

    allowed = set(cfg.get("allowed_categories") or [])
    if allowed and event.category not in allowed:
        return False

    if driving and cfg.get("speak_urgent_only_while_driving", True):
        return event.priority in {Priority.HIGH, Priority.CRITICAL}

    return event.priority in {Priority.NORMAL, Priority.HIGH, Priority.CRITICAL}
