@echo off
title Sistema de gestion de inventario
cls

REM ==== Configuración inicial ====
cd /d "%~dp0"

REM Activar entorno virtual
call laZona\Scripts\activate

REM ==== Crear backup de la base de datos ====
if not exist "backups" mkdir "backups"
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set "datetime=%%I"
set "fecha=%datetime:~0,4%-%datetime:~4,2%-%datetime:~6,2%"
set "hora=%datetime:~8,2%-%datetime:~10,2%"
copy "db.sqlite3" "backups\backup_%fecha%_%hora%.db" >nul

REM ==== Ejecutar migraciones ====
python manage.py makemigrations
python manage.py migrate

REM ==== Crear superusuario por defecto ====
python crear_superusuario.py

REM ==== Iniciar servidor de PILLAR 1 (Inventario) en puerto 8000 ====
start "Pillar_1_Inventario" cmd /k "@echo Iniciando servidor de Inventario en http://127.0.0.1:8000 && python manage.py runserver 0.0.0.0:8000"

REM ==== Iniciar servidor de DREACHT HUB en puerto 8001 ====
start "Dreacht_Hub" cmd /k "@echo Iniciando servidor de Dreacht Hub en http://127.0.0.1:8001 && "%~dp0..\dreacht_hub_web-master\dreacht_venv\Scripts\python.exe" "%~dp0..\dreacht_hub_web-master\manage.py" runserver 0.0.0.0:8001"

REM ==== Esperar 10 segundos para que los servidores carguen ====
timeout 10 > nul

REM ==== Iniciar ngrok para Inventario (puerto 8000) ====
start "Ngrok Inventario" cmd /k "@echo Iniciando ngrok para Inventario (puerto 8000) && ngrok http 8000"

REM ==== Iniciar ngrok para Dreacht Hub (puerto 8001) ====
start "Ngrok Dreacht Hub" cmd /k "@echo Iniciando ngrok para Dreacht Hub (puerto 8001) && ngrok http 8001"

REM ==== Iniciar bot de Telegram ====
start "Bot de Telegram" cmd /k "python manage.py run_telegram_bot"

REM ==== Mostrar instrucciones ===
cls
echo ======================================================
echo    SISTEMA INICIADO CORRECTAMENTE
echo ======================================================
echo.
echo [SERVIDORES LOCALES]
echo - Inventario:    http://127.0.0.1:8000
echo - Dreacht Hub:   http://127.0.0.1:8001
echo.
echo [ACCESO DESDE INTERNET]
echo - Espere a que aparezcan las URLs de ngrok en las ventanas
echo  correspondientes (pueden tardar unos segundos).
echo.
echo [NOTA]
echo - Las URLs de ngrok cambiarán cada vez que se reinicie.
echo - Para URLs fijas, actualice a un plan de pago de ngrok.
echo ======================================================

REM ==== Abrir navegadores con los servicios locales ====
start "" "http://127.0.0.1:8000"
start "" "http://127.0.0.1:8001"

