"""Frozen Windows entrypoint and approved configuration-script dispatcher."""
from __future__ import annotations
import multiprocessing
import os
from pathlib import Path
import runpy
import sys
import traceback

ROOT = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent
SCRIPTS = {'painel_configuracoes.py', 'configurar_jarvis.py', 'configurar_recursos.py',
           'configurar_casa_inteligente.py', 'configurar_gemini_gratis.py',
           'configurar_groq.py', 'configure_claude.py', 'main.py'}


def smoke_test():
    """Exercise packaged imports, settings window, assets and the actual shader."""
    import json
    import importlib
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    for module in ('main', 'sounddevice', 'google.genai', 'cv2', 'playwright.sync_api',
                   'core.ember_renderer', 'win32com.client', 'actions.screen_processor'):
        importlib.import_module(module)
    from painel_configuracoes import Panel
    panel = Panel()
    panel.update_idletasks()
    panel.update()
    assert len(panel.tabs) >= 12
    panel.destroy()
    from ui import JarvisUI
    desktop_ui = JarvisUI('face.png')
    app.processEvents()
    assert desktop_ui._win.isVisible(), 'Main window did not open'
    assert desktop_ui._win._desktop_controls.isVisible(), 'Desktop settings controls did not open'
    desktop_ui._win.close()
    app.processEvents()
    for asset in ('assets/shaders/ember_volume.frag', 'assets/shaders/ember_bloom.frag',
                  'core/prompt.txt', 'core/face_model.obj'):
        if not (ROOT / asset).is_file():
            raise FileNotFoundError(asset)
    from core.ember_cpu import CPUEmberRenderer
    cpu = CPUEmberRenderer('economy')
    try:
        for state in ('IDLE','LISTENING','THINKING','SPEAKING'):
            assert len(cpu.render(state,.5,dt=.1)) == cpu.size*cpu.size*4
    finally:
        cpu.close()
    # Hosted Windows runners may have no usable OpenGL driver. Record the outcome
    # separately rather than pretending that software-only CI validates the GPU.
    gpu = {'status': 'not_available'}
    try:
        from core.ember_renderer import EmberRenderer
        renderer = EmberRenderer('economy')
        try:
            for state in ('IDLE', 'LISTENING', 'THINKING', 'SPEAKING'):
                frame = renderer.render(state, .4, dt=.1)
                assert len(frame) == renderer.size * renderer.size * 4
            gpu = {'status': 'passed', 'renderer': renderer.ctx.info.get('GL_RENDERER')}
        finally:
            renderer.close()
    except Exception as exc:
        gpu['reason'] = str(exc)
    report = {'packaged_imports': 'passed', 'settings_window': 'passed', 'main_window': 'passed', 'desktop_settings_controls': 'passed',
              'assets': 'passed', 'cpu_fire_smoke': 'passed', 'gpu': gpu, 'live_audio_api': 'not_tested',
              'smart_home_hardware': 'not_tested'}
    (ROOT / 'smoke-test.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    app.quit()


def main():
    multiprocessing.freeze_support()
    os.chdir(ROOT)
    os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH', str(ROOT / 'browsers'))
    # Windowed executables have no stdout/stderr: preserve actionable failures.
    if getattr(sys, 'frozen', False):
        log_dir = Path(os.environ.get('LOCALAPPDATA', str(ROOT))) / 'JarvisOS' / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        for stream in ('stdout', 'stderr'):
            if getattr(sys, stream) is None:
                setattr(sys, stream, (log_dir / f'{os.getpid()}.log').open('a', encoding='utf-8', buffering=1))
    try:
        args = sys.argv[1:]
        if '--smoke-test' in args:
            smoke_test()
        elif '--visual-test' in args:
            from core.visual_test import main as visual_main
            visual_main()
        elif '--settings' in args:
            runpy.run_path(str(ROOT / 'painel_configuracoes.py'), run_name='__main__')
        elif args and Path(args[0]).suffix.lower() == '.py':
            # Existing configuration buttons relaunch sys.executable with a path.
            name = Path(args[0]).name
            if name not in SCRIPTS:
                raise ValueError(f'Ferramenta não autorizada: {name}')
            sys.argv = [str(ROOT / name), *args[1:]]
            if name == 'main.py':
                import main as application
                application.main()
            else:
                runpy.run_path(str(ROOT / name), run_name='__main__')
        else:
            import main as application
            application.main()
    except Exception:
        traceback.print_exc()
        if '--smoke-test' not in sys.argv:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, 'Não foi possível iniciar o JARVIS. Consulte os logs em %LOCALAPPDATA%\\JarvisOS\\logs.', 'JARVIS — erro de inicialização', 16)
        raise SystemExit(1)


if __name__ == '__main__':
    main()
