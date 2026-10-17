@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title JARVIS - Localizacao Precisa Opcional

echo ============================================================
echo LOCALIZACAO PRECISA DO WINDOWS - OPCIONAL
echo ============================================================
echo.
echo Isto NAO e necessario para o JARVIS funcionar ou compilar.
echo A localizacao aproximada/manual continua disponivel.
echo.
echo Para evitar incompatibilidade, este recurso usa Python 3.12.
echo.

py -3.12 -c "import sys" >nul 2>nul
if errorlevel 1 (
    echo [ERRO] Python 3.12 nao encontrado.
    echo Nao instale winsdk no seu Python 3.14.
    pause
    exit /b 1
)

if not exist ".venv-optional-location\Scripts\python.exe" (
    py -3.12 -m venv ".venv-optional-location"
)

".venv-optional-location\Scripts\python.exe" -m pip install --upgrade pip
".venv-optional-location\Scripts\python.exe" -m pip install -r requirements-optional-windows.txt

echo.
echo Componente opcional instalado em ambiente separado.
pause
