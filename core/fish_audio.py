"""Fish HTTP PCM streaming into the existing 24 kHz playback queue."""
import asyncio
import concurrent.futures
import re
import threading
import time
from core.voice_settings import DEFAULT_FISH_AUDIO_VOICE_ID


class FishAudioStream:
    def __init__(self, config, audio_queue, turn_done, log, *, transport=None):
        self.key = str(config.get('fish_audio_api_key') or '').strip()
        self.voice = config.get('fish_audio_voice_id') or DEFAULT_FISH_AUDIO_VOICE_ID
        self.model = config.get('fish_audio_model') or 's2.1-pro'
        self.audio_queue, self.turn_done, self.log = audio_queue, turn_done, log
        self.transport = transport
        self.jobs = asyncio.Queue(maxsize=16)
        self.buffer = ''
        self.epoch = 0
        self.stop = threading.Event()
        self.failed = False

    def feed(self, text):
        if self.failed: return
        self.buffer += (' ' if self.buffer else '') + text
        while self.buffer:
            match = re.search(r'[!?](?:\s|$)|(?<!\d)\.(?:\s|$)', self.buffer)
            cut = match.end() if match else None
            if cut is None and len(self.buffer) >= 220:
                cut = self.buffer.rfind(' ', 0, 220)
                if cut <= 0: cut = 220
            if cut is None: break
            phrase, self.buffer = self.buffer[:cut].strip(), self.buffer[cut:].lstrip()
            if phrase: self._queue(phrase)

    def finish(self):
        if self.buffer.strip(): self._queue(self.buffer.strip())
        self.buffer = ''
        self._queue(None)

    def _queue(self, text):
        try: self.jobs.put_nowait((self.epoch, text))
        except asyncio.QueueFull:
            self.cancel()
            self.failed = True
            self.log('FISH AUDIO: fila cheia. Resposta disponível em texto; reconecte para tentar novamente.')
            self.turn_done.set()

    def cancel(self):
        self.stop.set()
        self.stop = threading.Event()
        self.epoch += 1
        self.buffer = ''
        while not self.jobs.empty(): self.jobs.get_nowait()

    async def _emit(self, data, epoch, stop):
        while self.audio_queue.qsize() >= 20:
            if stop.is_set() or epoch != self.epoch: return
            await asyncio.sleep(.005)
        if not stop.is_set() and epoch == self.epoch:
            self.turn_done.clear()
            self.audio_queue.put_nowait(data)

    def _stream(self, text, epoch, stop, loop):
        post = self.transport
        if post is None:
            import requests
            post = requests.post
        payload = dict(text=text, reference_id=self.voice, format='pcm',
                       sample_rate=24000, latency='balanced', chunk_length=100)
        started = time.monotonic()
        with post('https://api.fish.audio/v1/tts',
                  headers={'Authorization': 'Bearer '+self.key, 'Content-Type':'application/json', 'model':self.model},
                  json=payload, stream=True, timeout=(5, 5)) as response:
            if response.status_code != 200:
                raise RuntimeError('HTTP '+str(response.status_code))
            remainder = b''
            for chunk in response.iter_content(chunk_size=2400):
                if stop.is_set() or epoch != self.epoch: return
                if time.monotonic()-started > 45: raise TimeoutError('Synthesis deadline')
                if not chunk: continue
                data = remainder+chunk
                length = len(data)//2*2
                remainder = data[length:]
                if length:
                    future = asyncio.run_coroutine_threadsafe(self._emit(data[:length], epoch, stop), loop)
                    while True:
                        try: future.result(timeout=.1); break
                        except concurrent.futures.TimeoutError:
                            if stop.is_set(): future.cancel(); return
            if remainder: raise RuntimeError('Incomplete PCM sample')

    async def run(self):
        loop = asyncio.get_running_loop()
        try:
            while True:
                epoch, text = await self.jobs.get()
                if epoch != self.epoch: continue
                if text is None:
                    self.turn_done.set()
                    continue
                if self.failed: continue
                try:
                    await asyncio.to_thread(self._stream, text, epoch, self.stop, loop)
                except Exception as exc:
                    if epoch == self.epoch:
                        self.failed = True
                        self.log('FISH AUDIO: síntese indisponível ('+type(exc).__name__+'). Confira chave, acesso à voz e conexão. Resposta disponível em texto.')
                        self.turn_done.set()
        finally:
            self.cancel()
