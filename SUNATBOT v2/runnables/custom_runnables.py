# runnables/custom_runnables.py - Funciones Ejecutables Personalizadas
from langchain.schema.runnable import Runnable, RunnableLambda, RunnableParallel
from typing import Dict, Any, List, Union
import asyncio
from concurrent.futures import ThreadPoolExecutor

class SunatRunnables:
    """Clase que contiene todos los Runnables personalizados para SUNATBOT"""
    
    @staticmethod
    def crear_runnable_categorizar() -> RunnableLambda:
        """Crea un Runnable para categorizar mensajes"""
        def categorizar(input_data: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
            if isinstance(input_data, dict):
                mensaje = input_data.get("mensaje", "")
            else:
                mensaje = str(input_data)
            
            mensaje_lower = mensaje.lower()
            categoria = "Otros"
            confianza = 0.5
            
            categorias_palabras = {
                "RUC": ["ruc", "registro único", "inscripción", "contribuyente", "alta ruc", "baja ruc"],
                "Declaraciones": ["declaración", "declarar", "djm", "cronograma", "vencimiento", "pdt"],
                "Facturación": ["factura", "comprobante", "boleta", "electrónica", "see", "emisión"],
                "Clave SOL": ["clave sol", "contraseña", "acceso", "sol", "representante", "usuario"],
                "Regímenes": ["régimen", "rus", "rer", "mype", "general", "cambio régimen"]
            }
            
            for cat, palabras in categorias_palabras.items():
                matches = sum(1 for palabra in palabras if palabra in mensaje_lower)
                if matches > 0:
                    categoria = cat
                    confianza = min(matches / len(palabras), 1.0)
                    break
            
            return {
                "categoria": categoria,
                "confianza": confianza,
                "mensaje_original": mensaje,
                "palabras_detectadas": [p for p in categorias_palabras.get(categoria, []) if p in mensaje_lower]
            }
        
        return RunnableLambda(categorizar)
    
    @staticmethod
    def crear_runnable_validador() -> RunnableLambda:
        """Crea un Runnable para validar entrada"""
        def validar(input_data: Dict[str, Any]) -> Dict[str, Any]:
            mensaje = input_data.get("mensaje", "")
            
            validaciones = {
                "es_valido": len(mensaje.strip()) > 0,
                "longitud_apropiada": 3 <= len(mensaje) <= 1000,
                "tiene_contenido": bool(mensaje.strip()),
                "es_tributario": any(word in mensaje.lower() for word in 
                                   ["ruc", "declaración", "factura", "sol", "régimen", "sunat", "tributario"])
            }
            
            input_data.update({
                "validaciones": validaciones,
                "es_consulta_valida": all(validaciones.values())
            })
            
            return input_data
        
        return RunnableLambda(validar)
    
    @staticmethod
    def crear_runnable_enriquecedor() -> RunnableLambda:
        """Crea un Runnable para enriquecer datos"""
        def enriquecer(input_data: Dict[str, Any]) -> Dict[str, Any]:
            categoria = input_data.get("categoria", "Otros")
            
            enlaces_categoria = {
                "RUC": [
                    "https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/FrameCriterioBusquedaWeb.jsp",
                    "https://ww1.sunat.gob.pe/a/html/contribuyente2/registro/adminforuc/registroruc/registroruc.html"
                ],
                "Declaraciones": [
                    "https://ww3.sunat.gob.pe/cl-ti-itcronobligme/fvS01Alias",
                    "https://www.sunat.gob.pe/sol.html"
                ],
                "Facturación": [
                    "https://e-consulta.sunat.gob.pe/ol-ti-itconsvalicpe/ConsValiCpe.htm",
                    "https://ww1.sunat.gob.pe/ol-ti-itconsultaunificadalibre/consultaUnificadaLibre/consulta"
                ],
                "Clave SOL": [
                    "https://www.sunat.gob.pe/sol.html",
                    "https://www.gob.pe/7550-recuperar-la-clave-sol"
                ],
                "Regímenes": [
                    "https://www.sunat.gob.pe/sol.html"
                ],
                "Otros": [
                    "https://www.sunat.gob.pe/sol.html"
                ]
            }
            
            input_data.update({
                "enlaces_recomendados": enlaces_categoria.get(categoria, []),
                "contexto_categoria": f"Especialista en {categoria}",
                "timestamp": "2025-07-02",
                "version_procesamiento": "LangChain_v1.0"
            })
            
            return input_data
        
        return RunnableLambda(enriquecer)
    
    @staticmethod
    def crear_cadena_paralela_completa() -> RunnableParallel:
        """Crea una cadena paralela que ejecuta múltiples Runnables"""
        return RunnableParallel({
            "categorizar": SunatRunnables.crear_runnable_categorizar(),
            "validar": SunatRunnables.crear_runnable_validador(),
            "enriquecer": SunatRunnables.crear_runnable_categorizar() | SunatRunnables.crear_runnable_enriquecedor()
        })
    
    @staticmethod
    def crear_runnable_async_procesador() -> RunnableLambda:
        """Crea un Runnable para procesamiento asíncrono"""
        async def procesar_async(input_data: Dict[str, Any]) -> Dict[str, Any]:
            # Simular procesamiento asíncrono
            await asyncio.sleep(0.1)
            
            mensaje = input_data.get("mensaje", "")
            categoria = input_data.get("categoria", "Otros")
            
            # Procesamiento paralelo simulado
            with ThreadPoolExecutor(max_workers=3) as executor:
                future_analisis = executor.submit(lambda: {"analisis": "completado"})
                future_validacion = executor.submit(lambda: {"validacion": "exitosa"})
                future_enriquecimiento = executor.submit(lambda: {"enriquecimiento": "aplicado"})
                
                resultados = {
                    "analisis": future_analisis.result(),
                    "validacion": future_validacion.result(),
                    "enriquecimiento": future_enriquecimiento.result()
                }
            
            input_data.update({
                "procesamiento_async": resultados,
                "estado": "procesado_async",
                "tiempo_procesamiento": "~0.1s"
            })
            
            return input_data
        
        return RunnableLambda(procesar_async)
