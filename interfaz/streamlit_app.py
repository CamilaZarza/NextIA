import os

import requests
import streamlit as st

API_URL = os.getenv("NEXTIA_API_URL", "http://127.0.0.1:8000")
N8N_URL = os.getenv("NEXTIA_N8N_URL", "http://127.0.0.1:5678/webhook")

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


def llamar_webhook(ruta: str, datos: dict | None = None, **kwargs):
    """Llama a un webhook de n8n. Devuelve (datos, error)."""
    if datos is None:
        datos = kwargs.get("json", {})
    try:
        respuesta = requests.post(
            f"{N8N_URL}/{ruta}",
            json=datos,
            timeout=30,
        )
    except requests.exceptions.ConnectionError:
        return None, "No se pudo conectar con n8n. Verificá que esté publicado y activo."
    except requests.exceptions.Timeout:
        return None, "n8n tardó demasiado en responder."

    try:
        contenido = respuesta.json()
    except ValueError:
        contenido = {"error": respuesta.text}

    if respuesta.status_code >= 400:
        detalle = contenido.get("detail") or contenido.get("error") or contenido.get("message")
        return None, f"Error {respuesta.status_code}: {detalle or 'Error desconocido'}"
    return contenido, None


def a_lista(texto: str) -> list[str]:
    """'python, git , excel' -> ['python', 'git', 'excel']"""
    return [c.strip() for c in texto.split(",") if c.strip()]


st.title("🎯 Nextia")
st.caption("Plataforma de vinculación y desarrollo profesional")

tab_est, tab_ofe, tab_comp, tab_res, tab_rec = st.tabs(
    ["Estudiantes", "Ofertas", "Compatibilidad", "Resultados", "Recomendaciones IA"]
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
        datos, error = llamar_webhook(
            "registrar-estudiante",
            json={"nombre": nombre, "carrera": carrera, "competencias": a_lista(competencias)},
        )
        if error:
            st.error(error)
        else:
            estudiante = datos.get("estudiante", datos)
            if isinstance(estudiante, dict) and estudiante.get("id") is not None:
                st.success(f"Estudiante creado con id {estudiante['id']}")
            else:
                st.warning("Estudiante registrado correctamente. La respuesta llegó sin el objeto de detalle.")
            st.caption("Proceso automático: n8n → FastAPI → persistencia JSON")

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
        datos, error = llamar_webhook(
            "registrar-oferta",
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
            oferta = datos.get("oferta", datos)
            if isinstance(oferta, dict) and oferta.get("id") is not None:
                st.success(f"Oferta creada con id {oferta['id']}")
            else:
                st.warning("Oferta registrada correctamente. La respuesta llegó sin el objeto de detalle.")
            st.caption("Proceso automático: n8n → FastAPI → persistencia JSON")

    st.subheader("Ofertas registradas")
    ofertas, error = llamar_api("GET", "/ofertas")
    if error:
        st.error(error)
    elif ofertas:
        st.dataframe(ofertas, use_container_width=True)

        st.subheader("Modificar una oferta")
        elegida = st.selectbox(
            "Elegí una oferta",
            ofertas,
            format_func=lambda o: f"{o['id']} - {o['titulo']} ({o['empresa']})",
            key="editar_oferta",
        )
        with st.form("form_editar_oferta"):
            nuevo_titulo = st.text_input("Título del puesto", value=elegida["titulo"], key=f"tit_{elegida['id']}")
            nueva_empresa = st.text_input("Empresa", value=elegida["empresa"], key=f"emp_{elegida['id']}")
            nuevos_obl = st.text_input(
                "Requisitos obligatorios (coma)",
                value=", ".join(elegida["requisitos_obligatorios"]),
                key=f"obl_{elegida['id']}",
            )
            nuevos_des = st.text_input(
                "Requisitos deseables (coma)",
                value=", ".join(elegida["requisitos_deseables"]),
                key=f"des_{elegida['id']}",
            )
            actualizar_oferta = st.form_submit_button("Actualizar")
        if actualizar_oferta:
            cambios = {
                "titulo": nuevo_titulo,
                "empresa": nueva_empresa,
                "requisitos_obligatorios": a_lista(nuevos_obl),
                "requisitos_deseables": a_lista(nuevos_des),
            }
            datos, error = llamar_api("PUT", f"/ofertas/{elegida['id']}", json=cambios)
            if error:
                st.error(error)
            else:
                st.success("Oferta actualizada (la tabla se refresca en la próxima acción)")
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
            res, error = llamar_webhook(
                "calcular-compatibilidad",
                json={"estudiante_id": est["id"], "oferta_id": ofe["id"]},
            )
            if error:
                st.error(error)
            else:
                resultado = res.get("resultado", res)
                st.session_state["ultimo_resultado"] = resultado
                st.metric("Score de compatibilidad", f"{resultado['score']} / 100")
                st.progress(int(resultado["score"]))
                if resultado["competencias_faltantes"]:
                    st.warning("Competencias faltantes: " + ", ".join(resultado["competencias_faltantes"]))
                else:
                    st.success("Cumple todos los requisitos")
                st.caption(f"Origen del resultado: {resultado['origen']}")
                st.caption("Cálculo automático: n8n → FastAPI → reglas Python")

# ---------------- RESULTADOS ----------------
with tab_res:
    st.subheader("Resultados guardados")
    resultados, error = llamar_api("GET", "/resultados")
    if error:
        st.error(error)
    elif resultados:
        st.dataframe(resultados, use_container_width=True)

        resultado_elegido = st.selectbox(
            "Resultado para generar recomendación",
            resultados,
            format_func=lambda r: (
                f"#{r['id']} - {r['estudiante']} / {r['oferta']} ({r['score']} puntos)"
            ),
            key="resultado_ia",
        )

        if st.button("Generar recomendación con IA"):
            datos, error_ia = llamar_webhook(
                "generar-recomendacion",
                {"resultado_id": resultado_elegido["id"]},
            )
            if error_ia:
                st.error(error_ia)
            else:
                st.success("Recomendación generada mediante n8n + Google Gemini")
                recomendacion = datos.get("resultado", datos)
                if isinstance(recomendacion, dict):
                    texto = recomendacion.get("texto", "")
                else:
                    texto = str(recomendacion)
                if texto and texto != "={{ $json }}":
                    st.write(texto)
                else:
                    recomendaciones, error_rec = llamar_api(
                        "GET",
                        "/recomendaciones",
                        params={"resultado_id": resultado_elegido["id"]},
                    )
                    if error_rec:
                        st.error(error_rec)
                    elif recomendaciones:
                        st.write(recomendaciones[-1]["texto"])
                st.caption(
                    "Origen: Google Gemini vía n8n · Recomendación automatizada: requiere revisión humana."
                )
    else:
        st.info("Todavía no se calculó ninguna compatibilidad.")

# ---------------- RECOMENDACIONES IA ----------------
with tab_rec:
    st.subheader("Historial de recomendaciones generadas por IA")
    recomendaciones, error = llamar_api("GET", "/recomendaciones")
    if error:
        st.error(error)
    elif recomendaciones:
        ids_resultado = sorted({r["resultado_id"] for r in recomendaciones})
        filtro = st.selectbox(
            "Filtrar por resultado",
            ["Todos", *ids_resultado],
            format_func=lambda x: x if x == "Todos" else f"Resultado #{x}",
            key="filtro_rec_resultado",
        )
        if filtro != "Todos":
            recomendaciones = [r for r in recomendaciones if r["resultado_id"] == filtro]

        st.caption(f"{len(recomendaciones)} recomendación(es)")
        for rec in reversed(recomendaciones):  # las más nuevas primero
            with st.expander(f"#{rec['id']} · Resultado #{rec['resultado_id']} · modelo {rec['modelo']}"):
                st.write(rec["texto"])
                st.caption(f"Origen: {rec['origen']}")
    else:
        st.info("Todavía no se generó ninguna recomendación.")