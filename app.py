from flask import Flask, render_template, request, jsonify
from llama_cpp import Llama
from typing import List, Dict, Any, Optional, Union
import os
import json

app = Flask(__name__)

# Cargar modelo
llm = Llama(
    model_path="modelo/mistral-7b-instruct-v0.1.Q2_K.gguf",
    n_ctx=2048,  
    verbose=False
)

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

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)

