@echo off
setlocal EnableExtensions
cd /d "%~dp0\.."
title JARVIS - Preparar Ambiente de Build

echo ============================================================
echo JARVIS - AMBIENTE DE BUILD ESTAVEL
echo ============================================================
echo.
echo O build NAO usa mais o Python padrao do Windows.
echo Ele usa uma venv exclusiva com Python 3.12 ou 3.11.
echo.

set "PYEXE="

py -3.12 -c "import sys; print(sys.executable)" >nul 2>nul
if not errorlevel 1 set "PYEXE=py -3.12"

if not defined PYEXE (
    py -3.11 -c "import sys; print(sys.executable)" >nul 2>nul
    if not errorlevel 1 set "PYEXE=py -3.11"
)

if not defined PYEXE (
    echo [ERRO] Python 3.12 ou 3.11 nao foi encontrado.
    echo.
    echo Seu Python principal pode continuar instalado.
    echo Para compilar o JARVIS, instale Python 3.12 x64 lado a lado.
    echo Depois execute este arquivo novamente.
    pause
    exit /b 1
)

echo Python escolhido:
%PYEXE% --version
echo.

if exist ".venv-build\Scripts\python.exe" (
    echo Ambiente de build existente encontrado.
) else (
    echo Criando ambiente isolado .venv-build...
    %PYEXE% -m venv ".venv-build"
    if errorlevel 1 goto :erro
)

set "VPY=%CD%\.venv-build\Scripts\python.exe"

echo.
echo Atualizando pip/setuptools/wheel...
"%VPY%" -m pip install --upgrade pip setuptools wheel
if errorlevel 1 goto :erro

echo.
echo Validando regras permanentes de build...
"%VPY%" "scripts\VALIDAR_DEPENDENCIAS_BUILD.py"
if errorlevel 1 goto :erro

echo.
echo Instalando dependencias do BUILD, sem winsdk...
"%VPY%" -m pip install -r requirements-build.txt
if errorlevel 1 goto :erro

echo.
echo Instalando empacotador...
"%VPY%" -m pip install --upgrade pyinstaller edge-tts miniaudio
if errorlevel 1 goto :erro

echo.
echo ============================================================
echo AMBIENTE PRONTO.
echo Python do build:
"%VPY%" --version
echo.
echo winsdk NAO participa do build principal.
echo ============================================================
pause
exit /b 0

:erro
echo.
echo [ERRO] Falha ao preparar ambiente de build.
echo Tire um print e envie no chat.
pause
exit /b 1
