"""Record thread stacks only when the Qt event loop stops responding."""
from __future__ import annotations
import faulthandler
import sys
import threading
import time
from PyQt6.QtCore import QTimer


def watch_gui(app):
    heartbeat = [time.monotonic()]
    stopped = threading.Event()
    timer = QTimer(app)
    timer.setInterval(500)
    timer.timeout.connect(lambda: heartbeat.__setitem__(0,time.monotonic()))
    timer.start()
    app.aboutToQuit.connect(stopped.set)

    def monitor():
        last_dump = 0.
        while not stopped.wait(2.):
            now = time.monotonic()
            if now-heartbeat[0] > 5. and now-last_dump > 15.:
                last_dump = now
                try:
                    print('[DIAGNÓSTICO] Interface sem responder há mais de 5 segundos.', file=sys.stderr, flush=True)
                    faulthandler.dump_traceback(file=sys.stderr,all_threads=True)
                except (OSError,ValueError,AttributeError):
                    pass
    threading.Thread(target=monitor,daemon=True,name='jarvis-gui-watchdog').start()
    return timer
