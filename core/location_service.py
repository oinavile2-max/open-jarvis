from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CFG = ROOT / "config" / "location.json"

DEFAULT = {
    "enabled": False,
    "mode": "auto",
    "manual_city": "",
    "manual_region": "",
    "last": {}
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

def _windows_location():
    try:
        import asyncio
        from winsdk.windows.devices.geolocation import Geolocator, GeolocationAccessStatus
        async def _get():
            status = await Geolocator.request_access_async()
            if status != GeolocationAccessStatus.ALLOWED:
                raise RuntimeError("Permissão de localização negada no Windows.")
            geo = Geolocator()
            pos = await geo.get_geoposition_async()
            p = pos.coordinate.point.position
            return {
                "source": "windows",
                "latitude": float(p.latitude),
                "longitude": float(p.longitude),
                "accuracy_m": float(pos.coordinate.accuracy or 0),
            }
        try:
            return asyncio.run(_get())
        except RuntimeError:
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(_get())
            finally:
                loop.close()
    except ModuleNotFoundError as e:
        if "winsdk" in str(e).lower():
            raise RuntimeError(
                "Localização precisa do Windows não instalada. "
                "Use modo automático/aproximado ou o instalador opcional."
            )
        raise RuntimeError(str(e))
    except Exception as e:
        raise RuntimeError(str(e))

def _approximate_ip():
    import requests
    r = requests.get("https://ipapi.co/json/", timeout=5)
    r.raise_for_status()
    d = r.json()
    return {
        "source": "approximate",
        "city": d.get("city") or "",
        "region": d.get("region") or "",
        "country": d.get("country_name") or "",
        "latitude": d.get("latitude"),
        "longitude": d.get("longitude"),
    }

def get_location():
    cfg = load()
    if not cfg.get("enabled"):
        raise RuntimeError("Localização desativada nas configurações.")
    mode = str(cfg.get("mode") or "auto").lower()

    if mode == "manual":
        city = str(cfg.get("manual_city") or "").strip()
        region = str(cfg.get("manual_region") or "").strip()
        if not city:
            raise RuntimeError("Defina uma cidade manualmente.")
        result = {"source":"manual","city":city,"region":region}
        cfg["last"] = result
        save(cfg)
        return result

    errors = []
    if mode in ("auto","windows"):
        try:
            result = _windows_location()
            cfg["last"] = result
            save(cfg)
            return result
        except Exception as e:
            errors.append(f"Windows: {e}")
            if mode == "windows":
                raise RuntimeError(" | ".join(errors))

    if mode in ("auto","approximate"):
        try:
            result = _approximate_ip()
            cfg["last"] = result
            save(cfg)
            return result
        except Exception as e:
            errors.append(f"Aproximada: {e}")

    raise RuntimeError("Não foi possível obter localização. " + " | ".join(errors))
