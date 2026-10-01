@echo off
REM ============================================================
REM EduPaie - Script de build Windows
REM Produit dist\EduPaie.exe (onefile, sans console, icone + version)
REM Usage : build.bat
REM ============================================================
setlocal
cd /d "%~dp0"

REM Disque C: sature : rediriger les fichiers temporaires vers la racine du
REM projet (drive E: ici). Sans effet si C: dispose d'assez d'espace.
set "TEMP=%~dp0.build_tmp"
set "TMP=%~dp0.build_tmp"
if not exist "%TEMP%" mkdir "%TEMP%"

set PY=.venv\Scripts\python.exe
if not exist "%PY%" set PY=python

echo.
echo [1/3] Generation des ressources de marque (logo, icone)...
"%PY%" tools\generate_assets.py
if errorlevel 1 goto :erreur

echo.
echo [2/3] Verification : tests metier...
"%PY%" -m unittest discover -s tests -v
if errorlevel 1 goto :erreur

echo.
echo [3/3] Construction de l'executable (PyInstaller)...

REM Supprimer l'exe precedent : PyInstaller doit pouvoir le remplacer.
REM Un exe fraichement ecrit peut etre verrouille quelques secondes par
REM l'antivirus, ou par l'application si elle est encore en cours d'execution.
if exist "dist\EduPaie.exe" (
    del /f /q "dist\EduPaie.exe" 2>nul
    if exist "dist\EduPaie.exe" (
        taskkill /f /im EduPaie.exe >nul 2>&1
        timeout /t 4 /nobreak >nul
        del /f /q "dist\EduPaie.exe" 2>nul
    )
    if exist "dist\EduPaie.exe" (
        echo *** dist\EduPaie.exe est verrouille : fermez EduPaie puis relancez. ***
        goto :erreur
    )
)
"%PY%" -m PyInstaller EduPaie.spec --noconfirm --clean --workpath ".venv\pyinstaller-work" --distpath "dist"
if errorlevel 1 goto :erreur

echo.
echo ============================================
echo  Build termine : dist\EduPaie.exe
echo ============================================
exit /b 0

:erreur
echo.
echo *** ECHEC DU BUILD ***
exit /b 1
