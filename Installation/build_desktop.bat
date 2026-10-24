@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul

echo ============================================================
echo   MARIHAR - Build Desktop App
echo ============================================================
echo.

set "PYTHON_EXE="
set "PYTHON_CANDIDATE="

call :try_python "C:\Python312\python.exe"
if not defined PYTHON_EXE call :try_python "%LocalAppData%\Programs\Python\Python312\python.exe"

echo [1/6] Verification de Python...
echo.
if not defined PYTHON_EXE (
    echo [ERREUR] Python 3.12 requis mais non fonctionnel.
    echo Chemins testes:
    echo   - C:\Python312\python.exe
    echo   - %LocalAppData%\Programs\Python\Python312\python.exe
    echo.
    echo Reinstallez Python 3.12 puis relancez ce script.
    pause
    exit /b 1
)

echo Python utilise: %PYTHON_EXE%
%PYTHON_EXE% --version
echo.
echo [2/6] Installation des dependances...
echo.
%PYTHON_EXE% -m pip install --upgrade pip >nul 2>&1
%PYTHON_EXE% -m pip install pywebview==5.3.2 flask flask-cors pyinstaller
if errorlevel 1 (
    echo [ERREUR] Echec de l'installation des dependances
    pause
    exit /b 1
)

echo.
echo [3/6] Verification des fichiers essentiels...
echo.
set "FILES_OK=1"
if not exist "..\Binaries\yt-dlp.exe" (
    echo [ERREUR] Binaries\yt-dlp.exe manquant
    set "FILES_OK=0"
)
if not exist "..\Binaries\ffmpeg.exe" (
    echo [ERREUR] Binaries\ffmpeg.exe manquant
    set "FILES_OK=0"
)
if not exist "..\Frontend\templates\index.html" (
    echo [ERREUR] Frontend\templates\index.html manquant
    set "FILES_OK=0"
)
if not exist "..\Frontend\static\css\style.css" (
    echo [ERREUR] Frontend\static\css\style.css manquant
    set "FILES_OK=0"
)
if not exist "..\MARIHAR.spec" (
    echo [ERREUR] MARIHAR.spec manquant
    set "FILES_OK=0"
)
if "%FILES_OK%"=="0" (
    echo.
    echo [ERREUR] Build annule: fichiers manquants.
    pause
    exit /b 1
)

echo.
echo [4/6] Preparation des dossiers...
echo.

set "DIST_BACKUP="
if exist "dist" (
    set "DIST_BACKUP=dist_backup"
    if exist "!DIST_BACKUP!" rmdir /s /q "!DIST_BACKUP!"
    ren "dist" "dist_backup"
)
if exist "build" rmdir /s /q "build"
if exist "dist_static" rmdir /s /q "dist_static"

echo.
echo [5/6] Compilation PyInstaller...
echo.
set "BUILD_LOG=build_last.log"
if exist "%BUILD_LOG%" del /q "%BUILD_LOG%"

%PYTHON_EXE% -m PyInstaller --noconfirm --clean "..\MARIHAR.spec" > "%BUILD_LOG%" 2>&1
if errorlevel 1 (
    echo [ERREUR] Echec de compilation. Voir build_last.log
    if exist "dist" rmdir /s /q "dist"
    if defined DIST_BACKUP if exist "dist_backup" ren "dist_backup" "dist"
    if exist "dist_static" rmdir /s /q "dist_static"
    type "%BUILD_LOG%"
    pause
    exit /b 1
)

echo.
echo [6/6] Finalisation...
echo.
if exist "dist\MARIHAR\MARIHAR.exe" goto success_onedir
if exist "dist\MARIHAR.exe" goto success_onefile
goto fail_no_output

:success_onedir
if defined DIST_BACKUP if exist "dist_backup" rmdir /s /q "dist_backup"
if exist "dist_static" rmdir /s /q "dist_static"
echo ============================================================
echo   BUILD REUSSI
echo ============================================================
echo Executable: dist\MARIHAR\MARIHAR.exe
echo Log build : %BUILD_LOG%
goto done

:success_onefile
if defined DIST_BACKUP if exist "dist_backup" rmdir /s /q "dist_backup"
if exist "dist_static" rmdir /s /q "dist_static"
echo ============================================================
echo   BUILD REUSSI (onefile)
echo ============================================================
echo Executable: dist\MARIHAR.exe
echo Log build : %BUILD_LOG%
goto done

:fail_no_output
echo [ERREUR] Aucune sortie detectee dans dist.
echo Voir le log: %BUILD_LOG%
if exist "dist" rmdir /s /q "dist"
if defined DIST_BACKUP if exist "dist_backup" ren "dist_backup" "dist"
if exist "dist_static" rmdir /s /q "dist_static"
type "%BUILD_LOG%"
pause
exit /b 1

:done

echo.
pause
goto :eof

:try_python
set "PYTHON_CANDIDATE=%~1"
set "PY_PROBE_FILE=%TEMP%\marihar_py_probe.txt"
if exist "%PY_PROBE_FILE%" del /q "%PY_PROBE_FILE%" >nul 2>&1

if not exist "%PYTHON_CANDIDATE%" (
    if /I "%PYTHON_CANDIDATE%"=="python" (
        python -c "print('PY_OK')" > "%PY_PROBE_FILE%" 2>nul
        set "PY_PROBE="
        if exist "%PY_PROBE_FILE%" set /p PY_PROBE=<"%PY_PROBE_FILE%"
        if /I "!PY_PROBE!"=="PY_OK" set "PYTHON_EXE=python"
    )
    if exist "%PY_PROBE_FILE%" del /q "%PY_PROBE_FILE%" >nul 2>&1
    goto :eof
)

"%PYTHON_CANDIDATE%" -c "print('PY_OK')" > "%PY_PROBE_FILE%" 2>nul
set "PY_PROBE="
if exist "%PY_PROBE_FILE%" set /p PY_PROBE=<"%PY_PROBE_FILE%"
if /I "!PY_PROBE!"=="PY_OK" set "PYTHON_EXE=%PYTHON_CANDIDATE%"
if exist "%PY_PROBE_FILE%" del /q "%PY_PROBE_FILE%" >nul 2>&1
goto :eof
