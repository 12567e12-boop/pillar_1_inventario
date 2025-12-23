@echo off
title Iniciar Proyecto de Inventario
cls

echo =================================================================
echo =      DETENIENDO SERVICIOS ANTERIORES (si existen)...         =
echo =================================================================
taskkill /f /im ngrok.exe >nul 2>&1
taskkill /f /im python.exe >nul 2>&1
echo.

echo =================================================================
echo =              INICIANDO SERVIDOR DJANGO (Inventario)           =
echo =================================================================
echo.
echo    - Directorio: C:\Users\dreat\OneDrive\Escritorio\DEMO\pillar_1_inventario-main
echo    - Puerto: 8000
echo.
start "Django Inventario" cmd /c "cd /d C:\Users\dreat\OneDrive\Escritorio\DEMO\pillar_1_inventario-main && python manage.py runserver 0.0.0.0:8000"

echo Esperando 10 segundos para que el servidor se inicie correctamente...
timeout /t 10 >nul
echo.

echo =================================================================
echo =                     INICIANDO NGROK                           =
echo =================================================================
echo.
echo    - Configuracion: c:\Users\dreat\OneDrive\Escritorio\DEMO\ngrok.yml
echo    - Tunel: inventario (http://localhost:8000)
echo.
start "Ngrok" cmd /k "ngrok start --config c:\Users\dreat\OneDrive\Escritorio\DEMO\ngrok.yml inventario"

echo.
echo =================================================================
echo =                       PROCESO FINALIZADO                        =
echo =================================================================
echo.
echo Se han abierto dos ventanas:
echo 1. Una para el servidor de Django (Inventario).
echo 2. Una para Ngrok.
echo.
echo En la ventana de Ngrok, busca la linea "Forwarding" para encontrar tu URL publica.
echo.
echo Para detener todo, simplemente cierra ambas ventanas.
echo.
pause
