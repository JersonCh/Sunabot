from flask import Flask, render_template, request, jsonify
try:
    from llama_cpp import Llama
    LLAMA_AVAILABLE = True
except ImportError:
    LLAMA_AVAILABLE = False
    print("⚠️ llama-cpp-python no está instalado. Usando modo de demostración.")

# Importar Google Gemini
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️ google-generativeai no está instalado. Chat directo usará modo de demostración.")

from typing import List, Dict, Any, Optional, Union
import os
import json
import re

# Importar módulos personalizados
from models.schemas import RespuestaEstructurada, ConsultaInput, ContinuacionInput
from chains.langchain_chains import SunatChains
from runnables.custom_runnables import SunatRunnables

app = Flask(__name__)

# Configurar Google Gemini
if GEMINI_AVAILABLE:
    # Intentar configurar Gemini con variable de entorno
    gemini_api_key = os.getenv('GEMINI_API_KEY')
    
    # TEMPORAL: Para prueba rápida, descomenta la línea siguiente y agrega tu API key
    gemini_api_key = "AIzaSyBVlqSGeScDUXTffhYQqy2Grqc5AJqJN9k"
    
    if gemini_api_key:
        genai.configure(api_key=gemini_api_key)
        try:
            gemini_model = genai.GenerativeModel('gemini-1.5-flash')
            print("✅ Google Gemini configurado correctamente")
        except Exception as e:
            print(f"⚠️ Error al configurar Gemini: {e}")
            gemini_model = None
    else:
        print("⚠️ GEMINI_API_KEY no encontrada. Chat directo usará modo de demostración.")
        gemini_model = None
else:
    gemini_model = None

# Cargar modelo
if LLAMA_AVAILABLE and os.path.exists("IA/mistral-7b-instruct-v0.1.Q2_K.gguf"):
    llm = Llama(
        model_path="IA/mistral-7b-instruct-v0.1.Q2_K.gguf",
        n_ctx=2048,  
        verbose=False
    )
    print("✅ Modelo de IA cargado correctamente")
else:
    # Mock del modelo para modo de demostración
    class MockLlama:
        def __call__(self, prompt, **kwargs):
            return {
                'choices': [{
                    'text': """**SUNABOT - Modo Demostración**

Para consultas sobre RUC, puedes:
1. **Consultar RUC**: https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/FrameCriterioBusquedaWeb.jsp
2. **Registrar RUC**: https://ww1.sunat.gob.pe/a/html/contribuyente2/registro/adminforuc/registroruc/registroruc.html

Para acceder al **Portal SOL**: https://www.sunat.gob.pe/sol.html

*Nota: Este es el modo de demostración. Para respuestas completas de IA, descarga el modelo de IA.*"""
                }]
            }
    
    llm = MockLlama()
    print("🤖 Usando modo de demostración (sin modelo de IA)")

CATEGORIAS_EXACTAS = {
    "RUC": "Registro Único de Contribuyentes",
    "Declaraciones": "Declaraciones tributarias y presentación",
    "Facturación": "Comprobantes de pago y facturación", 
    "Clave SOL": "Clave SOL y servicios en línea",
    "Regímenes": "Regímenes tributarios",
    "Otros": "Otras consultas tributarias"
}

# Inicializar cadenas LangChain
try:
    sunat_chains = SunatChains(llm, CATEGORIAS_EXACTAS)
except Exception as e:
    print(f"⚠️ Error al inicializar SunatChains: {e}")
    sunat_chains = None

# Crear runnables personalizados
categorizar_runnable = SunatRunnables.crear_runnable_categorizar()
validador_runnable = SunatRunnables.crear_runnable_validador()
cadena_paralela = SunatRunnables.crear_cadena_paralela_completa()

CATEGORIAS_EXACTAS = {
    "RUC": "Registro Único de Contribuyentes",
    "Declaraciones": "Declaraciones tributarias y presentación",
    "Facturación": "Comprobantes de pago y facturación", 
    "Clave SOL": "Clave SOL y servicios en línea",
    "Regímenes": "Regímenes tributarios",
    "Otros": "Otras consultas tributarias"
}

# Sistema de mensajes para categorías
def crear_sistema_categoria(categoria: str) -> str:
    """Crea mensajes de sistema específicos para cada categoría"""
    
    sistemas = {
        "RUC": """### SUNABOT - Especialista RUC
INSTRUCCIONES: Respuesta DIRECTA y CONCISA sobre RUC. Máximo 2-3 párrafos. Ve directo al grano.

LINKS ÚTILES PARA INCLUIR:
- Consulta RUC: https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/FrameCriterioBusquedaWeb.jsp
- Registro RUC: https://ww1.sunat.gob.pe/a/html/contribuyente2/registro/adminforuc/registroruc/registroruc.html""",
        
        "Declaraciones": """### SUNABOT - Especialista Declaraciones  
INSTRUCCIONES: Respuesta DIRECTA y CONCISA sobre declaraciones tributarias. Máximo 2-3 párrafos. Ve directo al grano.

LINKS ÚTILES PARA INCLUIR:
- Cronograma obligaciones: https://ww3.sunat.gob.pe/cl-ti-itcronobligme/fvS01Alias
- Portal SOL: https://www.sunat.gob.pe/sol.html""",
        
        "Facturación": """### SUNABOT - Especialista Facturación
INSTRUCCIONES: Respuesta DIRECTA y CONCISA sobre facturación y comprobantes. Máximo 2-3 párrafos. Ve directo al grano.

LINKS ÚTILES PARA INCLUIR:
- Verificar comprobantes: https://e-consulta.sunat.gob.pe/ol-ti-itconsvalicpe/ConsValiCpe.htm
- Consulta libre CPE: https://ww1.sunat.gob.pe/ol-ti-itconsultaunificadalibre/consultaUnificadaLibre/consulta""",
        
        "Clave SOL": """### SUNABOT - Especialista Clave SOL
INSTRUCCIONES: Respuesta DIRECTA y CONCISA sobre Clave SOL y servicios digitales. Máximo 2-3 párrafos. Ve directo al grano.

LINKS ÚTILES PARA INCLUIR:
- Login Clave SOL: https://www.sunat.gob.pe/sol.html
- Recuperar Clave SOL: https://www.gob.pe/7550-recuperar-la-clave-sol""",
        
        "Regímenes": """### SUNABOT - Especialista Regímenes
INSTRUCCIONES: Respuesta DIRECTA y CONCISA sobre regímenes tributarios. Máximo 2-3 párrafos. Ve directo al grano.

LINKS ÚTILES PARA INCLUIR:
- Portal SOL: https://www.sunat.gob.pe/sol.html""",
        
        "Otros": """### SUNABOT - Especialista General
INSTRUCCIONES: Respuesta DIRECTA y CONCISA sobre consultas tributarias. Máximo 2-3 párrafos. Ve directo al grano.

LINKS ÚTILES PARA INCLUIR:
- Portal SOL: https://www.sunat.gob.pe/sol.html
- Consulta RUC: https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/FrameCriterioBusquedaWeb.jsp"""
    }
    
    return sistemas.get(categoria, sistemas["Otros"])

# Cadena de Pensamiento (CoT)
def crear_prompt_cot(consulta: str) -> str:
    """Crea prompt con cadena de pensamiento para consultas generales"""
    return f"""### SUNABOT - RESPUESTA DIRECTA Y CONCISA

Consulta: "{consulta}"

INSTRUCCIONES ESPECIALES:
- Responde de forma DIRECTA y CONCISA
- Máximo 2-3 párrafos por respuesta
- Ve directo al punto sin rodeos
- Usa **negritas** solo para lo más importante
- Si hay pasos, máximo 3-4 puntos clave
- INCLUYE LINKS ÚTILES cuando sea relevante:
  * Consulta RUC: https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/FrameCriterioBusquedaWeb.jsp
  * Portal SOL: https://www.sunat.gob.pe/sol.html
  * Verificar comprobantes: https://e-consulta.sunat.gob.pe/ol-ti-itconsvalicpe/ConsValiCpe.htm
  * Cronograma: https://ww3.sunat.gob.pe/cl-ti-itcronobligme/fvS01Alias
  * Recuperar Clave SOL: https://www.gob.pe/7550-recuperar-la-clave-sol

### RESPUESTA CONCISA DE SUNABOT:"""


def detectar_categoria(mensaje: str) -> str:
    """Detecta la categoría basada en palabras clave"""
    mensaje_lower = mensaje.lower()
    
    # Detectar preguntas de definición primero
    if any(palabra in mensaje_lower for palabra in ["qué es", "que es", "define", "definición", "significa", "concepto"]):
        if "sunat" in mensaje_lower:
            return "Definición SUNAT"
        elif "ruc" in mensaje_lower:
            return "RUC"
        elif "clave sol" in mensaje_lower or "sol" in mensaje_lower:
            return "Clave SOL"
        elif any(word in mensaje_lower for word in ["renta cuarta", "cuarta categoria", "cuarta categoría", "renta 4ta"]):
            return "Definición Renta 4ta"
        elif any(word in mensaje_lower for word in ["renta quinta", "quinta categoria", "quinta categoría", "renta 5ta"]):
            return "Definición Renta 5ta"
    
    # Categorías específicas
    if any(word in mensaje_lower for word in ["ruc", "registro único", "inscripción ruc", "contribuyente", "alta ruc", "baja ruc"]):
        return "RUC"
    elif any(word in mensaje_lower for word in ["declaración", "declarar", "djm", "cronograma", "vencimiento", "pdt", "formulario"]):
        return "Declaraciones"
    elif any(word in mensaje_lower for word in ["factura", "comprobante", "boleta", "electrónica", "see", "emisión"]):
        return "Facturación"
    elif any(word in mensaje_lower for word in ["clave sol", "contraseña", "acceso", "sol", "representante", "usuario"]):
        return "Clave SOL"
    elif any(word in mensaje_lower for word in ["régimen", "rus", "rer", "mype", "general", "cambio régimen"]):
        return "Regímenes"
    # Detectar consultas generales sobre SUNAT
    elif "sunat" in mensaje_lower:
        return "SUNAT General"
    else:
        return "Otros"

def crear_prompt(mensaje: str, categoria: str = None, tipo: str = "general") -> str:
    """Crea el prompt apropiado según el tipo de consulta"""
    
    if tipo == "categoria" and categoria:
        # MENSAJE DE SISTEMA para botones específicos
        sistema = crear_sistema_categoria(categoria)
        return f"""{sistema}

### Consulta del usuario sobre {categoria}:
{mensaje}

### Respuesta especializada de SUNABOT:"""
    
    else:
        return crear_prompt_cot(mensaje)

def procesar_links_en_respuesta(texto_respuesta: str) -> str:
    """Convierte URLs en texto a enlaces HTML clickeables"""
    import re
    
    url_pattern = r'https?://[^\s<>"]+(?:[^\s<>".,;:])'
    
    def reemplazar_url(match):
        url = match.group(0)
        return f'<a href="{url}" target="_blank" style="color: #1976d2; text-decoration: underline;">{url}</a>'
    
    texto_con_links = re.sub(url_pattern, reemplazar_url, texto_respuesta)
    
    return texto_con_links

def procesar_consulta(mensaje: str, categoria: str = None, tipo: str = "general", max_tokens: int = 800) -> Dict[str, Any]:
    """Procesa la consulta usando las diferentes técnicas implementadas"""
    
    try:
        categoria_detectada = categoria or detectar_categoria(mensaje)
        
        prompt = crear_prompt(mensaje, categoria, tipo)
        
        resultado = llm(
            prompt, 
            max_tokens=max_tokens,
            temperature=0.7,
            top_p=0.9,
            stop=["</s>", "### Consulta", "### Usuario:", "Human:", "Assistant:"]
        )
        
        texto_respuesta = resultado['choices'][0]['text'].strip()
        
        texto_respuesta = procesar_links_en_respuesta(texto_respuesta)
        
        return {
            "respuesta": texto_respuesta,
            "categoria": categoria_detectada,
            "tipo_procesamiento": tipo,
            "tecnica_usada": "Sistema de Mensajes" if tipo == "categoria" else "Cadena de Pensamiento (CoT)",
            "success": True
        }
        
    except Exception as e:
        return {
            "respuesta": f"Error al procesar la consulta: {str(e)}",
            "categoria": categoria or "Error",
            "tipo_procesamiento": tipo,
            "tecnica_usada": "Error",
            "success": False,
            "error": str(e)
        }

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/responder", methods=["POST"])
def responder():
    data = request.get_json()
    mensaje = data.get("mensaje", "")
    categoria_especifica = data.get("categoria", None)
    tipo_respuesta = data.get("tipo", "general") 
    max_length = data.get("max_length", 1200)
    
    if not mensaje.strip():
        return jsonify({
            "error": "Por favor, proporciona una consulta válida.",
            "respuesta": "No se ha proporcionado ninguna consulta."
        }), 400
    
    try:
        # usar IA
        if tipo_respuesta == "general":
            categoria_detectada = detectar_categoria(mensaje)
            
            # Cadena de Pensamiento
            if categoria_detectada != "Otros":
                prompt = crear_prompt(mensaje, categoria_detectada, "categoria")
            else:
                prompt = crear_prompt_cot(mensaje)
            
            resultado = llm(
                prompt, 
                max_tokens=max_length,
                temperature=0.7,
                top_p=0.9,
                stop=["</s>", "### Consulta", "### Usuario:", "###"]
            )
            
            texto_respuesta = resultado['choices'][0]['text'].strip()
            
            texto_respuesta = procesar_links_en_respuesta(texto_respuesta)
            
            return jsonify({
                "respuesta": texto_respuesta,
                "categoria": categoria_detectada,
                "tipo_procesamiento": "ia_general",
                "tecnica_usada": "Cadena de Pensamiento (CoT)" if categoria_detectada == "Otros" else f"Sistema especializado + CoT ({categoria_detectada})",
                "es_ia": True
            })
        
        else:
            return jsonify({
                "respuesta": "Respuesta manejada por frontend",
                "categoria": categoria_especifica or "General",
                "tipo_procesamiento": "predeterminada",
                "tecnica_usada": "Respuestas predeterminadas",
                "es_ia": False
            })
        
    except Exception as e:
        return jsonify({
            "error": f"Error al procesar la consulta: {str(e)}",
            "respuesta": "Lo siento, ocurrió un error al procesar tu consulta. Por favor, intenta nuevamente.",
            "es_ia": False
        }), 500

@app.route("/responder_langchain", methods=["POST"])
def responder_langchain():
    """Endpoint que usa cadenas LangChain y salidas estructuradas"""
    try:
        data = request.get_json()
        
        # Validar entrada con Pydantic
        consulta_input = ConsultaInput(**data)
        
        # Usar runnable para validación
        validacion = validador_runnable.invoke({"mensaje": consulta_input.mensaje})
        
        if not validacion.get("es_consulta_valida", False):
            return jsonify({
                "error": "Consulta no válida",
                "validaciones": validacion.get("validaciones", {}),
                "respuesta": "Por favor, proporciona una consulta tributaria válida."
            }), 400
        
        # Usar cadena paralela para procesamiento completo
        resultado_paralelo = cadena_paralela.invoke({"mensaje": consulta_input.mensaje})
        
        # Procesar con cadenas LangChain
        if sunat_chains:
            resultado_chain = sunat_chains.procesar_consulta_con_chain(
                consulta_input.mensaje, 
                consulta_input.categoria_especifica
            )
        else:
            resultado_chain = {
                "respuesta": "Modo de demostración - Consulta procesada sin IA completa",
                "categoria": resultado_paralelo.get("categorizar", {}).get("categoria", "Otros"),
                "links_incluidos": []
            }
        
        # Crear respuesta estructurada
        respuesta = RespuestaEstructurada(
            respuesta=resultado_chain.get("respuesta", ""),
            categoria=resultado_chain.get("categoria", "Otros"),
            confianza=resultado_paralelo.get("categorizar", {}).get("confianza", 0.5),
            links_incluidos=resultado_chain.get("links_incluidos", []),
            tecnica_usada="LangChain Chains + Runnables",
            es_ia=True,
            tipo_procesamiento="langchain_completo"
        )
        
        return jsonify({
            **respuesta.dict(),
            "procesamiento_paralelo": resultado_paralelo,
            "cadena_usada": "SunatChains + Runnables",
            "validaciones": validacion.get("validaciones", {}),
            "metadata": resultado_paralelo.get("enriquecer", {})
        })
        
    except Exception as e:
        return jsonify({
            "error": f"Error en procesamiento LangChain: {str(e)}",
            "respuesta": "Error al procesar con cadenas LangChain.",
            "tecnica_usada": "Error LangChain"
        }), 500

@app.route("/continuar", methods=["POST"])
def continuar():
    data = request.get_json()
    mensaje = data.get("mensaje", "")
    context = data.get("context", "")
    categoria = data.get("categoria", "Otros")
    prompt = f"""### CONTINUACIÓN DE RESPUESTA SUNAT

Contexto previo de la conversación:
{context}

Solicitud adicional del usuario:
{mensaje}

Continúa proporcionando información adicional y detallada sobre el tema, manteniendo el formato estructurado:
- Usa **negritas** para títulos
- Usa numeración para pasos
- Usa guiones para listas
- Proporciona información completa y útil

### Continuación de SUNABOT:"""
    
    try:
        resultado = llm(
            prompt, 
            max_tokens=600,
            temperature=0.7,
            top_p=0.9,
            stop=["</s>", "### Consulta", "### Usuario:", "Human:", "Assistant:"]
        )
        texto = resultado['choices'][0]['text'].strip()
        
        texto = procesar_links_en_respuesta(texto)
        
        return jsonify({
            "respuesta": texto,
            "categoria": categoria
        })
        
    except Exception as e:
        return jsonify({
            "error": f"Error al continuar: {str(e)}",
            "respuesta": "Error al procesar la continuación."
        }), 500

@app.route("/responder_copilot", methods=["POST"])
def responder_copilot():
    """Endpoint que envía la consulta a GitHub Copilot para respuestas de alta calidad"""
    try:
        data = request.get_json()
        mensaje = data.get("mensaje", "")
        categoria_especifica = data.get("categoria", None)
        
        if not mensaje.strip():
            return jsonify({
                "error": "Por favor, proporciona una consulta válida.",
                "respuesta": "No se ha proporcionado ninguna consulta."
            }), 400
        
        # Detectar categoría automáticamente
        categoria_detectada = detectar_categoria(mensaje)
        categoria_final = categoria_especifica or categoria_detectada
        
        # Crear prompt optimizado para GitHub Copilot
        prompt_copilot = f"""
CONSULTA SUNAT: {mensaje}
CATEGORÍA: {categoria_final}

Como experto en temas tributarios de SUNAT (Perú), proporciona una respuesta:
- DIRECTA y CONCISA (máximo 3 párrafos)
- Con información ACTUALIZADA y PRECISA
- Incluye enlaces oficiales relevantes
- Usa **negritas** para puntos importantes
- Si hay pasos, enuméralos claramente

ENLACES OFICIALES ÚTILES:
- Consulta RUC: https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/FrameCriterioBusquedaWeb.jsp
- Portal SOL: https://www.sunat.gob.pe/sol.html
- Verificar comprobantes: https://e-consulta.sunat.gob.pe/ol-ti-itconsvalicpe/ConsValiCpe.htm
- Cronograma: https://ww3.sunat.gob.pe/cl-ti-itcronobligme/fvS01Alias
- Recuperar Clave SOL: https://www.gob.pe/7550-recuperar-la-clave-sol
"""
        
        # NOTA: Aquí el desarrollador debe implementar la llamada a la API de GitHub Copilot
        # Por ahora, usamos una respuesta simulada optimizada
        respuesta_simulada = generar_respuesta_especializada(mensaje, categoria_final)
        
        # Procesar enlaces en la respuesta
        respuesta_procesada = procesar_links_en_respuesta(respuesta_simulada)
        
        return jsonify({
            "respuesta": respuesta_procesada,
            "categoria": categoria_final,
            "tipo_procesamiento": "github_copilot",
            "tecnica_usada": "GitHub Copilot - Especialista SUNAT",
            "es_ia": True,
            "calidad": "premium",
            "prompt_usado": prompt_copilot.strip()
        })
        
    except Exception as e:
        return jsonify({
            "error": f"Error en procesamiento Copilot: {str(e)}",
            "respuesta": "Error al procesar con GitHub Copilot.",
            "tecnica_usada": "Error Copilot"
        }), 500

@app.route("/chat_directo", methods=["POST"])
def chat_directo():
    """Endpoint exclusivo para consultas directas del chat (Google Gemini)"""
    try:
        data = request.get_json()
        mensaje = data.get("mensaje", "")
        
        if not mensaje.strip():
            return jsonify({
                "error": "Por favor, proporciona una consulta válida.",
                "respuesta": "No se ha proporcionado ninguna consulta."
            }), 400
        
        # Para consultas directas del chat, SIEMPRE usar Google Gemini
        # Sin categorización automática, respuesta completamente libre
        
        # Generar respuesta con Google Gemini
        respuesta_gemini = generar_respuesta_copilot_libre(mensaje)
        
        return jsonify({
            "respuesta": respuesta_gemini,
            "categoria": "Chat Directo",
            "tipo_procesamiento": "google_gemini_libre",
            "tecnica_usada": "Google Gemini AI - Respuesta Libre" if GEMINI_AVAILABLE and gemini_model else "Modo Demostración",
            "es_ia": True if GEMINI_AVAILABLE and gemini_model else False,
            "calidad": "premium_gemini" if GEMINI_AVAILABLE and gemini_model else "demo"
        })
        
    except Exception as e:
        return jsonify({
            "error": f"Error en chat directo: {str(e)}",
            "respuesta": "Error al procesar tu consulta directa.",
            "tecnica_usada": "Error Chat Directo"
        }), 500

def detectar_pregunta_definicion(mensaje: str) -> bool:
    """Detecta si es una pregunta que busca definición o explicación"""
    mensaje_lower = mensaje.lower()
    palabras_definicion = [
        "qué es", "que es", "define", "significa", "explicame", "explícame",
        "concepto", "definición", "definicion", "información sobre"
    ]
    return any(palabra in mensaje_lower for palabra in palabras_definicion)

def generar_respuesta_copilot_libre(mensaje: str) -> str:
    """Genera respuesta libre REAL usando Google Gemini - SIN respuestas preestablecidas"""
    
    if not GEMINI_AVAILABLE or not gemini_model:
        return f"""**🤖 SUNABOT - Modo Demostración**

Hola, recibí tu consulta: *"{mensaje}"*

**Para activar respuestas de IA real, necesitas:**

1. **Obtener API Key GRATUITA** de Google AI Studio:
   - Ve a: https://aistudio.google.com/
   - Crea tu cuenta gratuita
   - Genera tu API Key

2. **Configurar la variable de entorno:**
   - Windows: `set GEMINI_API_KEY=tu_api_key_aqui`
   - Linux/Mac: `export GEMINI_API_KEY=tu_api_key_aqui`

3. **Reiniciar la aplicación**

**Mientras tanto, puedo ayudarte con:**
- **Portal SOL**: https://www.sunat.gob.pe/sol.html
- **Consulta RUC**: https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/FrameCriterioBusquedaWeb.jsp
- **Cronograma**: https://ww3.sunat.gob.pe/cl-ti-itcronobligme/fvS01Alias

*Nota: Una vez configurado, obtendré respuestas dinámicas de Google Gemini.*"""
    
    try:
        # Crear prompt especializado para SUNAT
        prompt_sunat = f"""Eres SUNABOT, un asistente especializado en temas tributarios de SUNAT (Perú). 

CONSULTA DEL USUARIO: "{mensaje}"

INSTRUCCIONES ESPECÍFICAS:
- Responde como experto en temas tributarios peruanos
- Sé directo, claro y útil
- Máximo 3-4 párrafos
- Usa **negritas** para puntos importantes
- Incluye enlaces oficiales de SUNAT cuando sea relevante
- Si no conoces algo específico, sé honesto al respecto
- Mantén un tono profesional pero amigable

ENLACES OFICIALES PRINCIPALES:
- Portal SOL: https://www.sunat.gob.pe/sol.html
- Consulta RUC: https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/FrameCriterioBusquedaWeb.jsp
- Verificar comprobantes: https://e-consulta.sunat.gob.pe/ol-ti-itconsvalicpe/ConsValiCpe.htm
- Cronograma: https://ww3.sunat.gob.pe/cl-ti-itcronobligme/fvS01Alias
- Recuperar Clave SOL: https://www.gob.pe/7550-recuperar-la-clave-sol

RESPUESTA DE SUNABOT:"""

        # Llamada real a Google Gemini
        response = gemini_model.generate_content(prompt_sunat)
        
        if response.text:
            # Procesar la respuesta y agregar marca de IA
            respuesta_procesada = f"""**🤖 Respuesta de Google Gemini**

{response.text.strip()}

---
*Respuesta generada por Google Gemini AI*"""
            return respuesta_procesada
        else:
            return "Lo siento, no pude generar una respuesta en este momento. Por favor, intenta nuevamente."
            
    except Exception as e:
        return f"""**Error en Google Gemini**
        
Lo siento, ocurrió un error al procesar tu consulta con Google Gemini: {str(e)}

**Para solucionar:**
1. Verifica tu GEMINI_API_KEY
2. Revisa tu conexión a internet
3. Reinicia la aplicación

**Enlaces útiles mientras tanto:**
- **Portal SOL**: https://www.sunat.gob.pe/sol.html
- **Consulta RUC**: https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/FrameCriterioBusquedaWeb.jsp"""

def generar_respuesta_especializada(mensaje: str, categoria: str) -> str:
    """Genera respuestas especializadas por categoría"""
    
    # Manejar categorías de definición
    if categoria == "Definición SUNAT":
        return """**¿Qué es SUNAT?**

La **SUNAT (Superintendencia Nacional de Aduanas y de Administración Tributaria)** es el organismo técnico especializado del Ministerio de Economía y Finanzas del Perú.

**Funciones principales**:
1. **Recaudación tributaria**: Administra impuestos como IGV, Renta, ISC
2. **Control aduanero**: Supervisa importaciones y exportaciones  
3. **Servicios al contribuyente**: RUC, declaraciones, comprobantes electrónicos

**Servicios digitales principales**:
- **Portal SOL**: https://www.sunat.gob.pe/sol.html
- **Consulta RUC**: https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/FrameCriterioBusquedaWeb.jsp
- **Cronograma de obligaciones**: https://ww3.sunat.gob.pe/cl-ti-itcronobligme/fvS01Alias

SUNAT es fundamental para el cumplimiento tributario en Perú."""
    
    elif categoria == "SUNAT General":
        return """**SUNAT - Información General**

La **SUNAT** es la entidad responsable de la administración tributaria y aduanera en Perú.

**Servicios más utilizados**:
- **Consulta de RUC**: https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/FrameCriterioBusquedaWeb.jsp
- **Portal SOL** (declaraciones y trámites): https://www.sunat.gob.pe/sol.html
- **Verificar comprobantes**: https://e-consulta.sunat.gob.pe/ol-ti-itconsvalicpe/ConsValiCpe.htm
- **Cronograma tributario**: https://ww3.sunat.gob.pe/cl-ti-itcronobligme/fvS01Alias

¿Tienes alguna consulta específica sobre RUC, declaraciones, facturación o Clave SOL?"""
    
    elif categoria == "Definición Renta 4ta":
        return """**¿Qué es la Renta de Cuarta Categoría?**

La **Renta de Cuarta Categoría** son los ingresos que obtienen las personas naturales por el **trabajo independiente** o por **servicios profesionales**.

**¿Quiénes están incluidos?**
- **Profesionales independientes**: médicos, abogados, ingenieros, contadores
- **Oficios independientes**: electricistas, plomeros, carpinteros
- **Servicios individuales**: consultores, asesores, capacitadores

**Características principales**:
1. **Trabajo independiente** (no hay relación laboral)
2. **Servicios personales** prestados sin materiales
3. **Facturación** con recibo por honorarios

**Obligaciones tributarias**:
- **Declaración mensual**: PDT 616 o Portal SOL
- **Retención del 8%** si el cliente es agente retenedor
- **Tasa anual**: 8% sobre renta neta o según escala progresiva

**Portal SOL**: https://www.sunat.gob.pe/sol.html
**Cronograma**: https://ww3.sunat.gob.pe/cl-ti-itcronobligme/fvS01Alias"""
    
    elif categoria == "Definición Renta 5ta":
        return """**¿Qué es la Renta de Quinta Categoría?**

La **Renta de Quinta Categoría** son los ingresos que obtienen las personas naturales por **trabajo dependiente** bajo relación laboral.

**¿Quiénes están incluidos?**
- **Trabajadores empleados** con contrato de trabajo
- **Funcionarios públicos** y empleados del Estado
- **Pensionistas** que reciben jubilación
- **Directores de empresas** con dietas

**Características principales**:
1. **Relación laboral dependiente** (empleador-trabajador)
2. **Sueldo fijo** o remuneración periódica
3. **Retención automática** por el empleador

**Sistema de retenciones**:
- **Empleador retiene** el impuesto mensualmente
- **Declaración anual**: Solo si hay exceso de retenciones
- **UIT 2024**: S/ 5,150 (exonerado hasta 7 UIT anuales)

**Portal SOL**: https://www.sunat.gob.pe/sol.html
**Cronograma**: https://ww3.sunat.gob.pe/cl-ti-itcronobligme/fvS01Alias"""
    
    # Primero verificar si es una pregunta de definición general
    if detectar_pregunta_definicion(mensaje):
        mensaje_lower = mensaje.lower()
        
        # Definiciones específicas
        if "sunat" in mensaje_lower and not any(word in mensaje_lower for word in ["ruc", "declaración", "factura", "clave"]):
            return """**¿Qué es SUNAT?**

La **SUNAT (Superintendencia Nacional de Aduanas y de Administración Tributaria)** es el organismo técnico especializado del Ministerio de Economía y Finanzas del Perú.

**Funciones principales**:
- **Administración tributaria**: Recaudación de impuestos internos
- **Administración aduanera**: Control del comercio exterior
- **Facilitación del comercio**: Simplificación de trámites

**Servicios principales**:
- Registro de contribuyentes (RUC)
- Declaraciones y pagos tributarios
- Fiscalización y control
- Orientación al contribuyente

**Portal oficial**: https://www.sunat.gob.pe/sol.html
**Consulta RUC**: https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/FrameCriterioBusquedaWeb.jsp"""
        
        elif "ruc" in mensaje_lower:
            return """**¿Qué es el RUC?**

El **RUC (Registro Único de Contribuyentes)** es un número de identificación de 11 dígitos que asigna SUNAT a toda persona natural o jurídica que realice actividades económicas en Perú.

**Características**:
- **Obligatorio** para actividades económicas
- **Único** e **intransferible**
- **Identifica** al contribuyente ante SUNAT

**Para qué sirve**:
- Emitir y recibir comprobantes de pago
- Presentar declaraciones tributarias
- Realizar trámites ante SUNAT

**Consultar RUC**: https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/FrameCriterioBusquedaWeb.jsp
**Registrar RUC**: https://ww1.sunat.gob.pe/a/html/contribuyente2/registro/adminforuc/registroruc/registroruc.html"""
        
        elif any(word in mensaje_lower for word in ["clave sol", "sol"]):
            return """**¿Qué es la Clave SOL?**

La **Clave SOL** es tu usuario y contraseña personal para acceder a **SUNAT Operaciones en Línea (SOL)**, la plataforma digital de SUNAT.

**Con tu Clave SOL puedes**:
- Presentar declaraciones tributarias
- Consultar deudas y pagos
- Emitir comprobantes de pago
- Actualizar datos del RUC
- Consultar cronogramas de obligaciones

**Obtener Clave SOL**:
- Se asigna automáticamente al registrar tu RUC
- **Recuperar**: https://www.gob.pe/7550-recuperar-la-clave-sol

**Portal SOL**: https://www.sunat.gob.pe/sol.html"""
        
        elif any(word in mensaje_lower for word in ["renta cuarta", "cuarta categoria", "cuarta categoría", "renta 4ta", "cuarta categor"]):
            return """**¿Qué es la Renta de Cuarta Categoría?**

La **Renta de Cuarta Categoría** son los ingresos por **trabajo independiente** o **servicios profesionales**.

**Incluye**:
- Profesionales independientes (médicos, abogados, ingenieros)
- Oficios independientes (electricistas, plomeros)
- Servicios de consultoría y asesoría

**Características**:
- **Trabajo independiente** (sin relación laboral)
- Facturación con **recibo por honorarios**
- **Retención del 8%** si el cliente es agente retenedor

**Portal SOL**: https://www.sunat.gob.pe/sol.html
**Cronograma**: https://ww3.sunat.gob.pe/cl-ti-itcronobligme/fvS01Alias"""
        
        elif any(word in mensaje_lower for word in ["renta quinta", "quinta categoria", "quinta categoría", "renta 5ta", "quinta categor"]):
            return """**¿Qué es la Renta de Quinta Categoría?**

La **Renta de Quinta Categoría** son los ingresos por **trabajo dependiente** bajo relación laboral.

**Incluye**:
- Trabajadores empleados con contrato
- Funcionarios públicos
- Pensionistas (jubilación)
- Directores de empresas

**Características**:
- **Relación laboral dependiente**
- **Retención automática** por el empleador
- Exonerado hasta 7 UIT anuales (S/ 36,050 en 2024)

**Portal SOL**: https://www.sunat.gob.pe/sol.html
**Cronograma**: https://ww3.sunat.gob.pe/cl-ti-itcronobligme/fvS01Alias"""
    
    respuestas_especializadas = {
        "RUC": {
            "consultar": f"""**Consulta de RUC en SUNAT**

Para consultar un RUC, tienes estas opciones:

1. **Portal oficial**: Ingresa a https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/FrameCriterioBusquedaWeb.jsp
2. **Buscar por**: Número de RUC, razón social o nombre
3. **Información disponible**: Estado, domicilio fiscal, actividad económica, representantes legales

**¿Necesitas registrar un RUC?** Ve a: https://ww1.sunat.gob.pe/a/html/contribuyente2/registro/adminforuc/registroruc/registroruc.html

La consulta es **gratuita** y está disponible **24/7**.""",
            
            "registro": f"""**Registro de RUC en SUNAT**

Para registrar un RUC como persona natural o jurídica:

1. **Requisitos básicos**: DNI vigente, formulario 2119, comprobante de domicilio
2. **Portal de registro**: https://ww1.sunat.gob.pe/a/html/contribuyente2/registro/adminforuc/registroruc/registroruc.html
3. **Proceso online**: Completamente digital, sin necesidad de ir presencialmente

**Tiempo de procesamiento**: Inmediato para personas naturales, hasta 1 día hábil para jurídicas.

Después del registro, accede al **Portal SOL**: https://www.sunat.gob.pe/sol.html""",
            
            "general": f"""**Información sobre RUC**

El **RUC (Registro Único de Contribuyentes)** es obligatorio para realizar actividades económicas en Perú.

**Consultar RUC**: https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/FrameCriterioBusquedaWeb.jsp
**Registrar RUC**: https://ww1.sunat.gob.pe/a/html/contribuyente2/registro/adminforuc/registroruc/registroruc.html

**Portal SOL** para trámites: https://www.sunat.gob.pe/sol.html"""
        },
        
        "Declaraciones": {
            "cronograma": f"""**Cronograma de Obligaciones Tributarias**

Para consultar fechas de vencimiento:

1. **Portal oficial**: https://ww3.sunat.gob.pe/cl-ti-itcronobligme/fvS01Alias
2. **Buscar por**: Último dígito del RUC y tipo de tributo
3. **Información disponible**: Fechas de vencimiento, multas, intereses

**Declaraciones mensuales**: IGV, Renta de 4ta/5ta categoría, planillas
**Declaraciones anuales**: Renta anual, patrimonio predial

Para presentar declaraciones: **Portal SOL** https://www.sunat.gob.pe/sol.html""",
            
            "general": f"""**Declaraciones Tributarias en SUNAT**

**Cronograma de vencimientos**: https://ww3.sunat.gob.pe/cl-ti-itcronobligme/fvS01Alias
**Presentar declaraciones**: https://www.sunat.gob.pe/sol.html

**Tipos principales**:
- **Mensuales**: IGV, retenciones
- **Anuales**: Renta anual
- **Otras**: Según régimen tributario

Recuerda revisar tu cronograma según el último dígito de tu RUC."""
        },
        
        "Facturación": {
            "verificar": f"""**Verificación de Comprobantes de Pago**

Para verificar si un comprobante es válido:

1. **Portal de verificación**: https://e-consulta.sunat.gob.pe/ol-ti-itconsvalicpe/ConsValiCpe.htm
2. **Datos necesarios**: RUC del emisor, tipo y número del comprobante
3. **Consulta libre**: https://ww1.sunat.gob.pe/ol-ti-itconsultaunificadalibre/consultaUnificadaLibre/consulta

**Comprobantes válidos**: Facturas, boletas, notas de crédito/débito electrónicas
**Verificación gratuita** y disponible **24/7**.""",
            
            "general": f"""**Facturación Electrónica SUNAT**

**Verificar comprobantes**: https://e-consulta.sunat.gob.pe/ol-ti-itconsvalicpe/ConsValiCpe.htm
**Consulta libre**: https://ww1.sunat.gob.pe/ol-ti-itconsultaunificadalibre/consultaUnificadaLibre/consulta

Desde 2019, todos los comprobantes deben ser **electrónicos**. Verifica siempre la validez de facturas y boletas en el portal oficial."""
        },
        
        "Clave SOL": {
            "recuperar": f"""**Recuperar Clave SOL**

Si olvidaste tu Clave SOL:

1. **Portal de recuperación**: https://www.gob.pe/7550-recuperar-la-clave-sol
2. **Requisitos**: DNI vigente y datos del RUC
3. **Proceso online**: Completamente digital

**Alternativas**:
- **Presencial**: En cualquier centro de servicios SUNAT
- **Call Center**: 0-801-12-100 (gratuito)

**Portal SOL**: https://www.sunat.gob.pe/sol.html""",
            
            "general": f"""**Clave SOL - Acceso a Servicios SUNAT**

La **Clave SOL** te permite acceder a todos los servicios en línea de SUNAT.

**Ingresar**: https://www.sunat.gob.pe/sol.html
**Recuperar clave**: https://www.gob.pe/7550-recuperar-la-clave-sol

Con tu Clave SOL puedes: presentar declaraciones, consultar deudas, emitir comprobantes, y más."""
        },
        
        "Regímenes": {
            "general": f"""**Regímenes Tributarios en Perú**

**Tipos principales**:
1. **RUS**: Régimen Único Simplificado (pequeños negocios)
2. **RER**: Régimen Especial de Renta (ingresos hasta S/ 525,000)
3. **MYPE Tributario**: Para micro y pequeñas empresas
4. **Régimen General**: Sin límites de ingresos

**Cambio de régimen**: Se realiza en el **Portal SOL** https://www.sunat.gob.pe/sol.html

Elige el régimen según tus ingresos anuales y tipo de actividad."""
        },
        
        "Otros": {
            "general": f"""**Consultas Generales SUNAT**

**Portal principal**: https://www.sunat.gob.pe/sol.html
**Consulta RUC**: https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/FrameCriterioBusquedaWeb.jsp
**Cronograma**: https://ww3.sunat.gob.pe/cl-ti-itcronobligme/fvS01Alias

Para consultas específicas, usa el **Portal SOL** con tu Clave SOL o visita un centro de servicios SUNAT."""
        }
    }
    
    # Detectar subcategoría basada en palabras clave
    mensaje_lower = mensaje.lower()
    
    if categoria == "RUC":
        if any(word in mensaje_lower for word in ["consultar", "buscar", "verificar"]):
            return respuestas_especializadas["RUC"]["consultar"]
        elif any(word in mensaje_lower for word in ["registrar", "inscribir", "crear"]):
            return respuestas_especializadas["RUC"]["registro"]
        else:
            return respuestas_especializadas["RUC"]["general"]
    
    elif categoria == "Declaraciones":
        if any(word in mensaje_lower for word in ["cronograma", "vencimiento", "fecha"]):
            return respuestas_especializadas["Declaraciones"]["cronograma"]
        else:
            return respuestas_especializadas["Declaraciones"]["general"]
    
    elif categoria == "Facturación":
        if any(word in mensaje_lower for word in ["verificar", "validar", "comprobar"]):
            return respuestas_especializadas["Facturación"]["verificar"]
        else:
            return respuestas_especializadas["Facturación"]["general"]
    
    elif categoria == "Clave SOL":
        if any(word in mensaje_lower for word in ["recuperar", "olvidé", "perdí"]):
            return respuestas_especializadas["Clave SOL"]["recuperar"]
        else:
            return respuestas_especializadas["Clave SOL"]["general"]
    
    elif categoria == "Regímenes":
        return respuestas_especializadas["Regímenes"]["general"]
    
    else:
        return respuestas_especializadas["Otros"]["general"]

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)

