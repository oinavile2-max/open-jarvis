"""Protocol, permissions, streaming and cancellation without cloud credentials."""
import ast
import asyncio
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from core.claude_brain import ClaudeBrain, approved_tools, text_delta, validate_servers
from core.mcp_bridge import MCPBridge, BearerAuth


class ConfigTests(unittest.TestCase):
    def test_explicit_permissions_only(self):
        config = {'mcp_servers': {'docs': {'type': 'http', 'url': 'https://example.com/mcp'}},
                  'mcp_allowed_tools': ['mcp__docs__lookup']}
        self.assertIn('mcp__docs__lookup', approved_tools(config))
        for name in ['Bash', 'mcp__other__lookup', 'mcp__docs__*']:
            with self.assertRaises(ValueError):
                approved_tools({**config, 'mcp_allowed_tools': [name]})

    def test_bad_server_config_rejected(self):
        for value in [[], {'jarvis': {}}, {'bad': {'command': ''}},
                      {'bad': {'type': 'http', 'url': 'file:///tmp/data'}}]:
            with self.assertRaises(ValueError):
                validate_servers(value)

    def test_no_duplicate_full_message_text(self):
        self.assertEqual(text_delta({'type': 'assistant', 'message': {'content': [{'text': 'oi'}]}}), '')
        self.assertEqual(text_delta({'type': 'stream_event', 'event': {'delta': {'type': 'text_delta', 'text': 'oi'}}}), 'oi')

    def test_cli_disables_builtin_tools_and_implicit_mcp(self):
        brain = ClaudeBrain({'claude_command': sys.executable}, '/tmp/mcp.json', '/tmp')
        command = brain.command()
        self.assertEqual(command[command.index('--tools') + 1], '')
        self.assertIn('--strict-mcp-config', command)
        self.assertEqual(command[command.index('--setting-sources') + 1], '')
        self.assertNotIn('--dangerously-skip-permissions', command)
        self.assertNotIn('--bare', command)  # subscription login remains available


class ProtocolTests(unittest.IsolatedAsyncioTestCase):
    async def test_auth_rejects_missing_token(self):
        called, messages = [], []
        async def app(*args): called.append(True)
        async def send(value): messages.append(value)
        await BearerAuth(app, 'secret')({'type': 'http', 'headers': []}, None, send)
        self.assertEqual(messages[0]['status'], 401)
        self.assertEqual(called, [])

    async def test_dispatch_blocks_unlisted_action(self):
        calls = []
        async def execute(name, args): calls.append(name); return {'result': 'ok'}
        bridge = MCPBridge([{'name': 'system_status'}, {'name': 'delete_files'}], execute, {})
        self.assertEqual(await bridge.dispatch('system_status', {}), {'result': 'ok'})
        with self.assertRaises(PermissionError): await bridge.dispatch('delete_files', {})
        self.assertEqual(calls, ['system_status'])

    async def test_persistent_cli_stream_and_cancel_reaps_process(self):
        with tempfile.TemporaryDirectory() as folder:
            script = Path(folder) / 'fake.py'
            script.write_text('''import sys,json,time
for line in sys.stdin:
    data=json.loads(line)
    text=data['message']['content'][0]['text']
    if text=='wait': time.sleep(30)
    print(json.dumps({'type':'stream_event','event':{'delta':{'type':'text_delta','text':text}}}),flush=True)
    print(json.dumps({'type':'result','subtype':'success','result':text,'session_id':'test'}),flush=True)
''')
            brain = ClaudeBrain({}, Path(folder) / 'mcp.json', folder)
            brain.command = lambda: [sys.executable, '-u', str(script)]
            chunks = []
            try:
                self.assertEqual(await brain.ask('Olá', chunks.append), 'Olá')
                process = brain.process
                self.assertEqual(await brain.ask('Tudo bem?', chunks.append), 'Tudo bem?')
                self.assertIs(brain.process, process)
                task = asyncio.create_task(brain.ask('wait', chunks.append))
                await asyncio.sleep(.03)
                task.cancel()
                await asyncio.gather(task, return_exceptions=True)
                self.assertIsNone(brain.process)
                self.assertIsNotNone(process.returncode)
                self.assertEqual(chunks, ['Olá', 'Tudo bem?'])
            finally:
                await brain.close()

    @unittest.skipUnless(importlib.util.find_spec('mcp'), 'MCP SDK not installed')
    async def test_real_mcp_handshake_tool_call_and_auth(self):
        import httpx
        from mcp import ClientSession
        from mcp.client.streamable_http import streamablehttp_client
        async def execute(name, arguments): return {'result': 'online'}
        bridge = MCPBridge([{'name': 'system_status', 'parameters': {'type': 'object'}}], execute, {})
        try:
            path = await bridge.start()
            config = json.loads(path.read_text())['mcpServers']['jarvis']
            async with httpx.AsyncClient(trust_env=False) as client:
                denied = await client.post(config['url'], json={})
                self.assertEqual(denied.status_code, 401)
            def local_client(**kwargs):
                return httpx.AsyncClient(trust_env=False, follow_redirects=True, **kwargs)
            async with streamablehttp_client(config['url'], headers=config['headers'], httpx_client_factory=local_client) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    listing = await session.list_tools()
                    self.assertEqual({t.name for t in listing.tools}, {'jarvis_list_tools', 'jarvis_execute'})
                    result = await session.call_tool('jarvis_execute', {'name': 'system_status', 'arguments': {}})
                    self.assertFalse(result.isError)
                    blocked = await session.call_tool('jarvis_execute', {'name': 'delete_files', 'arguments': {}})
                    self.assertTrue(blocked.isError)
        finally:
            await bridge.close()
        self.assertFalse(path.exists())

    async def test_new_typed_turn_stops_audio_after_claude_already_finished(self):
        source = Path(__file__).resolve().parents[1] / 'main.py'
        tree = ast.parse(source.read_text())
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'JarvisLive')
        method = next(n for n in cls.body if getattr(n, 'name', '') == '_queue_claude')
        module = ast.fix_missing_locations(ast.Module(body=[ast.ClassDef(name='Subject', bases=[], keywords=[], body=[method], decorator_list=[])], type_ignores=[]))
        ns = {'asyncio': asyncio}
        exec(compile(module, str(source), 'exec'), ns)
        subject = ns['Subject']()
        subject._claude = object()
        finished = asyncio.get_running_loop().create_future()
        finished.set_result(None)
        subject._claude_task = finished
        subject._is_speaking = False
        calls = []
        subject.interrupt = lambda: calls.append('stop')
        async def ask(text): calls.append(text)
        subject._ask_claude = ask
        subject._queue_claude('Correção')
        await subject._claude_task
        self.assertEqual(calls, ['stop', 'Correção'])

    async def test_transcriber_cannot_speak_or_call_tools_in_claude_mode(self):
        # Exercise the actual receive method with Gemini audio + a malicious
        # tool call; only input text may reach Claude, exactly once.
        source = Path(__file__).resolve().parents[1] / 'main.py'
        tree = ast.parse(source.read_text())
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'JarvisLive')
        method = next(n for n in cls.body if getattr(n, 'name', '') == '_receive_audio')
        ns = {'asyncio': asyncio, '_clean_transcript': lambda x: x, 'time': __import__('time')}
        module = ast.fix_missing_locations(ast.Module(body=[ast.ClassDef(name='Subject', bases=[], keywords=[], body=[method], decorator_list=[])], type_ignores=[]))
        exec(compile(module, str(source), 'exec'), ns)
        calls = []
        class Session:
            async def receive(self):
                yield SimpleNamespace(session_resumption_update=None, data=b'gemini audio', tool_call=object(),
                    server_content=SimpleNamespace(input_transcription=SimpleNamespace(text='Olá', finished=True),
                                                   turn_complete=True))
                raise asyncio.CancelledError
        subject = ns['Subject']()
        subject.session = Session()
        subject._claude_mode = True
        subject._queue_claude = calls.append
        with self.assertRaises(asyncio.CancelledError): await subject._receive_audio()
        self.assertEqual(calls, ['Olá'])
