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

REM ==== Iniciar servidor en una nueva ventana ====
start cmd /k "python manage.py runserver 0.0.0.0:8000"

REM ==== Esperar 3 segundos para que el servidor cargue ====
timeout 3 > nul

REM ==== Abrir navegador ====
start "" "http://127.0.0.1:8002"

REM ==== Iniciar ngrok en otra ventana ====
start cmd /k "ngrok http 8002"

REM ==== Iniciar bot de Telegram en otra ventana ====
start cmd /k "python manage.py run_telegram_bot"

