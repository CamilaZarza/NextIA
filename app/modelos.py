from typing import Literal

from pydantic import BaseModel, Field, field_validator

# Aca se definen los formatos de datos que se espera recibir al crear un estudiante, una oferta o una compatibilidad.

class EstudianteEntrada(BaseModel):
    nombre: str = Field(min_length=2, max_length=80)
    carrera: str = Field(min_length=2, max_length=100)
    competencias: list[str] = Field(min_length=1)   # al menos una


class OfertaEntrada(BaseModel):
    titulo: str = Field(min_length=2, max_length=100)
    empresa: str = Field(min_length=2, max_length=100)
    requisitos_obligatorios: list[str] = Field(min_length=1)
    requisitos_deseables: list[str] = []


class CompatibilidadEntrada(BaseModel):
    estudiante_id: int
    oferta_id: int

class RecomendacionEntrada(BaseModel):
    resultado_id: int
    texto: str = Field(min_length=5)
    modelo: str = "gemini"

    @field_validator("texto")
    @classmethod
    def validar_texto_generado(cls, texto: str) -> str:
        # Si el nodo de IA no devolvió nada, n8n manda la expresión sin evaluar
        if texto.strip().startswith("={{"):
            raise ValueError("el texto no fue generado por la IA (llegó una expresión de n8n sin evaluar)")
        return texto.strip()


# Supervisión humana: una persona aprueba o rechaza lo que generó la IA
class RevisionEntrada(BaseModel):
    estado: Literal["aprobada", "rechazada"]
    revisor: str = Field(min_length=2, max_length=80)
    comentario: str = Field(default="", max_length=500)