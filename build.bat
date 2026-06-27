@echo off
title CRAPY-COSMIC Builder (OUTSIDE DIR)

REM ===============================
REM CONFIG
REM ===============================
set VERSION=1.0.0
set OUTDIR=..\crapy-cosmic-build

echo ===============================
echo   CRAPY-COSMIC v%VERSION%
echo   OUTPUT: %OUTDIR%
echo ===============================
echo.

REM Crear carpeta externa
if not exist "%OUTDIR%" mkdir "%OUTDIR%"

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no encontrado
    pause
    exit /b
)

REM Instalar PyInstaller si falta
python -m pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Instalando PyInstaller...
    python -m pip install pyinstaller
)

echo.
echo LIMPIANDO...

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist release rmdir /s /q release
if exist crapy-cosmic.spec del crapy-cosmic.spec

if exist "%OUTDIR%" rmdir /s /q "%OUTDIR%"
mkdir "%OUTDIR%"
mkdir "%OUTDIR%\release"

echo.
echo COMPILANDO...

python -m PyInstaller ^
    --onefile ^
    --clean ^
    --name crapy-cosmic ^
    crapy-cosmic.py


if not exist dist\crapy-cosmic.exe (
    echo ERROR: No se genero el ejecutable
    pause
    exit /b
)

echo.
echo COPIANDO RESULTADOS...

copy dist\crapy-cosmic.exe "%OUTDIR%\release\"

(
echo CRAPY-COSMIC
echo Version: %VERSION%
echo.
echo Ejecutable: crapy-cosmic.exe
echo.
echo Generado automaticamente.
) > "%OUTDIR%\release\README.txt"

echo.
echo COMPRIMIENDO EN DIRECTORIO PADRE...

powershell -Command ^
"Compress-Archive -Path '%OUTDIR%\release\*' -DestinationPath '%OUTDIR%\crapy-cosmic-release-v%VERSION%.zip' -CompressionLevel Optimal -Force"

echo.
echo ===============================
echo LISTO
echo ===============================
echo.
echo Archivo final:
echo %OUTDIR%\crapy-cosmic-release-v%VERSION%.zip

echo.
echo Limpiando compilaciones anteriores...

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist crapy-cosmic.spec del crapy-cosmic.spec


pause