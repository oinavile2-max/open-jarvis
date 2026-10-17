@echo off
setlocal
cd /d "%~dp0"
title JARVIS - Instalacao

echo ==============================================
echo   JARVIS - INSTALACAO PARA WINDOWS
echo ==============================================
echo.
where py >nul 2>nul
if %errorlevel%==0 (
  set "PY=py"
) else (
  set "PY=python"
)

%PY% -m venv .venv
if errorlevel 1 goto :err
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 goto :err

echo.
echo Instalacao concluida.
echo Agora execute CONFIGURAR_GEMINI_GRATIS.bat
pause
exit /b 0
:err
echo.
echo Falha na instalacao. Verifique se o Python 3.11-3.13 esta instalado e tente novamente.
pause
exit /b 1
