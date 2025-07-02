# 🤖 SCRIPT DE INSTALACIÓN AUTOMÁTICA - SUNABOT v2
# Ejecuta este script en PowerShell como Administrador

Write-Host "=== INSTALADOR AUTOMÁTICO SUNABOT v2 ===" -ForegroundColor Cyan
Write-Host ""

# Verificar si estamos en el directorio correcto
$currentPath = Get-Location
Write-Host "Directorio actual: $currentPath" -ForegroundColor Yellow

if (-not (Test-Path "app.py")) {
    Write-Host "❌ ERROR: No se encuentra app.py en el directorio actual" -ForegroundColor Red
    Write-Host "Asegúrate de ejecutar este script desde: c:\proyecto\Sunabot\SUNATBOT v2" -ForegroundColor Yellow
    pause
    exit 1
}

Write-Host "✅ Archivo app.py encontrado" -ForegroundColor Green

# Verificar Python
Write-Host ""
Write-Host "🔍 Verificando instalación de Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>$null
    if ($pythonVersion) {
        Write-Host "✅ Python encontrado: $pythonVersion" -ForegroundColor Green
    } else {
        throw "Python no encontrado"
    }
} catch {
    Write-Host "❌ Python no está instalado o no está en PATH" -ForegroundColor Red
    Write-Host "Por favor, instala Python desde: https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "IMPORTANTE: Marca 'Add Python to PATH' durante la instalación" -ForegroundColor Yellow
    pause
    exit 1
}

# Verificar pip
Write-Host ""
Write-Host "🔍 Verificando pip..." -ForegroundColor Yellow
try {
    $pipVersion = pip --version 2>$null
    if ($pipVersion) {
        Write-Host "✅ pip encontrado: $pipVersion" -ForegroundColor Green
    } else {
        throw "pip no encontrado"
    }
} catch {
    Write-Host "❌ pip no está disponible" -ForegroundColor Red
    pause
    exit 1
}

# Crear entorno virtual
Write-Host ""
Write-Host "🏗️ Creando entorno virtual..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "ℹ️ Entorno virtual ya existe, usando el existente" -ForegroundColor Blue
} else {
    python -m venv venv
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Entorno virtual creado" -ForegroundColor Green
    } else {
        Write-Host "❌ Error al crear entorno virtual" -ForegroundColor Red
        pause
        exit 1
    }
}

# Activar entorno virtual
Write-Host ""
Write-Host "🔄 Activando entorno virtual..." -ForegroundColor Yellow
try {
    & ".\venv\Scripts\Activate.ps1"
    Write-Host "✅ Entorno virtual activado" -ForegroundColor Green
} catch {
    Write-Host "❌ Error al activar entorno virtual" -ForegroundColor Red
    Write-Host "Ejecuta manualmente: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor Yellow
    pause
    exit 1
}

# Actualizar pip
Write-Host ""
Write-Host "⬆️ Actualizando pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ pip actualizado" -ForegroundColor Green
} else {
    Write-Host "⚠️ Advertencia: No se pudo actualizar pip" -ForegroundColor Yellow
}

# Instalar dependencias
Write-Host ""
Write-Host "📦 Instalando dependencias..." -ForegroundColor Yellow
Write-Host "Esto puede tardar varios minutos..." -ForegroundColor Blue

pip install -r requirements.txt
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Dependencias instaladas correctamente" -ForegroundColor Green
} else {
    Write-Host "❌ Error al instalar dependencias" -ForegroundColor Red
    Write-Host "Intenta ejecutar manualmente: pip install -r requirements.txt" -ForegroundColor Yellow
    pause
    exit 1
}

# Verificar modelo
Write-Host ""
Write-Host "🤖 Verificando modelo de IA..." -ForegroundColor Yellow
$modelPath = "IA\mistral-7b-instruct-v0.1.Q2_K.gguf"

if (Test-Path $modelPath) {
    $modelSize = (Get-Item $modelPath).Length / 1GB
    Write-Host "✅ Modelo encontrado (${modelSize:N2} GB)" -ForegroundColor Green
} else {
    Write-Host "❌ MODELO NO ENCONTRADO" -ForegroundColor Red
    Write-Host "DEBES DESCARGAR EL MODELO:" -ForegroundColor Yellow
    Write-Host "1. Ve a: https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF/blob/main/mistral-7b-instruct-v0.1.Q2_K.gguf" -ForegroundColor White
    Write-Host "2. Descarga el archivo (2.87 GB)" -ForegroundColor White
    Write-Host "3. Guárdalo en: $currentPath\IA\" -ForegroundColor White
    Write-Host "4. Renómbralo exactamente a: mistral-7b-instruct-v0.1.Q2_K.gguf" -ForegroundColor White
    Write-Host ""
    $continue = Read-Host "¿Ya descargaste el modelo? (s/n)"
    if ($continue.ToLower() -ne "s") {
        Write-Host "Vuelve a ejecutar este script después de descargar el modelo" -ForegroundColor Yellow
        pause
        exit 1
    }
}

# Verificar estructura de módulos
Write-Host ""
Write-Host "📁 Verificando estructura de módulos..." -ForegroundColor Yellow

$requiredDirs = @("chains", "models", "runnables", "static", "templates")
$allDirsExist = $true

foreach ($dir in $requiredDirs) {
    if (Test-Path $dir) {
        Write-Host "✅ Directorio $dir encontrado" -ForegroundColor Green
    } else {
        Write-Host "❌ Directorio $dir NO encontrado" -ForegroundColor Red
        $allDirsExist = $false
    }
}

if (-not $allDirsExist) {
    Write-Host "❌ Faltan directorios necesarios" -ForegroundColor Red
    pause
    exit 1
}

# Todo listo
Write-Host ""
Write-Host "🎉 ¡INSTALACIÓN COMPLETA!" -ForegroundColor Green
Write-Host ""
Write-Host "Para ejecutar SUNABOT:" -ForegroundColor Cyan
Write-Host "1. python app.py" -ForegroundColor White
Write-Host "2. Abre http://localhost:5000 en tu navegador" -ForegroundColor White
Write-Host ""
Write-Host "Para sesiones futuras:" -ForegroundColor Cyan
Write-Host "1. cd '$currentPath'" -ForegroundColor White
Write-Host "2. .\venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "3. python app.py" -ForegroundColor White
Write-Host ""

$runNow = Read-Host "¿Quieres ejecutar SUNABOT ahora? (s/n)"
if ($runNow.ToLower() -eq "s") {
    Write-Host ""
    Write-Host "🚀 Iniciando SUNABOT..." -ForegroundColor Green
    Write-Host "Presiona Ctrl+C para detener el servidor" -ForegroundColor Yellow
    Write-Host ""
    python app.py
} else {
    Write-Host "✅ Instalación completada. Ejecuta 'python app.py' cuando estés listo." -ForegroundColor Green
}

Write-Host ""
Write-Host "Presiona cualquier tecla para salir..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
