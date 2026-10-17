from __future__ import annotations

import json
import secrets
import socket
import threading
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Callable, Optional

ROOT = Path(__file__).resolve().parent.parent
CFG = ROOT / "config" / "device_link.json"

DEFAULT = {
    "enabled": True,
    "port": 8767,
    "pairing_code_ttl_s": 180,
    "paired_devices": [],
    "allow_call_handoff": True,
    "allow_state_sync": True,
    "allow_remote_wake": True,
}

def load():
    data = dict(DEFAULT)
    try:
        if CFG.exists():
            raw = json.loads(CFG.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                data.update(raw)
    except Exception:
        pass
    return data

def save(data):
    CFG.parent.mkdir(parents=True, exist_ok=True)
    merged = dict(DEFAULT)
    merged.update(data or {})
    CFG.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")

@dataclass
class PairingSession:
    code: str
    created_at: float
    expires_at: float

    def valid(self) -> bool:
        return time.time() < self.expires_at

class DeviceLinkManager:
    """
    Lightweight local-network companion bridge.

    Protocol intentionally simple for future Android client:
      {"type":"pair","code":"123456","name":"Moto G32"}
      {"type":"wake","source":"phone"}
      {"type":"state","state":"LISTENING"}
      {"type":"handoff","direction":"phone_to_pc","session_id":"..."}
      {"type":"ping"}

    The current Windows build is server-side only. Android client can be added later
    without changing this protocol.
    """
    def __init__(self):
        self.cfg = load()
        self._pair: Optional[PairingSession] = None
        self._sock = None
        self._thread = None
        self._stop = threading.Event()
        self.on_event: Optional[Callable[[dict], None]] = None
        self.clients = {}

    def local_ip(self) -> str:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
        except Exception:
            return "127.0.0.1"
        finally:
            s.close()

    def new_pairing_code(self) -> PairingSession:
        ttl = int(self.cfg.get("pairing_code_ttl_s", 180))
        code = f"{secrets.randbelow(1_000_000):06d}"
        self._pair = PairingSession(code, time.time(), time.time()+ttl)
        return self._pair

    def pairing_info(self) -> dict:
        p = self._pair
        return {
            "ip": self.local_ip(),
            "port": int(self.cfg.get("port", 8767)),
            "code": p.code if p and p.valid() else "",
            "expires_at": p.expires_at if p else 0,
        }

    def _is_paired(self, device_id: str) -> bool:
        return any(str(x.get("id")) == str(device_id) for x in self.cfg.get("paired_devices", []))

    def _remember_device(self, device_id: str, name: str):
        devices = list(self.cfg.get("paired_devices", []))
        if not any(str(x.get("id")) == str(device_id) for x in devices):
            devices.append({
                "id": device_id,
                "name": name or "Android",
                "paired_at": time.time(),
            })
            self.cfg["paired_devices"] = devices
            save(self.cfg)

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        if not self.cfg.get("enabled", True):
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        try:
            if self._sock:
                self._sock.close()
        except Exception:
            pass

    def _serve(self):
        host = "0.0.0.0"
        port = int(self.cfg.get("port", 8767))
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((host, port))
        srv.listen(6)
        srv.settimeout(1.0)
        self._sock = srv

        while not self._stop.is_set():
            try:
                conn, addr = srv.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            threading.Thread(target=self._client, args=(conn, addr), daemon=True).start()

    def _client(self, conn, addr):
        conn.settimeout(60)
        f = conn.makefile("rwb")
        device_id = ""
        try:
            while not self._stop.is_set():
                line = f.readline()
                if not line:
                    break
                try:
                    msg = json.loads(line.decode("utf-8"))
                except Exception:
                    continue

                typ = str(msg.get("type") or "").lower()

                if typ == "pair":
                    code = str(msg.get("code") or "")
                    name = str(msg.get("name") or "Android")
                    device_id = str(msg.get("device_id") or secrets.token_hex(8))

                    if self._pair and self._pair.valid() and code == self._pair.code:
                        self._remember_device(device_id, name)
                        self.clients[device_id] = {"name":name, "addr":addr, "conn":conn}
                        self._send(f, {
                            "type":"paired",
                            "ok":True,
                            "device_id":device_id,
                            "server":"JARVIS Windows",
                        })
                        self._emit({"type":"device_connected","device_id":device_id,"name":name})
                    else:
                        self._send(f, {"type":"paired","ok":False,"error":"Código inválido ou expirado"})
                    continue

                if not device_id:
                    device_id = str(msg.get("device_id") or "")
                if not self._is_paired(device_id):
                    self._send(f, {"type":"error","error":"Dispositivo não pareado"})
                    continue

                if typ == "ping":
                    self._send(f, {"type":"pong","time":time.time()})
                elif typ in {"wake","state","handoff","call","command","notification"}:
                    msg["device_id"] = device_id
                    self._emit(msg)
                    self._send(f, {"type":"ack","for":typ})
        except Exception:
            pass
        finally:
            if device_id:
                self.clients.pop(device_id, None)
                self._emit({"type":"device_disconnected","device_id":device_id})
            try:
                f.close()
                conn.close()
            except Exception:
                pass

    def _send(self, f, obj: dict):
        f.write((json.dumps(obj, ensure_ascii=False)+"\n").encode("utf-8"))
        f.flush()

    def _emit(self, event: dict):
        if self.on_event:
            try:
                self.on_event(event)
            except Exception:
                pass

    def broadcast(self, obj: dict):
        dead = []
        payload = (json.dumps(obj, ensure_ascii=False)+"\n").encode("utf-8")
        for device_id, meta in list(self.clients.items()):
            try:
                meta["conn"].sendall(payload)
            except Exception:
                dead.append(device_id)
        for d in dead:
            self.clients.pop(d, None)
