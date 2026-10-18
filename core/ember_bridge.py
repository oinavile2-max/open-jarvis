"""Single-frame mailbox. GPU decoding never queues work on the voice thread."""
from __future__ import annotations
import threading
import time
from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from PyQt6.QtGui import QImage

class LiveEmber(QObject):
    updated=pyqtSignal()
    fault=pyqtSignal(str)
    def __init__(self,parent=None,quality='balanced'):
        super().__init__(parent)
        self.image=None;self.failed=False;self.error=''
        self._state=('IDLE',0.,False);self._active=False
        self._lock=threading.Lock();self._mail=None
        self._stop=threading.Event();self._wake=threading.Event()
        self._thread=None;self.quality=quality
        self.backend='starting'
        self._timer=QTimer(self);self._timer.timeout.connect(self._drain)
        self._timer.start(33)
        self.destroyed.connect(lambda *_: self._stop.set())
    def update_state(self,state,amplitude,muted=False,active=True):
        with self._lock:self._state=(state,amplitude,muted)
        self._active=active
        if active:
            self._wake.set()
            if self._thread is None and not self.failed:
                self._thread=threading.Thread(target=self._run,daemon=True,name='jarvis-ember-gpu')
                self._thread.start()
        else:self._wake.clear()
    def _run(self):
        renderer=None
        try:
            from core.ember_renderer import EmberRenderer
            try:
                renderer=EmberRenderer(self.quality)
                self.backend='gpu'
            except Exception as gpu_error:
                from core.ember_cpu import CPUEmberRenderer
                renderer=CPUEmberRenderer(self.quality)
                self.backend='cpu'
                self.error=str(gpu_error)
                print('[Esfera] Usando volume de fogo/fumaça em CPU:', gpu_error)
            while not self._stop.is_set():
                if not self._wake.wait(.2):continue
                started=time.monotonic()
                with self._lock:state=self._state
                try:
                    pixels=renderer.render(*state)
                except Exception:
                    if self.backend != 'gpu':
                        raise
                    renderer.close()
                    from core.ember_cpu import CPUEmberRenderer
                    renderer=CPUEmberRenderer(self.quality)
                    self.backend='cpu'
                    pixels=renderer.render(*state)
                with self._lock:self._mail=(pixels,renderer.size)
                elapsed=time.monotonic()-started
                # Leave CPU time available to conversation even on a weak PC.
                pause=max(0.,1./renderer.fps-elapsed)
                if self.backend=='cpu': pause=max(pause,elapsed*.5)
                self._stop.wait(pause)
        except Exception as exc:
            self.failed=True;self.error=str(exc)
            if not self._stop.is_set():
                self.fault.emit('Renderização volumétrica indisponível: '+self.error)
        finally:
            if renderer is not None:renderer.close()
    def _drain(self):
        with self._lock:frame=self._mail;self._mail=None
        if frame is not None:
            data,size=frame
            self.image=QImage(data,size,size,size*4,QImage.Format.Format_RGBA8888_Premultiplied).mirrored(False,True).copy()
            self.updated.emit()
    def close(self):
        self._active=False;self._timer.stop();self._stop.set();self._wake.set()
