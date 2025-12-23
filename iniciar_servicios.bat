@echo off
title Iniciar Servicios con Nginx
cls

echo Deteniendo procesos...
taskkill /f /im nginx.exe >nul 2>&1
taskkill /f /im ngrok.exe >nul 2>&1
taskkill /f /im python.exe >nul 2>&1

echo Iniciando Nginx...
rem Se usa -c para especificar la ruta de nuestro archivo de configuracion
rem Se ejecuta Nginx directamente con la ruta completa y la configuracion especifica
start "Nginx" "C:\Program Files (x86)\nginx-1.29.4\nginx-1.29.4\nginx.exe" -c "c:\Users\dreat\OneDrive\Escritorio\DEMO\nginx.conf" -p "C:\Program Files (x86)\nginx-1.29.4\nginx-1.29.4"

echo Iniciando servidor de Dreacht Hub (Puerto 8001)...
start "Dreacht" cmd /c "cd /d C:\Users\dreat\OneDrive\Escritorio\DEMO\dreacht_hub_web-master && dreacht_venv\Scripts\python.exe manage.py runserver 0.0.0.0:8001"

echo Iniciando servidor de Inventario (Puerto 8000)...
start "Inventario" cmd /c "cd /d C:\Users\dreat\OneDrive\Escritorio\DEMO\pillar_1_inventario-main && laZona\Scripts\python.exe manage.py runserver 0.0.0.0:8000"

echo Iniciando Bot de Telegram...
start "Telegram Bot" cmd /c "cd /d C:\Users\dreat\OneDrive\Escritorio\DEMO\pillar_1_inventario-main && laZona\Scripts\python.exe manage.py run_telegram_bot"

timeout 10 >nul

echo Iniciando Ngrok...
start "Ngrok" cmd /k "ngrok http 8888"

echo.
echo ===========================================
echo    SERVICIOS INICIADOS
echo ===========================================
echo.
echo [SERVIDORES LOCALES]
echo - Dreacht Hub: http://127.0.0.1:8000
echo - Inventario:  http://127.0.0.1:8001
echo.
echo [ACCESO POR NGROK]
echo 1. Busca la URL que empieza con 'https://' en la ventana de Ngrok
echo 2. Usa las siguientes rutas:
echo    - URL/hub/ para Dreacht Hub
echo    - URL/inventario/ para Inventario
echo.
echo [DETENER TODO]
echo Cierra la ventana de Ngrok o ejecuta 'taskkill /f /im nginx.exe'
echo ===========================================