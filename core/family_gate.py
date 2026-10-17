"""Opt-in permission and quiet-hours policy for future family participation.

No mic is opened and no conversations are recorded by this module. An audio
pipeline may call should_comment ONLY when all people consented.  This gate
cannot grant permission to execute any operation on the computer.
"""
from __future__ import annotations
from datetime import datetime
from pathlib import Path
import json
import time

FILE = Path(__file__).resolve().parents[1] / 'config' / 'family_mode.json'


def load_policy() -> dict:
    try:
        return json.loads(FILE.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {'enabled':False, 'all_present_consented':False,
                'quiet_start':22, 'quiet_end':8, 'min_seconds_between_comments':900}


class FamilyGate:
    def __init__(self):
        self._last_comment = 0.0

    def should_comment(self, *, now: datetime | None = None,
                       monotonic: float | None = None,
                       confidential=False, speaking=False,
                       has_useful_context=False) -> bool:
        cfg=load_policy()
        if not (cfg.get('enabled') and cfg.get('all_present_consented')):
            return False
        if confidential or speaking or not has_useful_context:
            return False
        when=now or datetime.now()
        hour=when.hour
        a=int(cfg.get('quiet_start', 22)) % 24
        b=int(cfg.get('quiet_end', 8)) % 24
        if (a <= hour < b if a < b else hour >= a or hour < b):
            return False
        clock=time.monotonic() if monotonic is None else monotonic
        gap=max(300, int(cfg.get('min_seconds_between_comments',900)))
        return (clock-self._last_comment) >= gap

    def mark_commented(self, monotonic: float | None = None):
        self._last_comment = time.monotonic() if monotonic is None else monotonic
