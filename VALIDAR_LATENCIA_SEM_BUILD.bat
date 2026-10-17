@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Verificando logica de latencia JARVIS V22 (sem gerar EXE)...
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 -m unittest discover -s tests -v
) else (
  python -m unittest discover -s tests -v
)
echo.
if %errorlevel% neq 0 (
  echo Falha na validacao. Confirme que Python 3.11+ esta instalado.
) else (
  echo Testes de fila e sinalizacao passaram.
)
pause
