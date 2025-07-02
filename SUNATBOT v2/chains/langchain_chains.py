# chains/langchain_chains.py - Cadenas y Runnables
from langchain.schema.runnable import RunnableLambda, RunnableParallel, RunnablePassthrough
from langchain.prompts import PromptTemplate
from typing import Dict, Any, List
import re

class SunatChains:
    """Clase que maneja las cadenas de LangChain para SUNATBOT"""
    
    def __init__(self, llm_instance, categorias_exactas: Dict[str, str]):
        self.llm = llm_instance
        self.categorias = categorias_exactas
        self.setup_chains()
    
    def setup_chains(self):
        """Configura todas las cadenas y runnables"""
        # Runnables individuales
        self.categorizar_runnable = RunnableLambda(self._detectar_categoria)
        self.procesar_links_runnable = RunnableLambda(self._procesar_links)
        self.generar_respuesta_runnable = RunnableLambda(self._generar_respuesta)
        
        # Cadena paralela para múltiples procesamientos
        self.parallel_chain = RunnableParallel({
            "categoria": self.categorizar_runnable,
            "mensaje_original": RunnablePassthrough(),
            "metadata": RunnableLambda(self._extraer_metadata)
        })
        
        # Cadena secuencial completa
        self.main_chain = (
            self.parallel_chain |
            self.generar_respuesta_runnable |
            self.procesar_links_runnable
        )
    
    def _detectar_categoria(self, input_data: Any) -> str:
        """Runnable para detectar categoría"""
        if isinstance(input_data, dict):
            mensaje = input_data.get("mensaje", "")
        else:
            mensaje = str(input_data)
            
        mensaje_lower = mensaje.lower()
        
        if any(word in mensaje_lower for word in ["ruc", "registro único", "inscripción ruc", "contribuyente"]):
            return "RUC"
        elif any(word in mensaje_lower for word in ["declaración", "declarar", "djm", "cronograma"]):
            return "Declaraciones"
        elif any(word in mensaje_lower for word in ["factura", "comprobante", "boleta", "electrónica"]):
            return "Facturación"
        elif any(word in mensaje_lower for word in ["clave sol", "contraseña", "acceso", "sol"]):
            return "Clave SOL"
        elif any(word in mensaje_lower for word in ["régimen", "rus", "rer", "mype"]):
            return "Regímenes"
        else:
            return "Otros"
    
    def _extraer_metadata(self, input_data: Any) -> Dict[str, Any]:
        """Runnable para extraer metadata"""
        if isinstance(input_data, dict):
            mensaje = input_data.get("mensaje", "")
        else:
            mensaje = str(input_data)
            
        return {
            "longitud": len(mensaje),
            "palabras": len(mensaje.split()),
            "tiene_signos": bool(re.search(r'[?¿!¡]', mensaje)),
            "timestamp": "2025-07-02"
        }
    
    def _generar_respuesta(self, parallel_result: Dict[str, Any]) -> Dict[str, Any]:
        """Runnable para generar respuesta usando el LLM"""
        categoria = parallel_result["categoria"]
        mensaje = parallel_result["mensaje_original"]
        metadata = parallel_result["metadata"]
        
        # Crear prompt basado en categoría
        prompt = self._crear_prompt_categoria(mensaje, categoria)
        
        try:
            resultado = self.llm(
                prompt,
                max_tokens=800,
                temperature=0.7,
                top_p=0.9,
                stop=["</s>", "### Consulta", "### Usuario:"]
            )
            
            texto_respuesta = resultado['choices'][0]['text'].strip()
            
            return {
                "respuesta": texto_respuesta,
                "categoria": categoria,
                "metadata": metadata,
                "tecnica_usada": f"Cadena LangChain - {categoria}",
                "success": True
            }
            
        except Exception as e:
            return {
                "respuesta": f"Error en cadena: {str(e)}",
                "categoria": categoria,
                "metadata": metadata,
                "tecnica_usada": "Error en Cadena",
                "success": False,
                "error": str(e)
            }
    
    def _procesar_links(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Runnable para procesar links en la respuesta"""
        if not response_data.get("success", False):
            return response_data
            
        texto = response_data["respuesta"]
        url_pattern = r'https?://[^\s<>"]+(?:[^\s<>".,;:])'
        
        def reemplazar_url(match):
            url = match.group(0)
            return f'<a href="{url}" target="_blank" style="color: #1976d2; text-decoration: underline;">{url}</a>'
        
        texto_con_links = re.sub(url_pattern, reemplazar_url, texto)
        response_data["respuesta"] = texto_con_links
        
        # Extraer lista de links
        links = re.findall(url_pattern, texto)
        response_data["links_incluidos"] = links
        
        return response_data
    
    def _crear_prompt_categoria(self, mensaje: str, categoria: str) -> str:
        """Crea prompts específicos por categoría"""
        sistemas = {
            "RUC": f"""### SUNABOT - Especialista RUC (Cadena LangChain)
Consulta: "{mensaje}"
Responde de forma DIRECTA sobre RUC. Incluye links relevantes.
### Respuesta:""",
            
            "Declaraciones": f"""### SUNABOT - Especialista Declaraciones (Cadena LangChain)
Consulta: "{mensaje}"
Responde sobre declaraciones tributarias. Incluye cronograma si es relevante.
### Respuesta:""",
            
            "Facturación": f"""### SUNABOT - Especialista Facturación (Cadena LangChain)
Consulta: "{mensaje}"
Responde sobre comprobantes y facturación electrónica.
### Respuesta:""",
            
            "Clave SOL": f"""### SUNABOT - Especialista Clave SOL (Cadena LangChain)
Consulta: "{mensaje}"
Responde sobre Clave SOL y acceso a servicios.
### Respuesta:""",
            
            "Regímenes": f"""### SUNABOT - Especialista Regímenes (Cadena LangChain)
Consulta: "{mensaje}"
Responde sobre regímenes tributarios.
### Respuesta:""",
            
            "Otros": f"""### SUNABOT - General (Cadena LangChain)
Consulta: "{mensaje}"
Responde sobre consultas tributarias generales.
### Respuesta:"""
        }
        
        return sistemas.get(categoria, sistemas["Otros"])
    
    def procesar_consulta_con_chain(self, mensaje: str, categoria_especifica: str = None) -> Dict[str, Any]:
        """Procesa consulta usando la cadena principal"""
        input_data = {
            "mensaje": mensaje,
            "categoria_especifica": categoria_especifica
        }
        
        try:
            resultado = self.main_chain.invoke(input_data)
            return resultado
        except Exception as e:
            return {
                "respuesta": f"Error en procesamiento con cadenas: {str(e)}",
                "categoria": "Error",
                "success": False,
                "error": str(e),
                "tecnica_usada": "Error en Cadena LangChain"
            }
