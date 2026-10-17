@echo off
title Instalador JARVIS
cd /d "%~dp0"
echo ============================================
echo       INSTALADOR JARVIS - WINDOWS
echo ============================================
echo.
where python >nul 2>nul
if errorlevel 1 (
  echo Python nao foi encontrado.
  echo Instale Python 3.11 ou superior e execute novamente.
  pause
  exit /b 1
)

echo Instalando componentes...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo.
  echo Falha ao instalar dependencias.
  pause
  exit /b 1
)

echo.
echo Instalacao concluida.
echo Abrindo configuracao inicial...
python configurar_jarvis.py
