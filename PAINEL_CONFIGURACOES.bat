@echo off
cd /d "%~dp0"
python painel_configuracoes.py
if errorlevel 1 pause
