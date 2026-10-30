"""Pasa todo a minúsculas y sin espacios, para que 'Python ' == 'python'."""
def normalizar(competencias: list[str]) -> set[str]:
    return {c.strip().lower() for c in competencias if c.strip()}


def calcular_compatibilidad(estudiante: dict, oferta: dict) -> dict:
    tiene = normalizar(estudiante["competencias"])
    obligatorias = normalizar(oferta["requisitos_obligatorios"])
    deseables = normalizar(oferta["requisitos_deseables"])

    if not obligatorias:
        raise ValueError("La oferta debe tener al menos un requisito obligatorio")

    cumplidas_obl = obligatorias & tiene          # intersección
    faltantes_obl = obligatorias - tiene          # lo que le falta
    cumplidas_des = deseables & tiene
    faltantes_des = deseables - tiene

    puntos_obl = 70 * len(cumplidas_obl) / len(obligatorias)
    puntos_des = 30 * len(cumplidas_des) / len(deseables) if deseables else 30

    return {
        "estudiante": estudiante["nombre"],
        "oferta": oferta["titulo"],
        "score": round(puntos_obl + puntos_des, 1),
        "competencias_faltantes": sorted(faltantes_obl | faltantes_des),
        "faltantes_obligatorias": sorted(faltantes_obl),
        "origen": "calculado con reglas de Python",
    }