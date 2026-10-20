"""Exercise the real microphone callback without hardware or network."""
import ast
import asyncio
from pathlib import Path
from types import SimpleNamespace
import threading
import time
import unittest
import numpy as np


class TestMicrophoneStream(unittest.IsolatedAsyncioTestCase):
    async def capture(self, muted=False, ptt=False):
        source=Path(__file__).resolve().parents[1]/'main.py'
        tree=ast.parse(source.read_text())
        cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='JarvisLive')
        body=[n for n in cls.body if getattr(n,'name','') in {'_listen_audio','_enqueue_mic_event'}]
        captured=[]
        samples=[np.full((320,1),80,dtype=np.int16),np.zeros((320,1),dtype=np.int16),
                 np.full((320,1),1200,dtype=np.int16)]
        class Stream:
            device=0
            active=True
            def __init__(self,**kwargs): self.callback=kwargs['callback']
            def __enter__(self):
                for sample in samples: self.callback(sample,320,None,None)
                return self
            def __exit__(self,*args): pass
        ns=dict(asyncio=asyncio,time=time,np=np,
                sd=SimpleNamespace(InputStream=Stream,query_devices=lambda *args:{'name':'fake'}),
                SEND_SAMPLE_RATE=16000,CHANNELS=1,CHUNK_SIZE=320,
                get_input_device=lambda:'',audio_devices=SimpleNamespace(resolve=lambda *args:None),
                _pcm_level=lambda x:0.01)
        module=ast.fix_missing_locations(ast.Module(body=[ast.ClassDef(name='Subject',bases=[],keywords=[],body=body,decorator_list=[])],type_ignores=[]))
        exec(compile(module,str(source),'exec'),ns)
        subject=ns['Subject']()
        subject._wake_enabled=False
        subject._speaking_lock=threading.Lock()
        subject._is_speaking=False
        subject._tail_active=lambda:False
        subject._echo=SimpleNamespace(_hist=[])
        subject._ptt_enabled=ptt
        subject._ptt_held=False
        subject._phone_active=False
        subject.ui=SimpleNamespace(muted=muted,write_log=lambda msg:None,set_audio_level=lambda x:None)
        subject._enqueue_mic_event=captured.append
        task=asyncio.create_task(subject._listen_audio())
        await asyncio.sleep(.02)
        task.cancel()
        await asyncio.gather(task,return_exceptions=True)
        return captured,samples

    async def test_quiet_speech_and_silence_reach_server_without_local_gate(self):
        events,samples=await self.capture()
        self.assertEqual([e['data'] for e in events],[s.tobytes() for s in samples])
        self.assertTrue(all(e['mime_type']=='audio/pcm;rate=16000' for e in events))
        self.assertFalse(any('audio_stream_end' in e for e in events))

    async def test_mute_still_blocks_transmission(self):
        events,_=await self.capture(muted=True)
        self.assertEqual(events,[])

    async def test_push_to_talk_still_requires_held_key(self):
        events,_=await self.capture(ptt=True)
        self.assertEqual(events,[])
