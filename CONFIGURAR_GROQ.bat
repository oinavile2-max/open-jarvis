@echo off
cd /d "%~dp0"
python configurar_groq.py
if errorlevel 1 pause
