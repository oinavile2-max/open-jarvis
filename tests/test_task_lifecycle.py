import asyncio
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from core.task_runs import TaskRuns, run_tracked
from core.speech_controller import SpeechController
from core.audio_output import CallbackAudioOutput


class TestTaskLifecycle(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.store=TaskRuns(Path(self.tmp.name)/'runs.db')
    def tearDown(self): self.tmp.cleanup()

    async def test_success_is_persisted_before_return(self):
        async def operation(): return SimpleNamespace(response={'result':'ok'})
        await run_tracked(self.store,'search',operation)
        self.assertEqual(self.store.recent()[0]['state'],'succeeded')

    async def test_reported_error_is_not_success(self):
        async def operation(): return SimpleNamespace(response={'result':"Tool 'search' failed: unavailable"})
        await run_tracked(self.store,'search',operation)
        self.assertEqual(self.store.recent()[0]['state'],'failed')

    async def test_exception_finishes_task(self):
        async def operation(): raise ValueError('private details')
        with self.assertRaises(ValueError): await run_tracked(self.store,'search',operation)
        row=self.store.recent()[0]
        self.assertEqual(row['state'],'failed')
        self.assertNotIn('private details',row['detail'])

    async def test_timeout_finishes_task(self):
        async def operation(): await asyncio.Event().wait()
        with self.assertRaises(asyncio.TimeoutError): await run_tracked(self.store,'search',operation,timeout=.01)
        self.assertEqual(self.store.recent()[0]['state'],'timed_out')

    async def test_cancel_finishes_task(self):
        started=asyncio.Event()
        async def operation():
            started.set();await asyncio.Event().wait()
        task=asyncio.create_task(run_tracked(self.store,'search',operation))
        await started.wait();task.cancel()
        with self.assertRaises(asyncio.CancelledError): await task
        self.assertEqual(self.store.recent()[0]['state'],'cancelled')

    async def test_crash_recovery_marks_abandoned_running_task(self):
        self.store.start('abandoned')
        TaskRuns(self.store.path)
        self.assertEqual(self.store.recent()[0]['state'],'failed')


class TestSpeechGeneration(unittest.TestCase):
    def test_late_write_after_cancel_is_discarded(self):
        class Native:
            def __init__(self,**kwargs): pass
        sink=CallbackAudioOutput(Native,samplerate=24000)
        controller=SpeechController();controller.bind(sink)
        token=controller.token()
        controller.cancel(None)
        controller.write(b'old answer',token)
        self.assertFalse(sink._pending)
        self.assertNotEqual(controller.token(),token)
