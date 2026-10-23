"""Durable weekly editorial plans shared by the native HUD and AI tools."""
from __future__ import annotations
from contextlib import contextmanager
from datetime import date, timedelta
import json
from pathlib import Path
import sqlite3
import sys
import time
import uuid

DAYS = ('Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo')
STATUSES = ('ideia', 'roteiro', 'gravado', 'editado', 'agendado', 'publicado')
FIELDS = ('title', 'channel', 'status', 'hook', 'script', 'cta')


def project_root():
    return Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent.parent


def default_planner():
    return ContentPlanner(project_root() / 'config' / 'content_plans.sqlite3')


def text(value, limit, *, required=False):
    if not isinstance(value, str) or len(value) > limit or (required and not value.strip()):
        raise ValueError('Texto inválido ou acima do limite permitido.')
    return value.strip()


def monday(value):
    try:
        day = date.fromisoformat(value)
    except (TypeError, ValueError):
        raise ValueError('Use a data de uma segunda-feira no formato AAAA-MM-DD.') from None
    if day.weekday() != 0:
        raise ValueError('A semana deve começar em uma segunda-feira.')
    return day


class ContentPlanner:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS plans (
                    id TEXT PRIMARY KEY, title TEXT NOT NULL, week_start TEXT NOT NULL,
                    brief TEXT NOT NULL, created_at REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS content_cards (
                    id TEXT PRIMARY KEY, plan_id TEXT NOT NULL REFERENCES plans(id),
                    scheduled_date TEXT NOT NULL, title TEXT NOT NULL, channel TEXT NOT NULL,
                    status TEXT NOT NULL, hook TEXT NOT NULL, script TEXT NOT NULL, cta TEXT NOT NULL,
                    position INTEGER NOT NULL, revision INTEGER NOT NULL DEFAULT 0);
                CREATE TABLE IF NOT EXISTS trello_links (
                    card_id TEXT NOT NULL REFERENCES content_cards(id), board_id TEXT NOT NULL,
                    remote_id TEXT NOT NULL, revision INTEGER NOT NULL, PRIMARY KEY(card_id,board_id));
                CREATE TABLE IF NOT EXISTS plan_boards (
                    plan_id TEXT PRIMARY KEY REFERENCES plans(id), board_id TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS publish_leases (
                    plan_id TEXT PRIMARY KEY REFERENCES plans(id), owner TEXT NOT NULL, expires REAL NOT NULL);
            ''')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=3)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        try:
            with db: yield db
        finally:
            db.close()

    def _card(self, value, start, position):
        if not isinstance(value, dict): raise ValueError('Cartão inválido.')
        day = value.get('day', 0)
        if type(day) is not int or not 0 <= day <= 6: raise ValueError('day deve estar entre 0 e 6.')
        fields = {name: text(value.get(name, ''), 180 if name == 'title' else 24000 if name == 'script' else 1000,
                             required=name == 'title') for name in FIELDS}
        fields['status'] = fields['status'] or 'ideia'
        fields['channel'] = fields['channel'] or 'Instagram'
        if fields['status'] not in STATUSES: raise ValueError('Etapa de produção inválida.')
        return {'id': uuid.uuid4().hex, 'scheduled_date': (start + timedelta(days=day)).isoformat(),
                **fields, 'position': position, 'revision': 0}

    def create_plan(self, title, week_start, brief='', cards=None):
        title, brief = text(title, 180, required=True), text(brief, 8000)
        start = monday(week_start)
        cards = cards if cards is not None else []
        if not isinstance(cards, list) or len(cards) > 70: raise ValueError('Use no máximo 70 cartões por semana.')
        prepared = [self._card(card, start, n) for n, card in enumerate(cards)]
        key = uuid.uuid4().hex
        with self.connect() as db:
            db.execute('INSERT INTO plans VALUES(?,?,?,?,?)', (key, title, start.isoformat(), brief, time.time()))
            for card in prepared: self._insert(db, key, card)
        return key

    def _insert(self, db, plan_id, card):
        names = ['id', 'scheduled_date', *FIELDS, 'position', 'revision']
        db.execute('INSERT INTO content_cards(id,scheduled_date,title,channel,status,hook,script,cta,position,revision,plan_id) VALUES(?,?,?,?,?,?,?,?,?,?,?)',
                   [card[n] for n in names] + [plan_id])

    def list_plans(self):
        with self.connect() as db:
            return [dict(row) for row in db.execute('SELECT p.*,COUNT(c.id) AS total FROM plans p LEFT JOIN content_cards c ON c.plan_id=p.id GROUP BY p.id ORDER BY p.created_at DESC')]

    def get_plan(self, plan_id):
        with self.connect() as db:
            row = db.execute('SELECT * FROM plans WHERE id=?', (plan_id,)).fetchone()
            if row is None: raise ValueError('Plano não encontrado.')
            plan = dict(row)
            remote = db.execute('SELECT board_id FROM plan_boards WHERE plan_id=?',(plan_id,)).fetchone()
            plan['trello_board_id'] = remote['board_id'] if remote else None
            plan['cards'] = [dict(c) for c in db.execute('SELECT * FROM content_cards WHERE plan_id=? ORDER BY scheduled_date,position,id', (plan_id,))]
            return plan

    def add_card(self, plan_id, card):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT week_start FROM plans WHERE id=?', (plan_id,)).fetchone()
            if row is None: raise ValueError('Plano não encontrado.')
            count = db.execute('SELECT COUNT(*) FROM content_cards WHERE plan_id=?', (plan_id,)).fetchone()[0]
            if count >= 70: raise ValueError('Limite de 70 cartões atingido.')
            prepared = self._card(card, monday(row['week_start']), count)
            self._insert(db, plan_id, prepared)
            return prepared['id']

    def update_card(self, card_id, changes, *, expected_revision=None):
        if not isinstance(changes, dict) or not changes or set(changes) - set(FIELDS):
            raise ValueError('Altere apenas título, canal, etapa, gancho, roteiro ou CTA.')
        valid = {k: text(v, 180 if k == 'title' else 24000 if k == 'script' else 1000, required=k == 'title') for k, v in changes.items()}
        if 'status' in valid and valid['status'] not in STATUSES: raise ValueError('Etapa inválida.')
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT revision FROM content_cards WHERE id=?', (card_id,)).fetchone()
            if row is None: raise ValueError('Cartão não encontrado.')
            if expected_revision is not None and expected_revision != row['revision']:
                raise ValueError('Este cartão mudou. Atualize o quadro antes de salvar.')
            fields = ','.join(f'{key}=?' for key in valid)
            db.execute(f'UPDATE content_cards SET {fields},revision=revision+1 WHERE id=?', [*valid.values(), card_id])

    @contextmanager
    def publish_lock(self, plan_id):
        self.get_plan(plan_id)
        owner = uuid.uuid4().hex
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT expires FROM publish_leases WHERE plan_id=?', (plan_id,)).fetchone()
            if row and row['expires'] > time.time(): raise ValueError('Este plano já está sendo enviado. Aguarde.')
            db.execute('INSERT OR REPLACE INTO publish_leases VALUES(?,?,?)', (plan_id, owner, time.time()+120))
        def renew():
            with self.connect() as db:
                changed = db.execute('UPDATE publish_leases SET expires=? WHERE plan_id=? AND owner=?', (time.time()+120, plan_id, owner)).rowcount
                if not changed: raise ValueError('A sessão de envio mudou. Atualize antes de continuar.')
        try: yield renew
        finally:
            with self.connect() as db: db.execute('DELETE FROM publish_leases WHERE plan_id=? AND owner=?', (plan_id, owner))

    def link_board(self, plan_id, board_id):
        with self.connect() as db:
            db.execute('INSERT OR REPLACE INTO plan_boards VALUES(?,?)',(plan_id,board_id))

    def remote_links(self, plan_id, board_id):
        with self.connect() as db:
            return {row['card_id']: row['remote_id'] for row in db.execute(
                'SELECT l.card_id,l.remote_id FROM trello_links l JOIN content_cards c ON c.id=l.card_id WHERE c.plan_id=? AND l.board_id=?',
                (plan_id, board_id))}

    def link_card(self, card_id, board_id, remote_id, revision):
        with self.connect() as db:
            db.execute('INSERT OR REPLACE INTO trello_links VALUES(?,?,?,?)', (card_id, board_id, remote_id, revision))


def card_markdown(card):
    return '\n\n'.join((f"# {card['title']}", f"Data: {card['scheduled_date']}  ·  Canal: {card['channel']}  ·  Etapa: {card['status']}",
                         '## Gancho\n'+card['hook'], '## Roteiro\n'+card['script'], '## Chamada para ação\n'+card['cta']))


def plan_markdown(plan):
    out = [f"# {plan['title']}", f"Semana: {plan['week_start']}", plan['brief']]
    start = monday(plan['week_start'])
    for offset, day in enumerate(DAYS):
        scheduled = (start+timedelta(days=offset)).isoformat()
        out.append(f'## {day} — {scheduled}')
        for card in plan['cards']:
            if card['scheduled_date'] == scheduled:
                out.append(card_markdown(card).replace('# ', '### ', 1))
    return '\n\n'.join(out)+'\n'
