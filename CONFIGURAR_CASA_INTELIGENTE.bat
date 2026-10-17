@echo off
cd /d "%~dp0"
python configurar_casa_inteligente.py
if errorlevel 1 pause
