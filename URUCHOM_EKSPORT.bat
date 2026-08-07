@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Nie znaleziono srodowiska .venv. Najpierw je utworz i zainstaluj playwright.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" feedybacky_export.py %*
set EXIT_CODE=%ERRORLEVEL%

echo.
if not "%EXIT_CODE%"=="0" (
    echo Program zakonczyl sie bledem o kodzie %EXIT_CODE%.
)
pause
exit /b %EXIT_CODE%
