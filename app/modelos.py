from pydantic import BaseModel, Field

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