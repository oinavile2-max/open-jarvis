@echo off
cd /d "%~dp0"
python -c "from core.user_setup import is_complete; raise SystemExit(0 if is_complete() else 5)"
if errorlevel 5 (
  python configurar_jarvis.py
)
python main.py
if errorlevel 1 pause
