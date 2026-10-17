"""
Automação residencial do JARVIS BR.

Provedores:
- Home Assistant: API REST oficial.
- eWeLink CUBE / iHost: Open API V2 local.
- Smart Life / Tuya: controle local via tinytuya.

O JARVIS nunca desbloqueia fechaduras, abre portões/garagens ou desarma
sistemas de segurança por este módulo. Ações desse tipo ficam bloqueadas
deliberadamente.
"""
from __future__ import annotations

import json
import difflib
from pathlib import Path
from typing import Any

import requests

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config" / "smart_home.json"

SAFE_DOMAINS = {
    "light", "switch", "fan", "climate", "scene",
    "media_player", "cover", "input_boolean", "script"
}
BLOCKED_DOMAINS = {"lock", "alarm_control_panel"}
BLOCKED_WORDS = {
    "destrancar", "desbloquear", "abrir portao", "abrir portão",
    "abrir garagem", "desarmar alarme", "desativar alarme"
}


def _load_config() -> dict:
    if not CONFIG_PATH.exists():
        return {"home_assistant": {}, "ewelink": {}, "tuya": {"devices": []}}
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"home_assistant": {}, "ewelink": {}, "tuya": {"devices": []}}


def _norm(s: Any) -> str:
    return str(s or "").strip().lower()


def _blocked(action: str, device: str) -> bool:
    s = f"{action} {device}".lower()
    return any(w in s for w in BLOCKED_WORDS)


# ----------------------------- Home Assistant -----------------------------

def _ha_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def _ha_base(cfg: dict) -> str:
    return str(cfg.get("url") or "").strip().rstrip("/")


def _ha_states(cfg: dict) -> list[dict]:
    base = _ha_base(cfg)
    token = str(cfg.get("token") or "").strip()
    if not base or not token:
        raise RuntimeError("Home Assistant não configurado.")
    r = requests.get(
        f"{base}/api/states",
        headers=_ha_headers(token),
        timeout=4,
        verify=bool(cfg.get("verify_ssl", True)),
    )
    r.raise_for_status()
    return r.json()


def _ha_find_entity(cfg: dict, wanted: str, domain_hint: str = "") -> dict:
    states = _ha_states(cfg)
    wanted_n = _norm(wanted)

    candidates = []
    for st in states:
        entity_id = str(st.get("entity_id") or "")
        domain = entity_id.split(".", 1)[0] if "." in entity_id else ""
        if domain not in SAFE_DOMAINS:
            continue
        if domain_hint and domain != domain_hint:
            continue
        friendly = str((st.get("attributes") or {}).get("friendly_name") or "")
        score = 0.0
        if wanted_n == _norm(entity_id):
            score = 1.0
        elif wanted_n == _norm(friendly):
            score = 0.99
        else:
            score = max(
                difflib.SequenceMatcher(None, wanted_n, _norm(friendly)).ratio(),
                difflib.SequenceMatcher(None, wanted_n, _norm(entity_id)).ratio(),
            )
        candidates.append((score, st))

    if not candidates:
        raise RuntimeError("Nenhum dispositivo compatível encontrado no Home Assistant.")
    candidates.sort(key=lambda x: x[0], reverse=True)
    if candidates[0][0] < 0.45:
        raise RuntimeError(f"Não encontrei um dispositivo parecido com '{wanted}'.")
    return candidates[0][1]


def _ha_service(cfg: dict, domain: str, service: str, data: dict) -> None:
    if domain in BLOCKED_DOMAINS:
        raise RuntimeError("Ação bloqueada por segurança.")
    base = _ha_base(cfg)
    token = str(cfg.get("token") or "").strip()
    r = requests.post(
        f"{base}/api/services/{domain}/{service}",
        headers=_ha_headers(token),
        json=data,
        timeout=5,
        verify=bool(cfg.get("verify_ssl", True)),
    )
    r.raise_for_status()


def _ha_control(cfg: dict, action: str, device: str, value: Any = None) -> str:
    if action == "listar":
        states = _ha_states(cfg)
        items = []
        for st in states:
            entity_id = str(st.get("entity_id") or "")
            domain = entity_id.split(".", 1)[0] if "." in entity_id else ""
            if domain in SAFE_DOMAINS:
                name = (st.get("attributes") or {}).get("friendly_name") or entity_id
                items.append(f"{name}: {st.get('state')}")
        return "Home Assistant: " + ("; ".join(items[:30]) if items else "nenhum dispositivo compatível.")

    ent = _ha_find_entity(cfg, device)
    entity_id = ent["entity_id"]
    domain = entity_id.split(".", 1)[0]

    if domain in BLOCKED_DOMAINS:
        raise RuntimeError("Esse tipo de dispositivo é bloqueado por segurança.")

    if action in {"ligar", "desligar", "alternar"}:
        service = {"ligar": "turn_on", "desligar": "turn_off", "alternar": "toggle"}[action]
        _ha_service(cfg, domain, service, {"entity_id": entity_id})
        return f"{device}: comando {action} enviado."

    if action == "brilho":
        if domain != "light":
            raise RuntimeError("Brilho só pode ser ajustado em luzes.")
        pct = max(0, min(100, int(float(value))))
        _ha_service(cfg, "light", "turn_on", {"entity_id": entity_id, "brightness_pct": pct})
        return f"Brilho de {device} ajustado para {pct}%."

    if action == "temperatura":
        if domain != "climate":
            raise RuntimeError("Temperatura só pode ser ajustada em dispositivos de climatização.")
        temp = float(value)
        _ha_service(cfg, "climate", "set_temperature", {"entity_id": entity_id, "temperature": temp})
        return f"Temperatura de {device} ajustada para {temp:g} °C."

    if action == "cena":
        # For scenes, device can be friendly name or entity id.
        scene = _ha_find_entity(cfg, device, domain_hint="scene")
        _ha_service(cfg, "scene", "turn_on", {"entity_id": scene["entity_id"]})
        return f"Cena {device} ativada."

    if action == "status":
        name = (ent.get("attributes") or {}).get("friendly_name") or entity_id
        return f"{name}: {ent.get('state')}."

    raise RuntimeError(f"Ação '{action}' não suportada pelo Home Assistant.")


# ----------------------------- eWeLink CUBE / iHost -----------------------------

def _ewelink_headers(cfg: dict) -> dict:
    token = str(cfg.get("token") or "").strip()
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def _ewelink_base(cfg: dict) -> str:
    return str(cfg.get("url") or "").strip().rstrip("/")


def _ewelink_devices(cfg: dict) -> list[dict]:
    base = _ewelink_base(cfg)
    token = str(cfg.get("token") or "").strip()
    if not base or not token:
        raise RuntimeError("eWeLink CUBE/iHost não configurado.")
    r = requests.get(
        f"{base}/open-api/v2/rest/devices",
        headers=_ewelink_headers(cfg),
        timeout=4,
        verify=bool(cfg.get("verify_ssl", True)),
    )
    r.raise_for_status()
    payload = r.json()
    if payload.get("error") not in (0, None):
        raise RuntimeError(payload.get("message") or "Erro no eWeLink.")
    return ((payload.get("data") or {}).get("device_list") or [])


def _ewelink_find(cfg: dict, wanted: str) -> dict:
    devices = _ewelink_devices(cfg)
    wanted_n = _norm(wanted)
    scored = []
    for d in devices:
        name = str(d.get("name") or "")
        serial = str(d.get("serial_number") or "")
        score = 1.0 if wanted_n in {_norm(name), _norm(serial)} else max(
            difflib.SequenceMatcher(None, wanted_n, _norm(name)).ratio(),
            difflib.SequenceMatcher(None, wanted_n, _norm(serial)).ratio(),
        )
        scored.append((score, d))
    if not scored:
        raise RuntimeError("Nenhum dispositivo eWeLink encontrado.")
    scored.sort(key=lambda x: x[0], reverse=True)
    if scored[0][0] < 0.45:
        raise RuntimeError(f"Não encontrei '{wanted}' no eWeLink.")
    return scored[0][1]


def _ewelink_put_state(cfg: dict, serial: str, state: dict) -> None:
    base = _ewelink_base(cfg)
    r = requests.put(
        f"{base}/open-api/v2/rest/devices/{serial}",
        headers=_ewelink_headers(cfg),
        json={"state": state},
        timeout=5,
        verify=bool(cfg.get("verify_ssl", True)),
    )
    r.raise_for_status()
    payload = r.json()
    if payload.get("error") not in (0, None):
        raise RuntimeError(payload.get("message") or "O eWeLink recusou o comando.")


def _ewelink_control(cfg: dict, action: str, device: str, value: Any = None) -> str:
    if action == "listar":
        devs = _ewelink_devices(cfg)
        parts = []
        for d in devs[:30]:
            name = d.get("name") or d.get("serial_number")
            state = d.get("state") or {}
            p = ((state.get("power") or {}).get("powerState"))
            parts.append(f"{name}: {p or ('online' if d.get('online') else 'offline')}")
        return "eWeLink: " + ("; ".join(parts) if parts else "nenhum dispositivo.")

    d = _ewelink_find(cfg, device)
    serial = str(d.get("serial_number"))

    if action in {"ligar", "desligar"}:
        _ewelink_put_state(cfg, serial, {"power": {"powerState": "on" if action == "ligar" else "off"}})
        return f"{device}: {action}."

    if action == "brilho":
        pct = max(1, min(100, int(float(value))))
        _ewelink_put_state(cfg, serial, {"brightness": {"brightness": pct}})
        return f"Brilho de {device} ajustado para {pct}%."

    if action == "status":
        return f"{device}: {json.dumps(d.get('state') or {}, ensure_ascii=False)}"

    raise RuntimeError(f"Ação '{action}' ainda não é suportada diretamente no eWeLink CUBE/iHost.")


# ----------------------------- Smart Life / Tuya local -----------------------------

def _tuya_device(cfg: dict, wanted: str) -> dict:
    devices = list(cfg.get("devices") or [])
    if not devices:
        raise RuntimeError("Nenhum dispositivo Smart Life/Tuya foi configurado.")
    wanted_n = _norm(wanted)
    scored = []
    for d in devices:
        name = str(d.get("name") or "")
        did = str(d.get("id") or "")
        score = 1.0 if wanted_n in {_norm(name), _norm(did)} else max(
            difflib.SequenceMatcher(None, wanted_n, _norm(name)).ratio(),
            difflib.SequenceMatcher(None, wanted_n, _norm(did)).ratio(),
        )
        scored.append((score, d))
    scored.sort(key=lambda x: x[0], reverse=True)
    if scored[0][0] < 0.45:
        raise RuntimeError(f"Não encontrei '{wanted}' no Smart Life/Tuya.")
    return scored[0][1]


def _tuya_client(d: dict):
    try:
        import tinytuya
    except Exception as exc:
        raise RuntimeError("tinytuya não está instalado. Rode INSTALAR.bat.") from exc

    kind = _norm(d.get("type") or "switch")
    cls = tinytuya.BulbDevice if kind in {"light", "bulb", "luz", "lampada", "lâmpada"} else tinytuya.OutletDevice
    dev = cls(str(d["id"]), str(d["ip"]), str(d["local_key"]))
    dev.set_version(float(d.get("version", 3.3)))
    return dev


def _tuya_control(cfg: dict, action: str, device: str, value: Any = None) -> str:
    if action == "listar":
        ds = cfg.get("devices") or []
        return "Smart Life/Tuya: " + ("; ".join(str(d.get("name") or d.get("id")) for d in ds) if ds else "nenhum dispositivo.")

    d = _tuya_device(cfg, device)
    dev = _tuya_client(d)

    if action == "ligar":
        dev.turn_on()
        return f"{device}: ligado."
    if action == "desligar":
        dev.turn_off()
        return f"{device}: desligado."
    if action == "status":
        return f"{device}: {json.dumps(dev.status(), ensure_ascii=False)}"
    if action == "brilho":
        if not hasattr(dev, "set_brightness_percentage"):
            raise RuntimeError("Esse dispositivo Tuya não expõe controle de brilho.")
        pct = max(1, min(100, int(float(value))))
        dev.set_brightness_percentage(pct)
        return f"Brilho de {device} ajustado para {pct}%."

    raise RuntimeError(f"Ação '{action}' não suportada nesse dispositivo Smart Life/Tuya.")


# ----------------------------- Unified tool -----------------------------

def smart_home_control(parameters: dict, player=None, **kwargs) -> str:
    action = _norm(parameters.get("action") or "status")
    device = str(parameters.get("device") or "").strip()
    provider = _norm(parameters.get("provider") or "auto")
    value = parameters.get("value")

    if _blocked(action, device):
        return "Por segurança, não desbloqueio fechaduras, não abro portões/garagens e não desarmo alarmes automaticamente."

    cfg = _load_config()

    providers = []
    if provider in {"home_assistant", "home assistant", "ha"}:
        providers = [("Home Assistant", _ha_control, cfg.get("home_assistant") or {})]
    elif provider in {"ewelink", "ewe", "ihost", "cube"}:
        providers = [("eWeLink", _ewelink_control, cfg.get("ewelink") or {})]
    elif provider in {"tuya", "smart life", "smart_home", "smart home"}:
        providers = [("Smart Life/Tuya", _tuya_control, cfg.get("tuya") or {})]
    else:
        # Auto mode: prefer local/universal HA, then eWeLink local, then Tuya local.
        providers = [
            ("Home Assistant", _ha_control, cfg.get("home_assistant") or {}),
            ("eWeLink", _ewelink_control, cfg.get("ewelink") or {}),
            ("Smart Life/Tuya", _tuya_control, cfg.get("tuya") or {}),
        ]

    errors = []
    if action == "listar" and provider == "auto":
        results = []
        for name, fn, pcfg in providers:
            try:
                if pcfg:
                    results.append(fn(pcfg, action, device, value))
            except Exception as e:
                errors.append(f"{name}: {e}")
        if results:
            msg = " | ".join(results)
            _log(msg, player)
            return msg

    for name, fn, pcfg in providers:
        if not pcfg:
            continue
        try:
            msg = fn(pcfg, action, device, value)
            _log(msg, player)
            return msg
        except Exception as e:
            errors.append(f"{name}: {e}")

    if errors:
        msg = "Não consegui executar a automação. " + " | ".join(errors)
    else:
        msg = "Casa inteligente ainda não configurada. Abra CONFIGURAR_CASA_INTELIGENTE.bat."
    _log(msg, player)
    return msg


def _log(msg: str, player=None) -> None:
    print(f"[Casa Inteligente] {msg}")
    if player:
        try:
            player.write_log(f"JARVIS: {msg}")
        except Exception:
            pass


TOOL = {
    "name": "smart_home_control",
    "description": (
        "Controla a casa inteligente em português. Use para ligar/desligar luzes, "
        "tomadas e ventiladores; ajustar brilho ou temperatura; ativar cenas; "
        "consultar status; e listar dispositivos. Integra Home Assistant, eWeLink "
        "CUBE/iHost e Smart Life/Tuya. Nunca use para destrancar fechaduras, abrir "
        "portões/garagens ou desarmar alarmes."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "Ação: listar, ligar, desligar, alternar, brilho, temperatura, cena ou status."
            },
            "device": {
                "type": "STRING",
                "description": "Nome amigável do dispositivo ou cena, por exemplo luz da sala."
            },
            "provider": {
                "type": "STRING",
                "description": "Opcional: auto, home_assistant, ewelink ou tuya."
            },
            "value": {
                "type": "NUMBER",
                "description": "Valor opcional para brilho (%) ou temperatura."
            },
        },
        "required": ["action"],
    },
    "handler": smart_home_control,
}
