"""Explicit publication of new editorial cards, with timeout reconciliation."""
from datetime import date, timedelta
import json
import re
from urllib.parse import quote
from core.content_planner import DAYS, card_markdown, monday, project_root


class TrelloError(RuntimeError):
    pass


def trello_config():
    try:
        return json.loads((project_root()/'config'/'api_keys.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}


class TrelloClient:
    def __init__(self, config, *, transport=None):
        key = str(config.get('trello_api_key') or '').strip()
        token = str(config.get('trello_token') or '').strip()
        if not key or not token:
            raise TrelloError('Configure chave e token em Ajustes > Conteúdo / Trello.')
        self.auth = f'OAuth oauth_consumer_key="{quote(key, safe="")}", oauth_token="{quote(token, safe="")}"'
        self.board_id = str(config.get('trello_board_id') or '').strip()
        if self.board_id and not re.fullmatch(r'[A-Za-z0-9]{8,32}', self.board_id):
            raise TrelloError('Informe somente o ID ou código do quadro Trello, sem a URL.')
        if transport is None:
            import requests
            transport = requests.Session()
        self.transport = transport

    def request(self, method, path, **params):
        # Credentials stay in the header, never in URLs, logs or tool results.
        try:
            response = self.transport.request(method, 'https://api.trello.com/1'+path,
                headers={'Authorization': self.auth, 'Accept': 'application/json'},
                params=params, timeout=(5,20))
            if response.status_code in (401,403):
                raise TrelloError('Trello recusou o acesso. Confira token, permissões e quadro.')
            if response.status_code == 429:
                raise TrelloError('Trello limitou as requisições. Aguarde antes de tentar novamente.')
            if not 200 <= response.status_code < 300:
                raise TrelloError(f'Trello retornou HTTP {response.status_code}. O envio pode estar parcial; atualize antes de repetir.')
            return response.json()
        except TrelloError:
            raise
        except Exception:
            raise TrelloError('Falha de conexão com Trello. O resultado pode ser parcial; a próxima tentativa verificará os cartões existentes.') from None

    def check_connection(self):
        data = self.request('GET', '/members/me', fields='username')
        return str(data.get('username') or 'Conta conectada')

    def close(self):
        close = getattr(self.transport, 'close', None)
        if close: close()


def publish_plan(planner, plan_id, config, *, confirmed=False, client=None, stop=None):
    if not confirmed:
        raise TrelloError('Confirme o envio ao Trello antes de publicar o plano.')
    plan = planner.get_plan(plan_id)
    if not plan['cards']: raise TrelloError('Adicione conteúdo ao plano antes de enviar.')
    own_client = client is None
    client = client or TrelloClient(config)
    created = skipped = 0
    def request(method, path, **params):
        if stop is not None and stop.is_set():
            raise TrelloError('Envio interrompido. Itens já confirmados foram preservados; confira o quadro antes de continuar.')
        return client.request(method, path, **params)
    try:
        with planner.publish_lock(plan_id) as renew:
            board = client.board_id or plan.get('trello_board_id')
            if not board:
                marker = f'[JARVIS-PLAN:{plan_id}]'
                boards = request('GET', '/members/me/boards', fields='id,desc', filter='open')
                board = next((b['id'] for b in boards if marker in b.get('desc', '')), None)
                if not board:
                    renew()
                    result = request('POST', '/boards', name=plan['title'], desc=marker,
                                            defaultLists='false', prefs_permissionLevel='private')
                    board = result['id']
            if not re.fullmatch(r'[A-Za-z0-9]{8,32}', board): raise TrelloError('Resposta de quadro inválida.')
            planner.link_board(plan_id, board)
            lists = request('GET', f'/boards/{board}/lists', filter='open', fields='id,name')
            remote = request('GET', f'/boards/{board}/cards', filter='all', fields='id,desc')
            start = monday(plan['week_start'])
            columns = {item['name']: item['id'] for item in lists}
            for offset, day in enumerate(DAYS):
                renew()
                label = f"{day} · {(start+timedelta(days=offset)).isoformat()}"
                if label not in columns:
                    columns[label] = request('POST', '/lists', name=label, idBoard=board, pos='bottom')['id']
            links = planner.remote_links(plan_id, board)
            for card in plan['cards']:
                renew()
                marker = f"[JARVIS-CARD:{card['id']}]"
                known_id = links.get(card['id'])
                existing = next((c for c in remote if c.get('id') == known_id or marker in c.get('desc', '')), None)
                if known_id and existing is None:
                    if not re.fullmatch(r'[A-Za-z0-9]{1,64}', known_id):
                        raise TrelloError('Vínculo Trello inválido. Confira o quadro antes de reenviar.')
                    existing = request('GET', f'/cards/{known_id}', fields='id')
                if existing:
                    planner.link_card(card['id'], board, existing['id'], card['revision'])
                    skipped += 1
                    continue
                offset = date.fromisoformat(card['scheduled_date'])-start
                label = f"{DAYS[offset.days]} · {card['scheduled_date']}"
                result = request('POST', '/cards', idList=columns[label], name=card['title'],
                                        desc=card_markdown(card)+'\n\n'+marker, pos='bottom')
                planner.link_card(card['id'], board, result['id'], card['revision'])
                remote.append({'id': result['id'], 'desc': marker})
                created += 1
            return {'created': created, 'existing': skipped, 'board_url': f'https://trello.com/b/{board}',
                    'message': 'Cartões existentes foram preservados; nenhuma postagem em rede social foi realizada.'}
    finally:
        if own_client: client.close()
