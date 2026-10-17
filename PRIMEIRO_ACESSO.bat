@echo off
cd /d "%~dp0"
python configurar_jarvis.py
if errorlevel 1 pause
