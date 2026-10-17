"""Independent JARVIS voice volume (0..200%), not system volume.

Raw Gemini PCM is processed BEFORE being sent to Windows WASAPI via
sounddevice and BEFORE echo cancellation receives the outgoing reference.
A soft knee limits peaks to avoid digital clipping when amplified.
"""
from __future__ import annotations

import json
from pathlib import Path
import numpy as np

_FILE = Path(__file__).resolve().parents[1] / 'config' / 'voice_output.json'
try:
    _volume = max(0, min(200, int(json.loads(_FILE.read_text(encoding='utf-8')).get('volume_percent', 100))))
except (ValueError, OSError, TypeError, AttributeError):
    _volume = 100


def get_volume() -> int:
    return _volume


def set_volume(percent: int, *, persist: bool = True) -> int:
    global _volume
    _volume = max(0, min(200, int(percent)))
    if persist:
        _FILE.parent.mkdir(parents=True, exist_ok=True)
        temp = _FILE.with_suffix('.tmp')
        temp.write_text(json.dumps({'volume_percent': _volume}, indent=2), encoding='utf-8')
        temp.replace(_FILE)
    return _volume


def amplify_pcm16(data: bytes, percent: int | None = None) -> bytes:
    """Return mono or interleaved stereo signed PCM16, without hard clipping.

    Peak shaping begins only above 0.85: most voice samples are amplified
    linearly, loud peaks compress smoothly toward the physical ±1.0 limit.
    """
    level = get_volume() if percent is None else max(0, min(200, int(percent)))
    if level == 100:
        return data
    if level == 0:
        return bytes(len(data))
    x = np.frombuffer(data, dtype='<i2').astype(np.float32) / 32768.0
    x *= level / 100.0
    peak = np.abs(x)
    shaped = np.where(peak <= .85, peak, .85 + .15 * (1. - np.exp(-(peak-.85)/.15)))
    y = np.copysign(shaped, x)
    return np.clip(np.rint(y*32767.0), -32768, 32767).astype('<i2').tobytes()
