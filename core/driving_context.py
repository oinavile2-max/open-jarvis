from __future__ import annotations
from dataclasses import dataclass
import time

@dataclass
class DrivingState:
    active: bool = False
    source: str = "manual"
    last_changed: float = 0.0

class DrivingContext:
    """
    Conservative context helper.
    This module does not try to infer driving from sensitive data silently.
    It supports explicit/manual activation now and is ready for Android Auto /
    phone motion context later.
    """
    def __init__(self):
        self.state = DrivingState(active=False, source="manual", last_changed=time.time())

    def set_active(self, active: bool, source: str = "manual"):
        self.state = DrivingState(
            active=bool(active),
            source=source,
            last_changed=time.time()
        )

    def is_active(self) -> bool:
        return bool(self.state.active)
