@echo off
REM ============================================================
REM EduPaie - Build complet : exe PyInstaller + installateur Inno Setup
REM Usage : tools\build_installer.bat
REM Prerequis : Inno Setup 6 (winget install -e --id JRSoftware.InnoSetup)
REM Sortie  : output\EduPaie-Setup-<version>.exe
REM ============================================================
setlocal
pushd "%~dp0.."
cd

set ISCC="%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if not exist %ISCC% set ISCC="%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist %ISCC% set ISCC="%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not exist %ISCC% (
    echo.
    echo *** Inno Setup 6 introuvable ***
    echo Installez-le avec : winget install -e --id JRSoftware.InnoSetup
    popd
    exit /b 1
)

echo.
echo [1/2] Construction de l'executable (tests inclus)...
call "%CD%\build.bat"
if errorlevel 1 goto :erreur

echo.
echo [2/2] Compilation de l'installateur...
%ISCC% "%CD%\tools\installer.iss"
if errorlevel 1 goto :erreur

echo.
echo ============================================
echo  Installateur genere : output\EduPaie-Setup-1.0.0.exe
echo ============================================
popd
exit /b 0

:erreur
echo.
echo *** ECHEC DU BUILD INSTALLATEUR ***
popd
exit /b 1
