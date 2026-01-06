@echo off
title Instalar Dependencias del Bot
cls

echo ============================================================
echo   Instalando dependencias necesarias para el bot
echo ============================================================
echo.

cd /d "%~dp0"

echo Activando entorno virtual...
call laZona\Scripts\activate

echo.
echo Instalando python-telegram-bot...
pip install python-telegram-bot==20.7

echo.
echo Instalando Pillow (para procesar imágenes)...
pip install Pillow

echo.
echo Instalando asgiref (para async)...
pip install asgiref

echo.
echo ============================================================
echo   Instalación completada
echo ============================================================
echo.
echo Ahora puedes ejecutar el bot con: iniciar_bot.bat
echo.

pause
