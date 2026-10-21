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


async def verify_packaged_mcp():
    """Credential-free protocol check performed by the frozen executable."""
    import asyncio
    import json
    import httpx
    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client
    from core.mcp_bridge import MCPBridge

    async def execute(name, arguments):
        return {'result': 'online'}

    bridge = MCPBridge([{'name': 'system_status', 'parameters': {'type': 'object'}}], execute, {})
    try:
        async with asyncio.timeout(20):
            path = await bridge.start()
            server = json.loads(path.read_text())['mcpServers']['jarvis']
            async with httpx.AsyncClient(trust_env=False) as client:
                denied = await client.post(server['url'], json={})
                assert denied.status_code == 401, 'MCP accepted a missing token'
            def local_client(**kwargs):
                return httpx.AsyncClient(trust_env=False, follow_redirects=True, **kwargs)
            async with streamablehttp_client(server['url'], headers=server['headers'], httpx_client_factory=local_client) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools = await session.list_tools()
                    assert {tool.name for tool in tools.tools} == {'jarvis_list_tools', 'jarvis_execute'}
                    result = await session.call_tool('jarvis_execute', {'name': 'system_status', 'arguments': {}})
                    assert not result.isError, 'Authorized MCP call failed'
                    blocked = await session.call_tool('jarvis_execute', {'name': 'delete_files', 'arguments': {}})
                    assert blocked.isError, 'Unlisted MCP action was accepted'
    finally:
        await bridge.close()
    return 'passed'


def smoke_test():
    """Exercise packaged imports, settings window, assets and the actual shader."""
    import json
    import importlib
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    for module in ('main', 'sounddevice', 'google.genai', 'cv2', 'playwright.sync_api',
                   'core.ember_renderer', 'win32com.client', 'actions.screen_processor',
                   'core.claude_brain', 'core.mcp_bridge', 'core.startup_settings'):
        importlib.import_module(module)
    from painel_configuracoes import Panel
    panel = Panel()
    panel.update_idletasks()
    panel.update()
    assert panel.fish_voice_id.get() == '4ff2cc8f7c524b38a7fa110e4e12c72d'
    assert hasattr(panel, 'fish_key')
    assert 'Claude / MCP' in panel.tabs
    assert panel.brain_provider.get() == 'claude_code'
    assert panel.claude_model.get() == 'sonnet'
    assert hasattr(panel, 'mcp_servers')
    assert len(panel.tabs) >= 12
    panel.destroy()
    from ui import JarvisUI
    desktop_ui = JarvisUI('face.png')
    app.processEvents()
    assert desktop_ui._win.isVisible(), 'Main window did not open'
    assert desktop_ui._win._desktop_controls.isVisible(), 'Desktop settings controls did not open'
    assert desktop_ui._win.hud.hud_style == 'neural_blue', 'Blue sphere default missing'
    desktop_ui._win._open_quick_menu()
    app.processEvents()
    assert desktop_ui._win._quick_menu.isVisible(), 'Quick menu missing'
    desktop_ui._win._quick_menu.hide()
    from PyQt6.QtWidgets import QLabel
    note = QLabel()
    for style in ('particle', 'nebula', 'neural_blue'):
        desktop_ui._win._apply_quick_orb(style, note)
        assert desktop_ui._win.hud.hud_style == style, note.text()
    desktop_ui._win._open_photo_profiles()
    app.processEvents()
    assert desktop_ui._win._photo_dialog.isVisible()
    desktop_ui._win._photo_dialog.close()
    from core.face_profiles import FaceMatcher
    FaceMatcher(ROOT/'assets'/'face_models')
    desktop_ui._win.set_wallpaper_mode(False)
    desktop_ui._win._show_content('Pesquisa', 'Search results for: teste\n\n1. Fonte de teste\nResumo legível.\nSource: https://example.com')
    app.processEvents()
    assert desktop_ui._win._search_cards_widget is not None
    desktop_ui._win.grab().save(str(ROOT / 'smoke-main.png'))
    # Smoke settings are isolated from the shipped default.
    ux = ROOT / 'config' / 'ux.json'
    if ux.exists(): ux.unlink()
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
    import asyncio
    mcp_status = asyncio.run(verify_packaged_mcp())
    report = {'claude_settings': 'passed', 'mcp_local_protocol': mcp_status,
              'claude_login': 'not_tested', 'packaged_imports': 'passed', 'settings_window': 'passed', 'main_window': 'passed', 'desktop_settings_controls': 'passed',
              'assets': 'passed', 'quick_menu': 'passed', 'sphere_switch': 'passed', 'fish_settings': 'passed', 'photo_dialog': 'passed', 'face_models_load': 'passed', 'search_cards': 'passed', 'cpu_fire_smoke': 'passed', 'gpu': gpu, 'live_audio_api': 'not_tested',
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
