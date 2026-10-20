import asyncio
import unittest
from core.fish_audio import FishAudioStream
from core.voice_settings import DEFAULT_FISH_AUDIO_VOICE_ID


class Response:
    status_code=200
    def __enter__(self): return self
    def __exit__(self,*args): pass
    def iter_content(self,**kwargs):
        yield b'\x01'
        yield b'\x02\x03\x04'


class TestFishAudio(unittest.IsolatedAsyncioTestCase):
    async def test_pcm_stream_request_and_turn_completion(self):
        requests=[]
        def post(url,**kwargs):
            requests.append((url,kwargs));return Response()
        q=asyncio.Queue();done=asyncio.Event();logs=[]
        stream=FishAudioStream({'fish_audio_api_key':'test-only'},q,done,logs.append,transport=post)
        task=asyncio.create_task(stream.run())
        try:
            stream.feed('Olá, estou pronto.')
            stream.finish()
            await asyncio.wait_for(done.wait(),1)
            self.assertEqual(q.get_nowait(),b'\x01\x02\x03\x04')
            body=requests[0][1]['json']
            self.assertEqual(body['reference_id'],DEFAULT_FISH_AUDIO_VOICE_ID)
            self.assertEqual(body['format'],'pcm')
            self.assertEqual(body['sample_rate'],24000)
            self.assertEqual(requests[0][1]['headers']['Authorization'],'Bearer test-only')
            self.assertFalse(logs)
        finally:
            task.cancel();await asyncio.gather(task,return_exceptions=True)

    async def test_cancel_rejects_old_audio_and_clears_text(self):
        q=asyncio.Queue();done=asyncio.Event()
        stream=FishAudioStream({},q,done,lambda x:None)
        stream.feed('Primeira resposta.')
        epoch=stream.epoch;stop=stream.stop
        stream.cancel()
        await stream._emit(b'old',epoch,stop)
        self.assertTrue(q.empty())
        self.assertTrue(stream.jobs.empty())
        self.assertEqual(stream.buffer,'')

    async def test_http_failure_is_visible_and_does_not_expose_key(self):
        class Denied(Response): status_code=401
        logs=[];done=asyncio.Event()
        stream=FishAudioStream({'fish_audio_api_key':'secret-test'},asyncio.Queue(),done,logs.append,transport=lambda *a,**k:Denied())
        task=asyncio.create_task(stream.run())
        try:
            stream.feed('Teste.');stream.finish()
            await asyncio.wait_for(done.wait(),1)
            self.assertTrue(stream.failed)
            self.assertTrue(logs)
            self.assertNotIn('secret-test',''.join(logs))
        finally:
            task.cancel();await asyncio.gather(task,return_exceptions=True)
