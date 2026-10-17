from __future__ import annotations
import time
from dataclasses import dataclass

@dataclass
class ClapConfig:
    enabled: bool = True
    min_peak: float = 0.52
    min_rms: float = 0.055
    max_duration_ms: int = 180
    cooldown_s: float = 1.4

class WakeDetector:
    def __init__(self, wake_word="jarvis", clap=None):
        self.wake_word = (wake_word or "jarvis").strip().lower()
        self.clap = clap or ClapConfig()
        self._last_clap = 0.0
        self._burst_started = 0.0
        self._burst_peak = 0.0
        self._burst_rms = 0.0
        self._in_burst = False

    def notify_audio_level(self, peak: float, rms: float) -> bool:
        now = time.monotonic()
        if not self.clap.enabled:
            return False
        hot = peak >= self.clap.min_peak and rms >= self.clap.min_rms
        if hot and not self._in_burst:
            self._in_burst = True
            self._burst_started = now
            self._burst_peak = peak
            self._burst_rms = rms
            return False
        if self._in_burst:
            self._burst_peak = max(self._burst_peak, peak)
            self._burst_rms = max(self._burst_rms, rms)
            if not hot:
                dur_ms = (now - self._burst_started) * 1000.0
                self._in_burst = False
                ok = (
                    dur_ms <= self.clap.max_duration_ms
                    and self._burst_peak >= self.clap.min_peak
                    and self._burst_rms >= self.clap.min_rms
                    and (now - self._last_clap) >= self.clap.cooldown_s
                )
                if ok:
                    self._last_clap = now
                    return True
        return False

    def notify_transcript(self, text: str) -> bool:
        t = " ".join(str(text or "").lower().split())
        return bool(
            t == self.wake_word
            or t.startswith(self.wake_word + " ")
            or f" {self.wake_word} " in f" {t} "
            or t.endswith(" " + self.wake_word)
        )
