@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
    echo Python Launcher nao encontrado. Instale Python 3 no Windows.
    pause
    exit /b 1
)
echo ===============================================
echo JARVIS Windows V22 ^| TESTES DE LOGICA - SEM EXE
 echo ===============================================
py -3 -m unittest discover -s tests -v
if errorlevel 1 (
  echo [ERRO] Um ou mais testes falharam. Nao declare esta versao validada.
) else (
  echo [OK] Testes de logica concluidos.
)
pause
