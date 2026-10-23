"""Authenticated loopback MCP server over the active JARVIS tool dispatcher."""
from __future__ import annotations
import asyncio
import json
import secrets
import socket
import tempfile
from pathlib import Path
from core.claude_brain import validate_servers

DEFAULT_ALLOWED = ('system_status', 'recall_memory', 'web_search', 'content_planner')


class BearerAuth:
    def __init__(self, app, token):
        self.app, self.token = app, token

    async def __call__(self, scope, receive, send):
        if scope['type'] == 'http':
            headers = dict(scope.get('headers', []))
            supplied = headers.get(b'authorization', b'')
            if not secrets.compare_digest(supplied, ('Bearer ' + self.token).encode()):
                await send({'type': 'http.response.start', 'status': 401,
                            'headers': [(b'content-type', b'application/json')]})
                await send({'type': 'http.response.body', 'body': b'{"error":"unauthorized"}'})
                return
        await self.app(scope, receive, send)


class MCPBridge:
    def __init__(self, declarations, execute, config):
        self.execute, self.config = execute, config
        self.allowed = set(config.get('mcp_allowed_actions', DEFAULT_ALLOWED)) - {'claude_reasoning'}
        self.declarations = []
        for decl in declarations:
            if not isinstance(decl, dict):
                decl = decl.model_dump(mode='json', exclude_none=True)
            if decl.get('name') in self.allowed:
                self.declarations.append(decl)
        self.names = {d['name'] for d in self.declarations}
        self.token = secrets.token_urlsafe(32)
        self.server = self.task = self.runtime = self.socket = None

    async def dispatch(self, name, arguments):
        if name not in self.names:
            raise PermissionError('Função não autorizada. Habilite em Ajustes > Claude / MCP.')
        if not isinstance(arguments, dict):
            raise ValueError('arguments deve ser um objeto.')
        return await self.execute(name, arguments)

    async def start(self):
        from mcp.server.fastmcp import FastMCP
        import uvicorn
        servers = validate_servers(self.config.get('mcp_servers', {}))
        # Bind before creating configuration: OS chooses a free loopback port.
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(('127.0.0.1', 0))
        self.socket.listen(128)
        port = self.socket.getsockname()[1]
        mcp = FastMCP('JARVIS', host='127.0.0.1', port=port, stateless_http=True, json_response=True)

        @mcp.tool()
        async def jarvis_list_tools() -> list[dict]:
            """Lista as funções autorizadas do JARVIS e seus parâmetros."""
            return self.declarations

        @mcp.tool()
        async def jarvis_execute(name: str, arguments: dict) -> dict:
            """Executa uma função previamente listada; arguments usa o esquema informado."""
            return await self.dispatch(name, arguments)

        self.runtime = tempfile.TemporaryDirectory(prefix='jarvis-claude-')
        root = Path(self.runtime.name)
        self.path = root / 'mcp.json'
        servers['jarvis'] = {'type': 'http', 'url': f'http://127.0.0.1:{port}/mcp',
                             'headers': {'Authorization': 'Bearer ' + self.token}}
        self.path.write_text(json.dumps({'mcpServers': servers}), encoding='utf-8')
        self.path.chmod(0o600)
        self.workspace = root
        self.server = uvicorn.Server(uvicorn.Config(
            BearerAuth(mcp.streamable_http_app(), self.token), host='127.0.0.1', port=port,
            log_level='error', access_log=False, lifespan='on'))
        self.task = asyncio.create_task(self.server.serve(sockets=[self.socket]))
        try:
            async with asyncio.timeout(5):
                while not self.server.started:
                    if self.task.done():
                        await self.task
                        raise RuntimeError('Servidor MCP encerrou durante a inicialização.')
                    await asyncio.sleep(.01)
        except BaseException:
            await self.close()
            raise
        return self.path

    async def close(self):
        if self.server:
            self.server.should_exit = True
        if self.task:
            try:
                await asyncio.wait_for(self.task, 3)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                self.task.cancel()
                await asyncio.gather(self.task, return_exceptions=True)
        if self.socket:
            self.socket.close()
        if self.runtime:
            self.runtime.cleanup()
