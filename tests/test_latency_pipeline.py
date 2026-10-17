"""Tests for latency-critical event handling without network/audio hardware."""
import ast
import asyncio
from pathlib import Path
import time
import types
import unittest

SRC = Path(__file__).resolve().parents[1] / 'main.py'


def isolate_methods():
    tree = ast.parse(SRC.read_text(encoding='utf-8'))
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'JarvisLive')
    names = {'_enqueue_mic_event', '_send_realtime'}
    selected = [n for n in cls.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name in names]
    new_class = ast.ClassDef(name='IsolatedJarvis', bases=[], keywords=[], body=selected, decorator_list=[])
    mod = ast.fix_missing_locations(ast.Module(body=[new_class], type_ignores=[]))
    ns = {'asyncio': asyncio, 'time': time, 'types': types.SimpleNamespace(Blob=lambda **kwargs: kwargs)}
    exec(compile(mod, str(SRC), 'exec'), ns)
    return ns['IsolatedJarvis']


class FakeLiveSession:
    def __init__(self):
        self.calls = []
    async def send_realtime_input(self, **kwargs):
        self.calls.append(kwargs)


class TestLatencyPipeline(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.model = isolate_methods()()
        self.model.out_queue = asyncio.Queue(maxsize=3)
        self.model.session = FakeLiveSession()
        self.model._speech_end_sent_at = 0
        self.model._first_audio_logged = True
        self.model._dropped_mic_frames = 0

    async def test_audio_before_stream_end(self):
        self.model._enqueue_mic_event({'data': b'A', 'mime_type': 'audio/pcm;rate=16000'})
        self.model._enqueue_mic_event({'data': b'B', 'mime_type': 'audio/pcm;rate=16000'})
        self.model._enqueue_mic_event({'audio_stream_end': True})
        task = asyncio.create_task(self.model._send_realtime())
        try:
            for _ in range(100):
                if len(self.model.session.calls) == 3:
                    break
                await asyncio.sleep(0.001)
            self.assertEqual(len(self.model.session.calls), 3)
            self.assertEqual(self.model.session.calls[0]['audio']['data'], b'A')
            self.assertEqual(self.model.session.calls[1]['audio']['data'], b'B')
            self.assertEqual(self.model.session.calls[2], {'audio_stream_end': True})
            self.assertGreater(self.model._speech_end_sent_at, 0)
            self.assertFalse(self.model._first_audio_logged)
        finally:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)

    async def test_queue_keeps_latest_audio_under_backpressure(self):
        for i in range(5):
            self.model._enqueue_mic_event({'data': bytes([i])})
        self.assertEqual(self.model._dropped_mic_frames, 2)
        self.assertEqual([self.model.out_queue.get_nowait()['data'] for _ in range(3)],
                         [b'\x02', b'\x03', b'\x04'])

    async def test_end_marker_survives_full_queue(self):
        for i in range(3):
            self.model._enqueue_mic_event({'data': bytes([i])})
        self.model._enqueue_mic_event({'audio_stream_end': True})
        self.assertEqual(self.model.out_queue.get_nowait()['data'], b'\x01')
        self.assertEqual(self.model.out_queue.get_nowait()['data'], b'\x02')
        self.assertEqual(self.model.out_queue.get_nowait(), {'audio_stream_end': True})


if __name__ == '__main__':
    unittest.main()
