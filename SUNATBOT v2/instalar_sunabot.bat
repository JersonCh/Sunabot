@echo off
echo ===============================================
echo    INSTALADOR SUNABOT v2 - Metodo Alternativo
echo ===============================================
echo.

REM Verificar si estamos en el directorio correcto
if not exist "app.py" (
    echo [ERROR] No se encuentra app.py en el directorio actual
    echo Asegurate de ejecutar este script desde: c:\proyecto\Sunabot\SUNATBOT v2
    pause
    exit /b 1
)

echo [OK] Archivo app.py encontrado
echo.

REM Verificar Python
echo Verificando Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python no esta instalado o no esta en PATH
    echo Instala Python desde: https://www.python.org/downloads/
    echo IMPORTANTE: Marca 'Add Python to PATH' durante la instalacion
    pause
    exit /b 1
)

echo [OK] Python encontrado
echo.

REM Verificar pip
echo Verificando pip...
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] pip no esta disponible
    pause
    exit /b 1
)

echo [OK] pip encontrado
echo.

REM Crear entorno virtual
echo Creando entorno virtual...
if exist "venv" (
    echo [INFO] Entorno virtual ya existe
) else (
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] No se pudo crear el entorno virtual
        pause
        exit /b 1
    )
    echo [OK] Entorno virtual creado
)
echo.

REM Activar entorno virtual
echo Activando entorno virtual...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [ERROR] No se pudo activar el entorno virtual
    pause
    exit /b 1
)

echo [OK] Entorno virtual activado
echo.

REM Actualizar pip
echo Actualizando pip...
python -m pip install --upgrade pip --quiet
echo [OK] pip actualizado
echo.

REM Instalar dependencias
echo Instalando dependencias (esto puede tardar varios minutos)...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] No se pudieron instalar las dependencias
    echo Intenta ejecutar manualmente: pip install -r requirements.txt
    pause
    exit /b 1
)

echo [OK] Dependencias instaladas
echo.

REM Verificar modelo
echo Verificando modelo de IA...
if exist "IA\mistral-7b-instruct-v0.1.Q2_K.gguf" (
    echo [OK] Modelo encontrado
) else (
    echo [ERROR] MODELO NO ENCONTRADO
    echo.
    echo DEBES DESCARGAR EL MODELO:
    echo 1. Ve a: https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF/blob/main/mistral-7b-instruct-v0.1.Q2_K.gguf
    echo 2. Descarga el archivo (2.87 GB^)
    echo 3. Guardalo en: %CD%\IA\
    echo 4. Renombralo exactamente a: mistral-7b-instruct-v0.1.Q2_K.gguf
    echo.
    set /p continue="Ya descargaste el modelo? (s/n): "
    if /i "%continue%" neq "s" (
        echo Vuelve a ejecutar este script despues de descargar el modelo
        pause
        exit /b 1
    )
)

echo.
echo ============================================
echo        INSTALACION COMPLETA!
echo ============================================
echo.
echo Para ejecutar SUNABOT:
echo 1. python app.py
echo 2. Abre http://localhost:5000 en tu navegador
echo.
echo Para sesiones futuras:
echo 1. cd "%CD%"
echo 2. venv\Scripts\activate.bat
echo 3. python app.py
echo.

set /p runnow="Quieres ejecutar SUNABOT ahora? (s/n): "
if /i "%runnow%" equ "s" (
    echo.
    echo Iniciando SUNABOT...
    echo Presiona Ctrl+C para detener el servidor
    echo.
    python app.py
) else (
    echo.
    echo Instalacion completada. Ejecuta 'python app.py' cuando estes listo.
)

echo.
pause
