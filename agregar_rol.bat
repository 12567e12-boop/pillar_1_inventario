@echo off
title Agregar Campo ROL a Empleados
cls

cd /d "%~dp0"

echo ============================================================
echo   AGREGAR CAMPO ROL A EMPLEADOS
echo ============================================================
echo.

python agregar_rol_empleados.py

echo.
pause
