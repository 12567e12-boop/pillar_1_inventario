@echo off
setlocal enabledelayedexpansion
title Dreacht Hub - Iniciando...

echo ===================================
echo  INICIANDO DREACHT HUB
echo ===================================
echo.

REM Verificar Python
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python no esta instalado o no esta en el PATH
    pause
    exit /b
)

REM Verificar si el entorno virtual existe, si no, crearlo
if not exist "dreacht_venv" (
    echo Creando entorno virtual...
    python -m venv dreacht_venv
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] No se pudo crear el entorno virtual
        pause
        exit /b
    )
)

echo Activando entorno virtual...
call dreacht_venv\Scripts\activate.bat
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] No se pudo activar el entorno virtual
    pause
    exit /b
)

echo Instalando dependencias...
echo [INFO] Esto puede tomar unos instantes...

:: Intentar instalar normalmente
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo [ADVERTENCIA] Reintentando instalación forzada...
    pip install --force-reinstall -r requirements.txt
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] No se pudieron instalar las dependencias
        echo [SOLUCION] Cierra todos los programas que puedan estar usando Python y vuelve a intentar
        pause
        exit /b
    )
)

echo Aplicando migraciones...
python manage.py makemigrations
python manage.py migrate

echo.
echo ===================================
echo  DREACHT HUB LISTO
echo ===================================
echo.
echo Iniciando servidor de desarrollo...
echo Presiona Ctrl+C para detener el servidor cuando termines.
echo.

title Dreacht Hub - Servidor en ejecucion
start cmd /k "python manage.py runserver 0.0.0.0:8001"

REM Esperar 3 segundos para que el servidor inicie
timeout 3 > nul

echo Iniciando el navegador...
start http://127.0.0.1:8001/

echo Iniciando ngrok...
start cmd /k "ngrok http 8001"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] No se pudo iniciar el servidor
    pause
)

title Dreacht Hub - Detenido
pause