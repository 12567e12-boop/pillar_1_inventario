@echo off
title Limpiar Cache del Proyecto
cls

echo ============================================================
echo   Limpiando cache de Python (.pyc y __pycache__)
echo ============================================================
echo.

cd /d "%~dp0"

REM Eliminar todos los archivos .pyc
echo Eliminando archivos .pyc...
del /s /q *.pyc 2>nul

REM Eliminar carpetas __pycache__
echo Eliminando carpetas __pycache__...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"

REM Eliminar migraciones (opcional, descomentar si es necesario)
REM echo Eliminando migraciones...
REM for /d /r . %%d in (migrations) do @if exist "%%d" del /s /q "%%d\*.py" 2>nul
REM for /d /r . %%d in (migrations) do @if exist "%%d\__pycache__" rd /s /q "%%d\__pycache__" 2>nul

echo.
echo ============================================================
echo   Limpiando archivos estáticos recopilados...
echo ============================================================
echo.

REM Eliminar archivos estáticos recopilados
if exist "staticfiles" (
    echo Eliminando archivos estáticos...
    rmdir /s /q "staticfiles" 2>nul
)

echo.
echo ============================================================
echo   Instrucciones para limpiar la caché del navegador:
echo ============================================================
echo.
echo 1. Presione Ctrl+Shift+Supr en su navegador
echo 2. Seleccione "Todo" en el rango de tiempo
echo 3. Marque "Imágenes y archivos almacenados en caché"
echo 4. Haga clic en "Borrar datos"
echo.
echo ============================================================
echo   Limpieza completada. Presione cualquier tecla para salir...
echo ============================================================

pause >nul
echo Ahora puedes reiniciar el bot con: iniciar_bot.bat
echo.

pause
