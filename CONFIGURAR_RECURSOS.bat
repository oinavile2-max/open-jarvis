@echo off
cd /d "%~dp0"
python configurar_recursos.py
if errorlevel 1 pause
