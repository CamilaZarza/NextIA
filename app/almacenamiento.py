import json
from pathlib import Path

# Carpeta data/ ubicada al lado de la carpeta app/
CARPETA = Path(__file__).resolve().parent.parent / "data"


def leer(nombre: str) -> list[dict]:
    ruta = CARPETA / f"{nombre}.json"
    if not ruta.exists():
        return []                      # si el archivo no existe, lista vacía
    with open(ruta, encoding="utf-8") as archivo:
        return json.load(archivo)


def guardar(nombre: str, datos: list[dict]) -> None:
    CARPETA.mkdir(exist_ok=True)
    with open(CARPETA / f"{nombre}.json", "w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, ensure_ascii=False, indent=2)


def siguiente_id(datos: list[dict]) -> int:
    # El mayor id existente + 1 (o 1 si la lista está vacía)
    return max((d["id"] for d in datos), default=0) + 1