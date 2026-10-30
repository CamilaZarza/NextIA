import requests
import streamlit as st

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="NextIA", page_icon="🎯", layout="wide")


def llamar_api(metodo: str, ruta: str, **kwargs):
    """Llama a la API. Devuelve (datos, error). Nunca rompe la pantalla."""
    try:
        respuesta = requests.request(metodo, f"{API_URL}{ruta}", timeout=10, **kwargs)
    except requests.exceptions.ConnectionError:
        return None, "No se pudo conectar con la API. ¿Está corriendo uvicorn?"
    except requests.exceptions.Timeout:
        return None, "La API tardó demasiado en responder."

    if respuesta.status_code >= 400:
        try:
            detalle = respuesta.json().get("detail", "Error desconocido")
        except ValueError:
            detalle = respuesta.text
        if isinstance(detalle, list):  # errores 422 de Pydantic
            detalle = "; ".join(f"{e['loc'][-1]}: {e['msg']}" for e in detalle)
        return None, f"Error {respuesta.status_code}: {detalle}"
    return respuesta.json(), None


def a_lista(texto: str) -> list[str]:
    """'python, git , excel' -> ['python', 'git', 'excel']"""
    return [c.strip() for c in texto.split(",") if c.strip()]


st.title("🎯 Nextia")
st.caption("Plataforma de vinculación y desarrollo profesional")

tab_est, tab_ofe, tab_comp, tab_res = st.tabs(
    ["Estudiantes", "Ofertas", "Compatibilidad", "Resultados"]
)

# ---------------- ESTUDIANTES ----------------
with tab_est:
    st.subheader("Crear nuevo estudiante")
    with st.form("form_estudiante", clear_on_submit=True):
        nombre = st.text_input("Nombre")
        carrera = st.text_input("Carrera")
        competencias = st.text_input(
            "Competencias (separadas por coma)", placeholder="python, git, excel"
        )
        enviar = st.form_submit_button("Guardar")

    if enviar:
        datos, error = llamar_api(
            "POST",
            "/estudiantes",
            json={"nombre": nombre, "carrera": carrera, "competencias": a_lista(competencias)},
        )
        if error:
            st.error(error)
        else:
            st.success(f"Estudiante creado con id {datos['id']}")

    st.subheader("Estudiantes registrados")
    estudiantes, error = llamar_api("GET", "/estudiantes")
    if error:
        st.error(error)
    elif estudiantes:
        st.dataframe(estudiantes, use_container_width=True)

        st.subheader("Modificar un estudiante")
        elegido = st.selectbox(
            "Elegí un estudiante",
            estudiantes,
            format_func=lambda e: f"{e['id']} - {e['nombre']}",
            key="editar_estudiante",
        )
        with st.form("form_editar"):
            nuevas = st.text_input(
                "Competencias",
                value=", ".join(elegido["competencias"]),
                key=f"comp_{elegido['id']}",
            )
            actualizar = st.form_submit_button("Actualizar")
        if actualizar:
            cambios = {
                "nombre": elegido["nombre"],
                "carrera": elegido["carrera"],
                "competencias": a_lista(nuevas),
            }
            datos, error = llamar_api("PUT", f"/estudiantes/{elegido['id']}", json=cambios)
            if error:
                st.error(error)
            else:
                st.success("Estudiante actualizado (la tabla se refresca en la próxima acción)")
    else:
        st.info("Todavía no hay estudiantes.")

# ---------------- OFERTAS ----------------
with tab_ofe:
    st.subheader("Nueva oferta")
    with st.form("form_oferta", clear_on_submit=True):
        titulo = st.text_input("Título del puesto")
        empresa = st.text_input("Empresa")
        obligatorios = st.text_input("Requisitos obligatorios (coma)", placeholder="python, sql")
        deseables = st.text_input("Requisitos deseables (coma)", placeholder="power bi, git")
        enviar_oferta = st.form_submit_button("Guardar")

    if enviar_oferta:
        datos, error = llamar_api(
            "POST",
            "/ofertas",
            json={
                "titulo": titulo,
                "empresa": empresa,
                "requisitos_obligatorios": a_lista(obligatorios),
                "requisitos_deseables": a_lista(deseables),
            },
        )
        if error:
            st.error(error)
        else:
            st.success(f"Oferta creada con id {datos['id']}")

    st.subheader("Ofertas registradas")
    ofertas, error = llamar_api("GET", "/ofertas")
    if error:
        st.error(error)
    elif ofertas:
        st.dataframe(ofertas, use_container_width=True)
    else:
        st.info("Todavía no hay ofertas.")

# ---------------- COMPATIBILIDAD ----------------
with tab_comp:
    st.subheader("Calcular compatibilidad")
    estudiantes, error_e = llamar_api("GET", "/estudiantes")
    ofertas, error_o = llamar_api("GET", "/ofertas")

    if error_e or error_o:
        st.error(error_e or error_o)
    elif not estudiantes or not ofertas:
        st.info("Cargá al menos un estudiante y una oferta.")
    else:
        est = st.selectbox(
            "Estudiante",
            estudiantes,
            format_func=lambda e: f"{e['id']} - {e['nombre']}",
            key="comp_estudiante",
        )
        ofe = st.selectbox(
            "Oferta",
            ofertas,
            format_func=lambda o: f"{o['id']} - {o['titulo']} ({o['empresa']})",
            key="comp_oferta",
        )
        if st.button("Calcular compatibilidad"):
            res, error = llamar_api(
                "POST",
                "/compatibilidad",
                json={"estudiante_id": est["id"], "oferta_id": ofe["id"]},
            )
            if error:
                st.error(error)
            else:
                st.metric("Score de compatibilidad", f"{res['score']} / 100")
                st.progress(int(res["score"]))
                if res["competencias_faltantes"]:
                    st.warning("Competencias faltantes: " + ", ".join(res["competencias_faltantes"]))
                else:
                    st.success("Cumple todos los requisitos")
                st.caption(f"Origen del resultado: {res['origen']}")

# ---------------- RESULTADOS ----------------
with tab_res:
    st.subheader("Resultados guardados")
    resultados, error = llamar_api("GET", "/resultados")
    if error:
        st.error(error)
    elif resultados:
        st.dataframe(resultados, use_container_width=True)
    else:
        st.info("Todavía no se calculó ninguna compatibilidad.")