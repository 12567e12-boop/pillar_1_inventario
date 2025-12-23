@echo off
title Iniciar Servicios y Ngrok
cls

echo Deteniendo procesos anteriores...
taskkill /f /im ngrok.exe >nul 2>&1
taskkill /f /im python.exe >nul 2>&1

echo Iniciando servidor de Inventario...
start "Inventario" cmd /c "cd /d C:\Users\dreat\OneDrive\Escritorio\DEMO\pillar_1_inventario-main && python manage.py runserver 0.0.0.0:8000"

echo Iniciando servidor de Dreacht Hub...
start "Dreacht" cmd /c "cd /d C:\Users\dreat\OneDrive\Escritorio\DEMO\dreacht_hub_web-master && dreacht_venv\Scripts\python.exe manage.py runserver 0.0.0.0:8001"

echo Iniciando Bot de Telegram...
start "Telegram Bot" cmd /c "cd /d C:\Users\dreat\OneDrive\Escritorio\DEMO\pillar_1_inventario-main && laZona\Scripts\python.exe manage.py run_telegram_bot"

echo Esperando que los servidores inicien...
timeout /t 10 >nul

echo Iniciando Ngrok para Inventario (puerto 8000)...
start "Ngrok Inventario" cmd /k "cd /d C:\Users\dreat\OneDrive\Escritorio\DEMO\pillar_1_inventario-main && ngrok http 8000"

echo Iniciando Ngrok para Dreacht Hub (puerto 8001)...
start "Ngrok Dreacht" cmd /k "cd /d C:\Users\dreat\OneDrive\Escritorio\DEMO\pillar_1_inventario-main && ngrok http 8001"

echo.
echo ===========================================
echo    SERVICIOS INICIADOS
echo ===========================================
echo.
echo [SERVIDORES LOCALES]
echo - Inventario:  http://127.0.0.1:8000
echo - Dreacht Hub: http://127.0.0.1:8001
echo - Bot Telegram: Activo (ventana separada)
echo.
echo [INSTRUCCIONES NGROK]
echo 1. En 'Ngrok Inventario' busca la línea que dice:
echo    'Forwarding https://xxx.ngrok-free.dev -^> http://localhost:8000'
echo.
echo 2. En 'Ngrok Dreacht' busca la línea que dice:
echo    'Forwarding https://yyy.ngrok-free.dev -^> http://localhost:8001'
echo.
echo [NOTA]
echo - Las URLs de ngrok son aleatorias
echo - Se generan nuevas URLs cada vez que inicias los túneles
echo - Cierra todas las ventanas para detener los servicios
echo - El bot de Telegram está corriendo en una ventana separada
echo ===========================================