"""Bounded evidence buffer; used only during assistant playback."""
from collections import deque


class BargeInBuffer:
    def __init__(self, max_frames=12):
        self.frames = deque(maxlen=max_frames)
        self.pending = False

    def reset(self):
        self.frames.clear()
        self.pending = False

    def feed(self, pcm, is_voice, required):
        if self.pending:
            return None
        if not is_voice:
            self.frames.clear()
            return None
        self.frames.append(bytes(pcm))
        if len(self.frames) < required:
            return None
        self.pending = True
        return tuple(self.frames)
