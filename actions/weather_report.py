import webbrowser
from urllib.parse import quote_plus

def weather_action(parameters: dict, player=None, session_memory=None) -> str:
    city=(parameters.get("city") or "").strip() if isinstance(parameters.get("city"),str) else ""
    when=(parameters.get("time") or "hoje").strip()
    if not city:
        try:
            from core.location_context import get_location, refresh_location
            loc=get_location() or refresh_location()
            if loc:
                city=f"{loc['lat']:.4f},{loc['lon']:.4f}"
        except Exception:
            city=""
    if not city:
        msg="Não consegui obter sua localização. Ative a Localização do Windows ou diga a cidade."
        _log(msg,player); return msg
    q=f"clima {city} {when}"
    url=f"https://www.google.com/search?q={quote_plus(q)}"
    try:
        if not webbrowser.open(url): raise RuntimeError("o navegador não respondeu")
    except Exception as e:
        msg=f"Não consegui abrir a previsão do tempo: {e}"; _log(msg,player); return msg
    msg=f"Abri a previsão do tempo para {when}."
    _log(msg,player)
    if session_memory:
        try: session_memory.set_last_search(query=q,response=msg)
        except Exception: pass
    return msg

def _log(message: str, player=None) -> None:
    print(f"[Clima] {message}")
    if player:
        try: player.write_log(f"JARVIS: {message}")
        except Exception: pass

TOOL={
    "name":"weather_report",
    "description":"Mostra a previsão do tempo. Se a cidade não for informada, usa a localização do Windows quando disponível.",
    "parameters":{"type":"OBJECT","properties":{"city":{"type":"STRING","description":"Cidade opcional"},"time":{"type":"STRING","description":"Período, por exemplo hoje ou amanhã"}}},
    "handler":weather_action,
}
