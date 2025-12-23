@echo off
title Iniciar Inventario y Dreacht Hub
cls
REM Cambiar a la ruta base
cd /d "C:\Users\dreat\OneDrive\Escritorio\DEMO"
echo Deteniendo procesos anteriores...
taskkill /F /IM ngrok.exe >nul 2>&1
taskkill /F /IM python.exe >nul 2>&1
echo Iniciando servidor de Inventario...
start "Inventario" cmd /k "cd /d C:\Users\dreat\OneDrive\Escritorio\DEMO\pillar_1_inventario-main && python manage.py runserver 0.0.0.0:8000"
echo Iniciando servidor de Dreacht Hub...
start "Dreacht" cmd /k "cd /d C:\Users\dreat\OneDrive\Escritorio\DEMO\dreacht_hub_web-master && dreacht_venv\Scripts\python.exe manage.py runserver 0.0.0.0:8001"
timeout 5 >nul
echo Iniciando túneles ngrok...
start "Ngrok Inventario" cmd /k "cd /d C:\Users\dreat\OneDrive\Escritorio\DEMO\pillar_1_inventario-main && ngrok start inventario --config=ngrok.yml"
start "Ngrok Dreacht" cmd /k "cd /d C:\Users\dreat\OneDrive\Escritorio\DEMO\pillar_1_inventario-main && ngrok start dreacht-hub --config=ngrok.yml"
echo ===========================================
echo    AMBOS SERVICIOS INICIADOS
echo ===========================================
echo.
echo [SERVIDORES LOCALES]
echo - Inventario:  http://127.0.0.1:8000
echo - Dreacht Hub: http://127.0.0.1:8001
echo.
echo [ACCESO EXTERNO]
echo 1. En 'Ngrok Inventario' busca la línea que dice:
echo    'Forwarding https://xxx.ngrok-free.dev -> http://localhost:8000'
echo.
echo 2. En 'Ngrok Dreacht' busca la línea que dice:
echo    'Forwarding https://yyy.ngrok-free.dev -> http://localhost:8001'
echo.
echo [RUTAS]
echo - Base: C:\Users\dreat\OneDrive\Escritorio\DEMO
echo - Inventario: \pillar_1_inventario-main\
echo - Dreacht Hub: \dreacht_hub_web-master\
echo.
echo [IMPORTANTE]
echo - Cada servicio usa su propio token de ngrok
echo - Las URLs cambian al reiniciar los túneles
echo ===========================================