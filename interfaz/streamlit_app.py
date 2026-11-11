import os

import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
N8N_URL = os.getenv("N8N_URL", "http://127.0.0.1:5678/webhook")

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
    st.subheader("📊 Resultados y Recomendaciones con IA")
    resultados, error = llamar_api("GET", "/resultados")
    if error:
        st.error(error)
    elif resultados:
        subtab_analisis, subtab_tablas = st.tabs(
            ["✨ Asistente y Diagnóstico IA", "📋 Historial y Auditoría de Datos"]
        )

        with subtab_analisis:
            st.markdown(
                "Seleccioná una postulación para revisar el diagnóstico técnico y consultar o generar recomendaciones personalizadas con IA:"
            )

            # Ordenar para mostrar los más recientes arriba
            resultados_inversos = list(reversed(resultados))
            resultado_elegido = st.selectbox(
                "Postulación evaluada:",
                resultados_inversos,
                format_func=lambda r: (
                    f"#{r['id']} · {r['estudiante']}  ➔  {r['oferta']}  ({r['score']} pts)"
                ),
                key="resultado_ia",
            )

            col_diag, col_ia = st.columns([1, 1], gap="large")

            with col_diag:
                with st.container(border=True):
                    st.markdown("#### 📐 Diagnóstico de Compatibilidad")
                    st.caption("Calculado de forma determinista mediante reglas de Python")

                    score = float(resultado_elegido["score"])
                    if score >= 70:
                        st.success(f"**Score de afinidad:** {score} / 100 — Alto match")
                    elif score >= 40:
                        st.warning(f"**Score de afinidad:** {score} / 100 — Match intermedio")
                    else:
                        st.error(f"**Score de afinidad:** {score} / 100 — Brecha formativa alta")

                    st.progress(min(int(score), 100))

                    st.markdown("##### 📌 Brechas detectadas")
                    faltantes_obl = resultado_elegido.get("faltantes_obligatorias", [])
                    todas_faltantes = resultado_elegido.get("competencias_faltantes", [])
                    faltantes_des = [c for c in todas_faltantes if c not in faltantes_obl]

                    if faltantes_obl:
                        st.markdown(f"🔴 **Obligatorias:** `{'`, `'.join(faltantes_obl)}`")
                    if faltantes_des:
                        st.markdown(f"🟡 **Deseables:** `{'`, `'.join(faltantes_des)}`")
                    if not todas_faltantes:
                        st.success("✅ Cumple todos los requisitos.")

                    st.caption(f"🏷️ Origen: `{resultado_elegido.get('origen', 'calculado con reglas de Python')}`")

            with col_ia:
                with st.container(border=True):
                    st.markdown("#### 🤖 Plan de Mejora con IA")
                    st.caption("Generado por Google Gemini vía n8n")

                    recs, error_rec = llamar_api(
                        "GET",
                        "/recomendaciones",
                        params={"resultado_id": resultado_elegido["id"]},
                    )

                    if recs:
                        if len(recs) > 1:
                            indice_rec = st.selectbox(
                                "Versión de la recomendación:",
                                range(len(recs)),
                                format_func=lambda i: f"Versión #{i+1} (ID #{recs[i]['id']})",
                                index=len(recs) - 1,
                                key=f"sel_rec_{resultado_elegido['id']}",
                            )
                            rec_activa = recs[indice_rec]
                        else:
                            rec_activa = recs[0]

                        st.info(rec_activa["texto"])
                        st.caption(
                            f"✨ Modelo: `{rec_activa.get('modelo', 'gemini')}` · ⚠️ `{rec_activa.get('origen', 'requiere revisión humana')}`"
                            f" · Revisión: `{rec_activa['estado']}`"
                        )
                        if rec_activa["estado"] == "pendiente":
                            st.caption("Aprobala o rechazala desde la pestaña **Recomendaciones IA**.")
                    else:
                        st.info("ℹ️ Todavía no se ha generado una recomendación para esta postulación.")

                    if st.button("⚡ Generar nueva recomendación con IA", type="primary", use_container_width=True):
                        with st.spinner("Consultando a Google Gemini vía n8n..."):
                            datos, error_ia = llamar_webhook(
                                "generar-recomendacion",
                                {"resultado_id": resultado_elegido["id"]},
                            )
                        if error_ia:
                            st.error(error_ia)
                        else:
                            st.success("¡Recomendación generada y guardada con éxito!")
                            st.rerun()

        with subtab_tablas:
            st.markdown("#### 📊 Historial completo de compatibilidades")
            st.dataframe(resultados, use_container_width=True)

            st.divider()
            st.markdown("#### 📝 Auditoría general de recomendaciones con IA")
            todas_recs, error_todas = llamar_api("GET", "/recomendaciones")
            if error_todas:
                st.error(error_todas)
            elif todas_recs:
                st.dataframe(todas_recs, use_container_width=True)
            else:
                st.info("No hay recomendaciones en la base de datos.")
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

        filtro_estado = st.radio(
            "Estado de revisión",
            ["todas", "pendiente", "aprobada", "rechazada"],
            horizontal=True,
            key="filtro_rec_estado",
        )
        if filtro_estado != "todas":
            recomendaciones = [r for r in recomendaciones if r["estado"] == filtro_estado]

        ICONOS = {"pendiente": "🕒", "aprobada": "✅", "rechazada": "❌"}
        st.caption(f"{len(recomendaciones)} recomendación(es)")
        for rec in reversed(recomendaciones):  # las más nuevas primero
            titulo_rec = (
                f"{ICONOS[rec['estado']]} #{rec['id']} · Resultado #{rec['resultado_id']} "
                f"· modelo {rec['modelo']} · {rec['estado']}"
            )
            with st.expander(titulo_rec):
                st.write(rec["texto"])
                st.caption(f"Origen: {rec['origen']}")

                if rec["estado"] != "pendiente":
                    st.info(
                        f"Revisada por {rec['revisor']} el {rec['fecha_revision']}"
                        + (f": {rec['comentario']}" if rec.get("comentario") else "")
                    )
                    continue

                # Supervisión humana: nada generado por IA se da por válido sin esta revisión
                with st.form(f"form_revision_{rec['id']}"):
                    revisor = st.text_input("Revisor/a", key=f"revisor_{rec['id']}")
                    comentario = st.text_input("Comentario (opcional)", key=f"coment_{rec['id']}")
                    col_ok, col_no = st.columns(2)
                    aprobar = col_ok.form_submit_button("Aprobar")
                    rechazar = col_no.form_submit_button("Rechazar")
                if aprobar or rechazar:
                    revision = {
                        "estado": "aprobada" if aprobar else "rechazada",
                        "revisor": revisor,
                        "comentario": comentario,
                    }
                    datos, error = llamar_api("PUT", f"/recomendaciones/{rec['id']}/revision", json=revision)
                    if error:
                        st.error(error)
                    else:
                        st.success(f"Recomendación {datos['estado']} (se refresca en la próxima acción)")
    else:
        st.info("Todavía no se generó ninguna recomendación.")