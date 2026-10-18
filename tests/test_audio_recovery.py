import threading
import time
import unittest
from unittest.mock import patch
from types import SimpleNamespace
from core.audio_devices import HardwareChangeDetector
from core.audio_output import CallbackAudioOutput


class NativeStream:
    latency = .02
    def __init__(self, **kwargs):
        self.callback = kwargs['callback']
    def start(self): pass
    def abort(self): pass
    def close(self): pass


class TestAudioRecovery(unittest.TestCase):
    def test_changed_hardware_requires_stable_snapshot(self):
        detector = HardwareChangeDetector()
        a=(('Capture','built-in',1),)
        b=(*a,('Capture','usb',1))
        self.assertFalse(detector.changed(a))
        self.assertFalse(detector.changed(b))
        self.assertFalse(detector.changed(None))
        self.assertTrue(detector.changed(b))
        self.assertFalse(detector.changed(b))
        self.assertFalse(detector.changed(a))
        self.assertTrue(detector.changed(a))

    def test_refresh_reinitializes_host_and_invalidates_saved_indices(self):
        from core import audio_devices
        events=[]
        fake=SimpleNamespace(_terminate=lambda:events.append('close'),
                             _initialize=lambda:events.append('open'))
        with patch.dict('sys.modules',sounddevice=fake), patch.object(audio_devices,'list_devices') as listing:
            audio_devices.refresh_host()
            self.assertEqual(events,['close','open'])
            listing.assert_called_once_with('input',refresh=True)

    def test_callback_preserves_pcm_and_fills_rest_with_silence(self):
        sink=CallbackAudioOutput(NativeStream,samplerate=16000,timeout=.2)
        failure=[]
        def writer():
            try: sink.write(b'\x01\x02\x03\x04')
            except Exception as exc: failure.append(exc)
        thread=threading.Thread(target=writer);thread.start()
        deadline=time.monotonic()+.2
        while not sink._pending and time.monotonic()<deadline: time.sleep(.001)
        target=bytearray(8)
        sink._callback(target,4,None,None)
        thread.join(.5)
        self.assertFalse(thread.is_alive())
        self.assertFalse(failure)
        self.assertEqual(target,b'\x01\x02\x03\x04\x00\x00\x00\x00')
        sink.stop();sink.close()

    def test_stalled_device_has_bounded_wait(self):
        sink=CallbackAudioOutput(NativeStream,samplerate=16000,timeout=.025)
        before=time.monotonic()
        with self.assertRaises(TimeoutError): sink.write(b'\x00\x00')
        self.assertLess(time.monotonic()-before,.5)
        self.assertFalse(sink._pending)
        sink.stop();sink.close()

    def test_disconnect_unblocks_writer(self):
        sink=CallbackAudioOutput(NativeStream,samplerate=16000,timeout=1.)
        errors=[]
        def writer():
            try: sink.write(b'\x00\x00')
            except TimeoutError: errors.append('disconnected')
        thread=threading.Thread(target=writer);thread.start()
        deadline=time.monotonic()+.2
        while not sink._pending and time.monotonic()<deadline: time.sleep(.001)
        sink.stop();thread.join(.3)
        self.assertFalse(thread.is_alive())
        self.assertEqual(errors,['disconnected'])
        sink.close()
