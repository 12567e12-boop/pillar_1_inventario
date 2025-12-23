@echo off
title Dreacht Tunnels (LocalTunnel)
cls

echo ===================================================
echo    INICIANDO TUNELES PUBLICOS (LOCALTUNNEL)
echo ===================================================
echo.
echo NOTA: La primera vez que entres a la URL, localtunnel
echo te pedira una ip publica
echo.

echo Iniciando Tunel para Inventario (Puerto 8000)...
start "LT Inventario (8000)" cmd /k "lt --port 8000"

echo Iniciando Tunel para Dreacht Hub (Puerto 8001)...
start "LT Dreacht Hub (8001)" cmd /k "lt --port 8001"

echo.
echo ===================================================
echo    TUNELES INICIADOS
echo ===================================================
echo 1. Revisa las ventanas nuevas para ver las URLs
echo    (Ejemplo: https://heavy-zebra-45.loca.lt)
echo 2. NO Cierres esta ventana ni las de los tuneles
echo.
pause
