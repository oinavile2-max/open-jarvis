@echo off
cd /d "%~dp0"
if exist .venv\Scripts\pythonw.exe (
  start "" .venv\Scripts\pythonw.exe configurar_gemini_gratis.py
) else if exist .venv\Scripts\python.exe (
  .venv\Scripts\python.exe configurar_gemini_gratis.py
) else (
  python configurar_gemini_gratis.py
)
