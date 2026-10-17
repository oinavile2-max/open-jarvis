"""Video-backed animated JARVIS orb.

Uses the *user-provided* clip for visually faithful standby.  The optional
PyQt6 QtMultimedia decoder supplies frames straight to the existing HUD
QPainter; no browser, second microphone, network or blocking OpenCV loop.

Voice dynamics modify the presentation and playback tempo, while the original
procedural LivingOrb remains a resilient fallback if multimedia is missing.
The reference footage must not be sold/re-distributed without usage rights.
"""
from __future__ import annotations

from pathlib import Path
import threading
import time

from PyQt6.QtCore import QObject, QUrl, QTimer, pyqtSignal
from PyQt6.QtGui import QImage
try:
    from PyQt6.QtMultimedia import QMediaPlayer, QVideoSink
except (ImportError, RuntimeError):
    QMediaPlayer = QVideoSink = None


class ReferenceVideoOrb(QObject):
    updated = pyqtSignal()
    fault = pyqtSignal(str)
    _cv_frame = pyqtSignal(object)  # background cv2 thread -> Qt GUI thread

    # Cropping keeps the detailed ash and molten filaments large in the HUD.
    # Coordinates refer to the supplied vertical 720 x 1280 clip.
    CROP_TOP_FRACTION = 0.18
    CROP_HEIGHT_FRACTION = 0.64

    def __init__(self, path: Path, parent=None):
        super().__init__(parent)
        self.path = Path(path)
        self.image: QImage | None = None
        self._failed = False
        self._running = False
        self._active = False
        self._rate = 1.0
        self._cv_mode = QMediaPlayer is None
        self._cv_thread = None
        self._cv_wake = threading.Event()
        self._cv_stop = threading.Event()
        self._cv_frame_pending = False
        self._cv_frame.connect(self._on_cv_frame)
        self.player = None
        self.sink = None
        if not self._cv_mode:
            try:
                self.player = QMediaPlayer(self)
                self.sink = QVideoSink(self)
                self.sink.videoFrameChanged.connect(self._on_frame)
                self.player.setVideoOutput(self.sink)
                # The video audio track is stripped from the bundled asset.
                # No audio output here: the clip cannot talk over the voice.
                self.player.errorOccurred.connect(self._on_error)
                self.player.positionChanged.connect(self._on_position)
                self.player.setLoops(QMediaPlayer.Loops.Infinite)
            except Exception:
                self._cv_mode = True
                self.player = self.sink = None
        self._stall_timer = QTimer(self)
        self._stall_timer.setSingleShot(True)
        self._stall_timer.timeout.connect(self._check_stall)

    @property
    def ready(self) -> bool:
        return self.image is not None and not self.image.isNull()

    @property
    def failed(self) -> bool:
        return self._failed

    def _on_error(self, *_args):
        # The fallback still displays the *same reference frames*. A decoder
        # failure is not permission to silently replace the requested look.
        if not self._cv_mode:
            self.fault.emit('QtMultimedia falhou; iniciando decodificador alternativo')
            self._cv_mode = True
            if self.player:
                self.player.stop()
            if self._active:
                self._start_cv()
        else:
            self._failed = True
            self.fault.emit('Falha também na leitura alternativa do vídeo')

    def _check_stall(self):
        if self._active and not self.ready and not self._cv_mode:
            self._on_error()

    def _start_cv(self):
        self._cv_wake.set()
        if self._cv_thread is None or not self._cv_thread.is_alive():
            self._cv_stop.clear()
            self._cv_thread = threading.Thread(target=self._cv_worker,
                                              name='jarvis-orb-reference', daemon=True)
            self._cv_thread.start()

    def _cv_worker(self):
        # Imported lazily, and decoding runs ONLY in a background worker.
        try:
            import cv2
        except ImportError:
            self._failed = True
            self.fault.emit('OpenCV não instalado; usar animação procedural')
            return
        cap = cv2.VideoCapture(str(self.path))
        if not cap.isOpened():
            self._failed = True
            self.fault.emit('Não foi possível abrir o vídeo da esfera')
            return
        cap.set(cv2.CAP_PROP_POS_MSEC, 1750)
        fps = max(15., min(60., cap.get(cv2.CAP_PROP_FPS) or 30.))
        try:
            while not self._cv_stop.is_set():
                if not self._cv_wake.wait(.2):
                    continue
                started = time.monotonic()
                if cap.get(cv2.CAP_PROP_POS_MSEC) >= 58800:
                    cap.set(cv2.CAP_PROP_POS_MSEC, 1750)
                ok, bgr = cap.read()
                if not ok:
                    cap.set(cv2.CAP_PROP_POS_MSEC, 1750)
                    continue
                # Keep only one image pending; Qt may skip stale animation
                # frames when the computer is busy but never blocks voice.
                if not self._cv_frame_pending:
                    self._cv_frame_pending = True
                    self._cv_frame.emit(bgr)
                delay = 1. / (fps * max(.5, min(1.5, self._rate)))
                self._cv_stop.wait(max(0., delay - (time.monotonic()-started)))
        finally:
            cap.release()

    def _on_cv_frame(self, bgr):
        try:
            h, w = bgr.shape[:2]
            im = QImage(bgr.data, w, h, int(bgr.strides[0]),
                        QImage.Format.Format_BGR888)
            self.image = im.copy()
            self.updated.emit()
        except Exception:
            self._failed = True
        finally:
            self._cv_frame_pending = False

    def _on_position(self, position: int):
        # The first second is a black/unformed transition, not the usual orb.
        # Skip it on each cycle so the object never vanishes at the seam.
        if position >= 58800 and self.player.isSeekable():
            self.player.setPosition(1750)

    def _on_frame(self, frame):
        try:
            if not frame.isValid():
                return
            img = frame.toImage()
            if img.isNull():
                return
            # Copy once: video buffers are recycled after the callback.
            self.image = img.copy()
            self.updated.emit()
        except Exception as exc:
            self._on_error(exc)

    def set_active(self, active: bool):
        if self._failed or not self.path.is_file():
            return
        active = bool(active)
        if active == self._active and (self._running or not active):
            return
        self._active = active
        if self._cv_mode:
            if active:
                self._running = True
                self._start_cv()
            else:
                self._cv_wake.clear()
        elif active:
            if not self._running:
                self.player.setSource(QUrl.fromLocalFile(str(self.path.resolve())))
                self._running = True
                self.player.play()
                self.player.setPosition(1750)
                self._stall_timer.start(4200)
            else:
                self.player.play()
        elif self._running:
            self.player.pause()

    def adjust_motion(self, state: str, level: float):
        if not self._running or self._failed:
            return
        level = max(0., min(1., float(level)))
        target = {'LISTENING': 1.08, 'THINKING': 1.14,
                  'PROCESSING': 1.14, 'ERROR': .87}.get(state.upper(), 1.0)
        if state.upper() == 'SPEAKING':
            target = 1.02 + .16 * level
        if abs(target - self._rate) >= .045:
            self._rate = target
            if self.player is not None and not self._cv_mode:
                self.player.setPlaybackRate(target)

    def close(self):
        self._cv_stop.set()
        self._cv_wake.set()
        if self.player is not None:
            self.player.stop()
        self.image = None
