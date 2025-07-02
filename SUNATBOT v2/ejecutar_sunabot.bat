@echo off
title SUNABOT v2 - Servidor
echo ===============================================
echo            EJECUTANDO SUNABOT v2
echo ===============================================
echo.

REM Verificar directorio
if not exist "app.py" (
    echo [ERROR] Ejecuta este script desde el directorio del proyecto
    pause
    exit /b 1
)

REM Activar entorno virtual
if exist "venv\Scripts\activate.bat" (
    echo Activando entorno virtual...
    call venv\Scripts\activate.bat
    echo [OK] Entorno virtual activado
) else (
    echo [ADVERTENCIA] No se encontro entorno virtual
    echo Usando Python del sistema...
)

echo.
echo Iniciando SUNABOT...
echo Abre http://localhost:5000 en tu navegador
echo Presiona Ctrl+C para detener el servidor
echo.
echo ===============================================

python app.py

echo.
echo SUNABOT detenido.
pause
