# Arquitectura de Nextia

## 1. Diagrama general

```mermaid
flowchart LR
    U(["Usuario"])

    subgraph HOST["Equipo anfitrión"]
        ST["Streamlit<br/>interfaz/streamlit_app.py<br/>:8501"]
        subgraph API["FastAPI · app/ · :8000"]
            MAIN["main.py<br/>endpoints"]
            MOD["modelos.py<br/>validación Pydantic"]
            SC["scoring.py<br/>reglas de compatibilidad"]
            ALM["almacenamiento.py"]
        end
        DATA[("data/*.json<br/>estudiantes · ofertas<br/>resultados · recomendaciones")]
    end

    subgraph DOCKER["Docker · n8n/compose.yaml"]
        N8N["n8n :5678<br/>4 workflows"]
        VOL[("volumen n8n_data")]
    end

    GEM["Google Gemini<br/>gemini-3.5-flash-lite"]

    U -- navegador --> ST
    ST -- "POST /webhook/* (altas, compatibilidad, IA)" --> N8N
    ST -- "GET / PUT (consultas, modificaciones, revisión)" --> MAIN
    N8N -- "HTTP JSON vía host.docker.internal:8000" --> MAIN
    N8N -- "HTTPS (credencial en n8n)" --> GEM
    N8N --- VOL
    MAIN --> MOD
    MAIN --> SC
    MAIN --> ALM
    ALM <--> DATA
```

**Separación de responsabilidades**

- **Streamlit** solo muestra y envía datos. No calcula nada.
- **n8n** orquesta los procesos automáticos: valida la entrada con nodos `IF`, llama a la API y a la IA, y responde con el código HTTP correspondiente.
- **FastAPI** es la única puerta a los datos. Valida con Pydantic, aplica las reglas de `scoring.py` y persiste en JSON.
- **Gemini** solo redacta recomendaciones a partir de resultados ya calculados. Sus respuestas quedan `pendiente` hasta que una persona las revisa.

## 2. Puertos y servicios

| Servicio | Dónde corre | Puerto | URL |
|---|---|---|---|
| Streamlit | Equipo anfitrión (venv) | 8501 | http://localhost:8501 |
| FastAPI | Equipo anfitrión (venv) | 8000 | http://127.0.0.1:8000 · Swagger en `/docs` |
| n8n | Contenedor Docker `nextia-n8n` | 5678 → 5678 | http://localhost:5678 |
| Gemini | Servicio externo de Google | 443 (HTTPS) | Configurado como credencial en n8n |

- n8n corre dentro de Docker, así que no puede usar `127.0.0.1` para llegar a la API: ese sería el propio contenedor. Por eso los workflows usan `http://host.docker.internal:8000`, y `compose.yaml` define `extra_hosts: host.docker.internal:host-gateway` para que ese nombre resuelva al equipo anfitrión.
- Para que la API acepte conexiones que vienen del contenedor, conviene iniciarla con `--host 0.0.0.0`.
- La configuración y los workflows de n8n se guardan en el volumen `n8n_data`, así que sobreviven a `docker compose down`.
- La interfaz permite cambiar las URLs de la API y de n8n con las variables `NEXTIA_API_URL` y `NEXTIA_N8N_URL`.

## 3. Comunicación entre componentes

| Origen | Destino | Operación | Para qué |
|---|---|---|---|
| Streamlit | n8n | `POST /webhook/registrar-estudiante` | Alta de estudiante |
| Streamlit | n8n | `POST /webhook/registrar-oferta` | Alta de oferta |
| Streamlit | n8n | `POST /webhook/calcular-compatibilidad` | Calcular score |
| Streamlit | n8n | `POST /webhook/generar-recomendacion` | Recomendación con IA |
| Streamlit | FastAPI | `GET /estudiantes`, `GET /ofertas`, `GET /resultados`, `GET /recomendaciones` | Listados |
| Streamlit | FastAPI | `PUT /estudiantes/{id}`, `PUT /ofertas/{id}` | Modificaciones |
| Streamlit | FastAPI | `PUT /recomendaciones/{id}/revision` | Revisión humana |
| n8n | FastAPI | `POST /estudiantes`, `POST /ofertas` | Persistir altas validadas |
| n8n | FastAPI | `POST /compatibilidad` | Calcular y guardar resultado |
| n8n | FastAPI | `GET /resultados`, `POST /recomendaciones` | Leer resultado y guardar la recomendación |
| n8n | Gemini | Basic LLM Chain | Generar el texto de la recomendación |
| FastAPI | `data/*.json` | `almacenamiento.leer()` / `guardar()` | Persistencia |

Todo el intercambio es **JSON sobre HTTP**.

## 4. Recorrido del proceso principal

```mermaid
sequenceDiagram
    actor U as Usuario
    participant ST as Streamlit
    participant N as n8n
    participant API as FastAPI
    participant D as data/*.json
    participant G as Gemini

    U->>ST: Carga estudiante y oferta
    ST->>N: POST /webhook/registrar-estudiante · registrar-oferta
    N->>N: IF: ¿datos completos? (si no → 400)
    N->>API: POST /estudiantes · /ofertas
    API->>D: guardar

    U->>ST: Elige estudiante y oferta
    ST->>N: POST /webhook/calcular-compatibilidad
    N->>N: IF: ¿vienen los dos IDs? (si no → 400)
    N->>API: POST /compatibilidad
    API->>API: scoring.py (70 % obligatorios + 30 % deseables)
    API->>D: guardar resultado (origen: reglas de Python)
    API-->>ST: score y competencias faltantes

    U->>ST: Generar recomendación
    ST->>N: POST /webhook/generar-recomendacion
    N->>API: GET /resultados
    N->>N: IF: ¿existe el resultado? (si no → 404)
    N->>G: score + competencias faltantes
    G-->>N: texto de la recomendación
    N->>API: POST /recomendaciones
    API->>D: guardar (estado: pendiente)

    U->>ST: Aprueba o rechaza
    ST->>API: PUT /recomendaciones/{id}/revision
    API->>D: guardar estado, revisor y fecha
```
