@echo off
REM ============================================================
REM EduPaie - Script de build Windows
REM Produit dist\EduPaie.exe (onefile, sans console, icone + version)
REM Usage : build.bat
REM ============================================================
setlocal
cd /d "%~dp0"

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
"%PY%" -m PyInstaller EduPaie.spec --noconfirm --clean
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
