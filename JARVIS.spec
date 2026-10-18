# Windows x64 portable bundle. No personal config or credentials are included.
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules, collect_all
root = Path(SPECPATH)
datas = []
hidden = ['main', 'ui', 'tkinter', 'PyQt6.QtMultimedia', 'PyQt6.QtMultimediaWidgets']
for package in ('core', 'actions', 'plugins', 'memory', 'dashboard', 'ui_components'):
    hidden += collect_submodules(package)
    for path in (root / package).rglob('*'):
        if path.is_file() and path.suffix in ('.py', '.txt', '.obj', '.html', '.css', '.js', '.svg', '.png', '.json') and '__pycache__' not in path.parts:
            # Only source and static resources; runtime memory and config are excluded.
            if path.suffix == '.json':
                continue
            datas.append((str(path), str(path.parent.relative_to(root))))
for path in (root / 'assets').rglob('*'):
    if path.is_file(): datas.append((str(path), str(path.parent.relative_to(root))))
for path in root.glob('configur*.py'):
    datas.append((str(path), '.')); hidden.append(path.stem)
datas += [(str(root / 'painel_configuracoes.py'), '.'), (str(root / 'LICENSE'), '.')]
hidden += ['painel_configuracoes', 'edge_tts', 'miniaudio']
binaries = []
for package in ('moderngl', 'glcontext', 'playwright', 'openwakeword'):
    d, b, h = collect_all(package)
    datas += d; binaries += b; hidden += h
if (root / 'browsers').exists(): datas.append((str(root / 'browsers'), 'browsers'))
a = Analysis([str(root / 'windows_launcher.py')], pathex=[str(root)],
             binaries=binaries, datas=datas, hiddenimports=hidden,
             excludes=['PySide6','PySide2','PyQt5'], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='JARVIS',
          debug=False, strip=False, upx=False, console=False, contents_directory='.')
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='JARVIS')
