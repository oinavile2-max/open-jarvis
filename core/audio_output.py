"""Callback-fed speaker output with bounded waits and explicit cancellation."""
from __future__ import annotations
from collections import deque
import threading
import time


class CallbackAudioOutput:
    def __init__(self, stream_factory, *, samplerate, channels=1, timeout=2., **kwargs):
        self._pending = deque()
        self._lock = threading.Lock()
        self._closed = False
        self._timeout = timeout
        self._byte_rate = samplerate * channels * 2
        self._stream = stream_factory(samplerate=samplerate, channels=channels,
                                      callback=self._callback, **kwargs)

    @property
    def latency(self):
        return self._stream.latency

    def start(self):
        self._stream.start()

    def _callback(self, outdata, frames, time_info, status):
        target = memoryview(outdata).cast('B')
        target[:] = bytes(len(target))
        cursor = 0
        with self._lock:
            while self._pending and cursor < len(target) and not self._closed:
                item = self._pending[0]
                data, offset, ready = item
                count = min(len(data)-offset, len(target)-cursor)
                target[cursor:cursor+count] = data[offset:offset+count]
                cursor += count
                item[1] += count
                if item[1] == len(data):
                    self._pending.popleft()
                    ready.set()

    def write(self, data):
        if not data:
            return
        ready = threading.Event()
        item = [bytes(data), 0, ready]
        with self._lock:
            if self._closed:
                raise TimeoutError('Saída de áudio encerrada durante reprodução')
            self._pending.append(item)
        # Waiting on our own event is bounded; it does not enter Pa_WriteStream,
        # which some disconnected Windows drivers leave blocked indefinitely.
        if not ready.wait(self._timeout + len(data)/self._byte_rate):
            with self._lock:
                self._pending = deque(entry for entry in self._pending if entry is not item)
            raise TimeoutError('A saída de som não está consumindo áudio')
        if self._closed:
            raise TimeoutError('Saída de áudio interrompida')

    def stop(self):
        with self._lock:
            self._closed = True
            for item in self._pending:
                item[2].set()
            self._pending.clear()
        self._stream.abort()

    def close(self):
        self._stream.close()
