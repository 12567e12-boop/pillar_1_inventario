@echo off
title Bot de Telegram - Sistema de Requisiciones
cls

echo ============================================================
echo   Iniciando Bot de Telegram
echo ============================================================
echo.

REM Cambiar al directorio del proyecto
cd /d "%~dp0"

REM Activar entorno virtual
echo Activando entorno virtual...
call laZona\Scripts\activate

echo.
echo Ejecutando migraciones...
python manage.py migrate

echo.
echo Verificando superusuario...
python crear_superusuario.py

echo.
echo ============================================================
echo   Iniciando bot de Telegram...
echo   Presiona Ctrl+C para detener
echo ============================================================
echo.

python manage.py run_telegram_bot

pause
