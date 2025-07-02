# models/schemas.py - Salidas Estructuradas
from pydantic import BaseModel, Field
from typing import List, Literal, Optional
import re

class RespuestaEstructurada(BaseModel):
    """Esquema estructurado para las respuestas del chatbot"""
    respuesta: str = Field(description="Respuesta del chatbot")
    categoria: Literal["RUC", "Declaraciones", "Facturación", "Clave SOL", "Regímenes", "Otros"]
    confianza: float = Field(ge=0.0, le=1.0, description="Nivel de confianza en la categorización")
    links_incluidos: List[str] = Field(default=[], description="URLs incluidas en la respuesta")
    tecnica_usada: str = Field(description="Técnica de procesamiento utilizada")
    es_ia: bool = Field(default=True, description="Si la respuesta fue generada por IA")
    tipo_procesamiento: str = Field(description="Tipo de procesamiento aplicado")

    def extraer_links(self) -> List[str]:
        """Extrae automáticamente los links de la respuesta"""
        url_pattern = r'https?://[^\s<>"]+(?:[^\s<>".,;:])'
        return re.findall(url_pattern, self.respuesta)

    def calcular_confianza(self, palabras_clave: List[str], mensaje: str) -> float:
        """Calcula la confianza basada en palabras clave encontradas"""
        mensaje_lower = mensaje.lower()
        matches = sum(1 for palabra in palabras_clave if palabra in mensaje_lower)
        return min(matches / len(palabras_clave), 1.0) if palabras_clave else 0.5

class ConsultaInput(BaseModel):
    """Esquema para las consultas de entrada"""
    mensaje: str = Field(min_length=1, description="Mensaje del usuario")
    categoria_especifica: Optional[str] = Field(None, description="Categoría específica si se proporciona")
    tipo_respuesta: str = Field(default="general", description="Tipo de respuesta solicitada")
    max_length: int = Field(default=1200, ge=100, le=2000, description="Longitud máxima de respuesta")

class ContinuacionInput(BaseModel):
    """Esquema para continuaciones de conversación"""
    mensaje: str = Field(min_length=1, description="Mensaje adicional del usuario")
    context: str = Field(description="Contexto previo de la conversación")
    categoria: str = Field(default="Otros", description="Categoría de la consulta")
