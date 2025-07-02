# 🤖 GUÍA COMPLETA DE INSTALACIÓN - SUNABOT v2

Esta guía te llevará paso a paso para ejecutar SUNABOT desde cero en una máquina nueva con Windows.

## 📋 REQUISITOS PREVIOS

### 1. Verificar si Python está instalado
Abre **PowerShell** como administrador y ejecuta:
```powershell
python --version
```

**Si NO tienes Python instalado:**
1. Ve a https://www.python.org/downloads/
2. Descarga Python 3.9 o superior (recomendado: Python 3.11)
3. **IMPORTANTE**: Durante la instalación, marca la casilla "Add Python to PATH"
4. Instala con configuración por defecto

### 2. Verificar pip (administrador de paquetes)
```powershell
pip --version
```

Si no funciona, reinstala Python marcando "Add to PATH".

## 🚀 INSTALACIÓN PASO A PASO

### PASO 1: Navegar al directorio del proyecto
```powershell
cd "c:\proyecto\Sunabot\SUNATBOT v2"
```

### PASO 2: Crear entorno virtual (RECOMENDADO)
```powershell
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
.\venv\Scripts\Activate.ps1
```

**Si obtienes error de políticas de ejecución:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
Luego vuelve a intentar activar el entorno.

### PASO 3: Actualizar pip
```powershell
python -m pip install --upgrade pip
```

### PASO 4: Instalar dependencias
```powershell
pip install -r requirements.txt
```

**Si hay errores con llama-cpp-python:**
```powershell
# Instalar herramientas de compilación si es necesario
pip install --upgrade setuptools wheel
pip install llama-cpp-python --no-cache-dir
```

### PASO 5: Descargar el modelo de IA
1. Ve a: https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF/blob/main/mistral-7b-instruct-v0.1.Q2_K.gguf
2. Haz clic en "Download" (archivo ~2.87 GB)
3. Mueve el archivo descargado a la carpeta `IA/`
4. **IMPORTANTE**: Renombra el archivo a exactamente: `mistral-7b-instruct-v0.1.Q2_K.gguf`

### PASO 6: Verificar estructura de archivos
Tu estructura debe verse así:
```
SUNATBOT v2/
├── app.py
├── requirements.txt
├── IA/
│   └── mistral-7b-instruct-v0.1.Q2_K.gguf  ← MODELO AQUÍ
├── chains/
├── models/
├── runnables/
├── static/
└── templates/
```

## ▶️ EJECUTAR LA APLICACIÓN

### Método 1: Ejecución directa
```powershell
python app.py
```

### Método 2: Con Flask (alternativo)
```powershell
set FLASK_APP=app.py
set FLASK_ENV=development
flask run --host=0.0.0.0 --port=5000
```

## 🌐 ACCEDER A LA APLICACIÓN

Una vez que veas el mensaje:
```
* Running on all addresses (0.0.0.0)
* Running on http://127.0.0.1:5000
* Running on http://[IP_LOCAL]:5000
```

Abre tu navegador y ve a:
- **Local**: http://localhost:5000
- **Red local**: http://127.0.0.1:5000

## ❌ SOLUCIÓN DE PROBLEMAS COMUNES

### Error: "No module named 'chains'"
Asegúrate de estar en el directorio correcto:
```powershell
cd "c:\proyecto\Sunabot\SUNATBOT v2"
python app.py
```

### Error: "Model file not found"
Verifica que el modelo esté en la ruta correcta:
```
IA/mistral-7b-instruct-v0.1.Q2_K.gguf
```

### Error de memoria/rendimiento lento
El modelo requiere al menos 4GB de RAM libre. Si tienes problemas:
1. Cierra otras aplicaciones
2. Considera usar un modelo más pequeño
3. Verifica que tu sistema tenga suficiente RAM

### Error con llama-cpp-python en Windows
```powershell
# Instalar Microsoft C++ Build Tools si es necesario
pip install --upgrade pip setuptools wheel
pip install llama-cpp-python --force-reinstall --no-cache-dir
```

### Puerto 5000 ocupado
Si el puerto está en uso:
```powershell
# Cambiar puerto en app.py línea final:
# app.run(debug=False, host="0.0.0.0", port=5001)
```

## 🔧 COMANDOS ÚTILES

### Desactivar entorno virtual
```powershell
deactivate
```

### Reactivar entorno virtual (sesiones futuras)
```powershell
cd "c:\proyecto\Sunabot\SUNATBOT v2"
.\venv\Scripts\Activate.ps1
python app.py
```

### Verificar dependencias instaladas
```powershell
pip list
```

### Actualizar dependencias
```powershell
pip install --upgrade -r requirements.txt
```

## 📝 NOTAS IMPORTANTES

1. **Entorno Virtual**: Siempre activa el entorno virtual antes de ejecutar
2. **Modelo de IA**: El archivo debe llamarse exactamente `mistral-7b-instruct-v0.1.Q2_K.gguf`
3. **Primera ejecución**: La primera vez puede tardar en cargar el modelo
4. **Rendimiento**: El modelo funcionará mejor con más RAM disponible
5. **Red**: La aplicación será accesible desde otros dispositivos en tu red local

## ✅ VERIFICACIÓN FINAL

Si todo está correcto, deberías ver:
```
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
```

Y al abrir http://localhost:5000 verás la interfaz de SUNABOT.

---

## 🆘 ¿NECESITAS AYUDA?

Si sigues teniendo problemas:
1. Verifica que Python esté en PATH
2. Asegúrate de estar en el directorio correcto
3. Confirma que el modelo esté descargado y renombrado correctamente
4. Verifica que todas las dependencias estén instaladas

¡Tu SUNABOT estará listo para responder consultas de SUNAT! 🎉
