@echo off
chcp 65001 >nul
echo Démarrage du serveur yt-dlp Web Interface...
echo.

set "PROJECT_DIR=%~dp0"
set "PROJECT_ROOT=%PROJECT_DIR%.."
set "PATH=%PROJECT_ROOT%\Binaries;%PATH%"

where deno >nul 2>&1
if %errorlevel% neq 0 (
    echo ERREUR: Deno n'est pas trouvé dans le PATH
    pause
    exit /b 1
)

echo Deno trouvé:
where deno
echo.

cd /d "%PROJECT_ROOT%"
python Backend\app.py

pause
