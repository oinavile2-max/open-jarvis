@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title JARVIS - Build de Teste Seguro

echo ============================================================
echo JARVIS - BUILD DE TESTE SEGURO
echo ============================================================
echo.

if not exist ".venv-build\Scripts\python.exe" (
    echo Preparando ambiente isolado primeiro...
    call "scripts\PREPARAR_AMBIENTE_BUILD.bat"
    if errorlevel 1 exit /b 1
)

set "VPY=%CD%\.venv-build\Scripts\python.exe"

echo Validando dependencias...
"%VPY%" "scripts\VALIDAR_DEPENDENCIAS_BUILD.py"
if errorlevel 1 (
    pause
    exit /b 1
)

echo.
echo Ambiente validado.
echo O script de empacotamento sera executado apenas quando autorizado.
echo.
echo Nesta V22 o problema winsdk/Python 3.14 foi bloqueado na origem.
pause
