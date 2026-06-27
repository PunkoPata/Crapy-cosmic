@echo off
title CRAPY-COSMIC Ultra Pack

echo ===============================
echo   CRAPY-COSMIC BUILDER ULTRA
echo ===============================
echo.

REM Comprobar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no encontrado
    pause
    exit /b
)

REM Ruta 7-Zip
set SEVENZIP="C:\Program Files\7-Zip\7z.exe"

if not exist %SEVENZIP% (
    echo ERROR: No se encuentra 7-Zip
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
echo Limpiando...

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist release rmdir /s /q release
if exist crapy-cosmic.spec del crapy-cosmic.spec
if exist crapy-cosmic-ultra.7z del crapy-cosmic-ultra.7z

mkdir release

echo.
echo Generando EXE...

python -m PyInstaller ^
    --onefile ^
    --clean ^
    --name crapy-cosmic ^
    crapy-cosmic.py


if not exist dist\crapy-cosmic.exe (
    echo ERROR creando EXE
    pause
    exit /b
)

copy dist\crapy-cosmic.exe release\


(
echo CRAPY-COSMIC
echo.
echo Ejecutable:
echo crapy-cosmic.exe
echo.
echo No requiere Python instalado.
) > release\README.txt


echo.
echo Comprimiendo con 7-Zip ULTRA...

%SEVENZIP% a ^
-m0=lzma2 ^
-mx=9 ^
-md=64m ^
-ms=on ^
-mfb=273 ^
crapy-cosmic-ultra.7z ^
release\*


echo.
echo ===============================
echo   TERMINADO
echo ===============================

for %%A in (crapy-cosmic-ultra.7z) do echo Tamano final: %%~zA bytes

pause