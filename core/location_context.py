from __future__ import annotations
import json, platform, subprocess, time, sys
from pathlib import Path


def _base() -> Path:
    if getattr(sys,'frozen',False): return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent

CACHE=_base()/'config'/'location_cache.json'


def _read() -> dict:
    try: return json.loads(CACHE.read_text(encoding='utf-8'))
    except Exception: return {}


def refresh_location(timeout: float=5.0) -> dict:
    """Tenta usar o serviço de Localização do Windows. Não envia coordenadas a terceiros.
    Requer que o usuário tenha permitido Localização no Windows. Retém apenas um cache local.
    """
    old=_read()
    if old and time.time()-float(old.get('ts',0)) < 900:
        return old
    if platform.system() != 'Windows':
        return old
    ps = r'''Add-Type -AssemblyName System.Device
$w = New-Object System.Device.Location.GeoCoordinateWatcher([System.Device.Location.GeoPositionAccuracy]::Default)
$w.Start()
$limit = (Get-Date).AddSeconds(4)
while ($w.Status -ne 'Ready' -and (Get-Date) -lt $limit) { Start-Sleep -Milliseconds 150 }
$p = $w.Position.Location
if (-not $p.IsUnknown) { $c=[Globalization.CultureInfo]::InvariantCulture; Write-Output ($p.Latitude.ToString($c)+"|"+$p.Longitude.ToString($c)+"|"+$p.HorizontalAccuracy.ToString($c)) }
$w.Stop()'''
    try:
        cp=subprocess.run(['powershell','-NoProfile','-NonInteractive','-Command',ps],capture_output=True,text=True,timeout=max(4,timeout),creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        line=(cp.stdout or '').strip().splitlines()[-1] if (cp.stdout or '').strip() else ''
        if line:
            lat,lon,acc=[float(x) for x in line.split('|')[:3]]
            data={'lat':lat,'lon':lon,'accuracy_m':acc,'ts':time.time(),'source':'Windows Location'}
            CACHE.parent.mkdir(parents=True,exist_ok=True); CACHE.write_text(json.dumps(data,indent=2),encoding='utf-8')
            return data
    except Exception:
        pass
    return old


def get_location() -> dict:
    return _read()


def get_location_summary() -> str:
    d=_read()
    if not d:
        return 'Localização: indisponível\nAtive “Serviços de localização” no Windows para personalização.'
    # UI deliberately shows coarse coordinates, while the cache retains the local reading.
    return f"Localização do Windows: {d['lat']:.2f}, {d['lon']:.2f}\nPrecisão reportada: ~{d.get('accuracy_m',0):.0f} m"


def prompt_context() -> str:
    d=_read()
    if not d: return '[LOCALIZAÇÃO]\nLocalização não disponível ou sem permissão.'
    return (f"[LOCALIZAÇÃO DO USUÁRIO]\nCoordenadas atuais do Windows: {d['lat']:.4f}, {d['lon']:.4f}. "
            f"Precisão aproximada: {d.get('accuracy_m',0):.0f} m. Use apenas quando a pergunta depender do local; não recite coordenadas sem necessidade.")
