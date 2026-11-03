from fastapi import FastAPI, HTTPException

from app import almacenamiento as db
from app.modelos import (
    CompatibilidadEntrada,
    EstudianteEntrada,
    OfertaEntrada,
    RecomendacionEntrada,
)
from app.scoring import calcular_compatibilidad

app = FastAPI(title="Nextia API")


def buscar_por_id(coleccion: str, id_: int, etiqueta: str) -> dict:
    """Devuelve el registro con ese id o responde 404."""
    for item in db.leer(coleccion):
        if item["id"] == id_:
            return item
    raise HTTPException(status_code=404, detail=f"{etiqueta} {id_} no existe")


@app.get("/status")
def status() -> dict:
    return {"ok": True, "estado": "activo"}


# ---------- Estudiantes ----------
@app.post("/estudiantes", status_code=201)
def crear_estudiante(datos: EstudianteEntrada) -> dict:
    estudiantes = db.leer("estudiantes")
    nuevo = {"id": db.siguiente_id(estudiantes), **datos.model_dump()}
    estudiantes.append(nuevo)
    db.guardar("estudiantes", estudiantes)
    return nuevo


@app.get("/estudiantes")
def listar_estudiantes() -> list[dict]:
    return db.leer("estudiantes")


@app.put("/estudiantes/{estudiante_id}")
def actualizar_estudiante(estudiante_id: int, datos: EstudianteEntrada) -> dict:
    estudiantes = db.leer("estudiantes")
    for posicion, estudiante in enumerate(estudiantes):
        if estudiante["id"] == estudiante_id:
            estudiantes[posicion] = {"id": estudiante_id, **datos.model_dump()}
            db.guardar("estudiantes", estudiantes)
            return estudiantes[posicion]
    raise HTTPException(status_code=404, detail=f"Estudiante {estudiante_id} no existe")


# ---------- Ofertas ----------
@app.post("/ofertas", status_code=201)
def crear_oferta(datos: OfertaEntrada) -> dict:
    ofertas = db.leer("ofertas")
    nueva = {"id": db.siguiente_id(ofertas), **datos.model_dump()}
    ofertas.append(nueva)
    db.guardar("ofertas", ofertas)
    return nueva


@app.get("/ofertas")
def listar_ofertas() -> list[dict]:
    return db.leer("ofertas")


# ---------- Procesamiento ----------
@app.post("/compatibilidad", status_code=201)
def calcular(datos: CompatibilidadEntrada) -> dict:
    estudiante = buscar_por_id("estudiantes", datos.estudiante_id, "Estudiante")
    oferta = buscar_por_id("ofertas", datos.oferta_id, "Oferta")

    try:
        calculo = calcular_compatibilidad(estudiante, oferta)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    resultados = db.leer("resultados")
    resultado = {
        "id": db.siguiente_id(resultados),
        "estudiante_id": estudiante["id"],
        "oferta_id": oferta["id"],
        **calculo,
    }
    resultados.append(resultado)
    db.guardar("resultados", resultados)
    return resultado


@app.get("/resultados")
def listar_resultados(estudiante_id: int | None = None) -> list[dict]:
    resultados = db.leer("resultados")
    if estudiante_id is not None:
        resultados = [r for r in resultados if r["estudiante_id"] == estudiante_id]
    return resultados

# ---------- Recomendaciones (las genera la IA vía n8n) ----------
@app.get("/resultados/{resultado_id}")
def obtener_resultado(resultado_id: int) -> dict:
    return buscar_por_id("resultados", resultado_id, "Resultado")


@app.post("/recomendaciones", status_code=201)
def guardar_recomendacion(datos: RecomendacionEntrada) -> dict:
    buscar_por_id("resultados", datos.resultado_id, "Resultado")  # valida que exista
    recomendaciones = db.leer("recomendaciones")
    nueva = {
        "id": db.siguiente_id(recomendaciones),
        **datos.model_dump(),
        "origen": "generado por IA (requiere revisión humana)",
    }
    recomendaciones.append(nueva)
    db.guardar("recomendaciones", recomendaciones)
    return nueva


@app.get("/recomendaciones")
def listar_recomendaciones(resultado_id: int | None = None) -> list[dict]:
    recomendaciones = db.leer("recomendaciones")
    if resultado_id is not None:
        recomendaciones = [r for r in recomendaciones if r["resultado_id"] == resultado_id]
    return recomendaciones