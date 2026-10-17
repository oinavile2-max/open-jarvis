"""Spotify on Windows — conservative, permissions-respecting media control.

Playback of a *specific* track needs Spotify-approved API access and an active
Spotify playback session. Without OAuth we support opening the Spotify app,
searching songs there, and sending OS media keys (target is NOT guaranteed).
Never claim a song started just because a protocol URI opened.
"""
from __future__ import annotations

import os
import platform
import shutil
import subprocess
from urllib.parse import quote


def _open_spotify_uri(uri: str) -> bool:
    try:
        if platform.system() == 'Windows':
            os.startfile(uri)  # user-installed registered Spotify app handler
            return True
        if platform.system() == 'Darwin':
            return subprocess.run(['open', uri], check=False, timeout=7).returncode == 0
        return subprocess.run(['xdg-open', uri], check=False, timeout=7).returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def spotify_control(parameters=None, **_kwargs):
    opts = parameters or {}
    action = str(opts.get('action', 'open')).lower().strip()
    query = str(opts.get('query') or '').strip()[:220]
    if action == 'open':
        return ('Abri o Spotify.' if _open_spotify_uri('spotify:') else
                'Não encontrei um Spotify instalado com abertura por link.')
    if action == 'search':
        if not query:
            return 'Qual música, artista ou álbum devo procurar?'
        if _open_spotify_uri('spotify:search:' + quote(query, safe='')):
            return f'Abri a pesquisa por {query} no Spotify. Selecione uma faixa para reproduzir.'
        return 'Não consegui abrir a pesquisa no aplicativo Spotify.'
    if action in ('play_pause', 'next', 'previous'):
        try:
            import pyautogui
            mapping = {'play_pause':'playpause', 'next':'nexttrack', 'previous':'prevtrack'}
            pyautogui.press(mapping[action])
            return ('Enviei o comando de mídia ao Windows. Ele pode controlar outro '
                    'aplicativo se o Spotify não for o player ativo.')
        except Exception as exc:
            return f'Não consegui enviar o comando de mídia: {exc}'
    return 'Comando do Spotify desconhecido.'


TOOL = {
    'name':'spotify_control',
    'description': ('Controla o Spotify: abrir app, buscar música dentro do Spotify '
        'ou enviar teclas de mídia ao Windows. Sem conta/API OAuth não garante '
        'reprodução automática de faixa específica. Nunca afirmar que reproduziu '
        'uma faixa específica se só abriu a pesquisa.'),
    'parameters': {'type':'OBJECT', 'properties': {
        'action': {'type':'STRING','enum':['open','search','play_pause','next','previous']},
        'query': {'type':'STRING', 'description':'Música ou artista, apenas para search'}
    }, 'required':['action']},
    'handler':spotify_control,
}
