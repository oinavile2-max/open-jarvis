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

echo Gerando executavel Windows...
"%VPY%" -m PyInstaller --clean --noconfirm JARVIS.spec
if errorlevel 1 exit /b 1
copy "scripts\ABRIR_AJUSTES.bat" "dist\JARVIS\"
copy "scripts\TESTAR_ESFERA.bat" "dist\JARVIS\"
copy "docs\LEIA_PRIMEIRO_WINDOWS.txt" "dist\JARVIS\"
echo Pronto: dist\JARVIS\JARVIS.exe
pause
