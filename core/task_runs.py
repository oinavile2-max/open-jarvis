"""Durable tool lifecycle; SQLite is used only at task boundaries."""
import asyncio
import sqlite3
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

TERMINAL = {'succeeded', 'failed', 'timed_out', 'cancelled'}


class TaskRuns:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, name TEXT, state TEXT, started REAL, ended REAL, detail TEXT)')
            db.execute("UPDATE runs SET state='failed', ended=?, detail='Sessão anterior encerrada antes da conclusão' WHERE state='running'", (time.time(),))

    @contextmanager
    def connect(self):
        db = sqlite3.connect(str(self.path), timeout=2)
        try:
            with db:
                yield db
        finally:
            db.close()

    def start(self, name):
        key = uuid.uuid4().hex
        with self.connect() as db:
            db.execute('INSERT INTO runs VALUES (?,?,?,?,?,?)', (key, name, 'running', time.time(), None, ''))
        return key

    def finish(self, key, state, detail=''):
        if state not in TERMINAL:
            raise ValueError(state)
        with self.connect() as db:
            db.execute("UPDATE runs SET state=?, ended=?, detail=? WHERE id=? AND state='running'", (state, time.time(), detail[:400], key))

    def recent(self, limit=40):
        with self.connect() as db:
            db.row_factory = sqlite3.Row
            return [dict(row) for row in db.execute('SELECT * FROM runs ORDER BY started DESC LIMIT ?', (min(100, max(1, limit)),))]


async def run_tracked(store, name, operation, *, timeout=60):
    starting = asyncio.create_task(asyncio.to_thread(store.start, name))
    try:
        key = await asyncio.shield(starting)
    except asyncio.CancelledError:
        key = await starting
        await asyncio.to_thread(store.finish, key, 'cancelled', 'Cancelada antes da execução.')
        raise
    try:
        result = await asyncio.wait_for(operation(), timeout)
        payload = getattr(result, 'response', {}) or {}
        text = str(payload.get('result', ''))
        failed = payload.get('error', False) or text.startswith(('Unknown tool:', 'Search failed', 'Error:', 'Failed:')) or (text.startswith("Tool '") and "failed:" in text)
        await asyncio.to_thread(store.finish, key, 'failed' if failed else 'succeeded', 'Falha informada pela ferramenta' if failed else '')
        return result
    except asyncio.CancelledError:
        await asyncio.to_thread(store.finish, key, 'cancelled', 'Espera cancelada; ações externas já iniciadas podem continuar.')
        raise
    except asyncio.TimeoutError:
        await asyncio.to_thread(store.finish, key, 'timed_out', 'Tempo de espera esgotado; ações externas já iniciadas podem continuar.')
        raise
    except Exception:
        await asyncio.to_thread(store.finish, key, 'failed', 'Erro na execução. Consulte o log local.')
        raise
