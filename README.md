# Nextia
 
Plataforma de vinculación y desarrollo profesional entre estudiantes, graduados y organizaciones que ofrecen oportunidades laborales.

---
## 1. Objetivo
 
Nextia permite registrar perfiles de estudiantes (con sus competencias) y ofertas laborales (con sus requisitos), y **calcular un indicador de compatibilidad (scoring)** entre ambos mediante reglas explícitas programadas en Python. Además, identifica las **competencias que le faltan** al estudiante para cada oferta.

- **Resultados calculados por reglas de programación** (scoring y competencias faltantes), que llevan la etiqueta `calculado con reglas de Python`.
- **Recomendaciones generadas por IA**, que se almacenan con la etiqueta `generado por IA (requiere revisión humana)`.

---

## 2. Componentes
 
| Componente | Tecnología | Responsabilidad |
|---|---|---|
| Interfaz | Streamlit | Formularios, tablas y visualización de resultados. No calcula nada: solo consulta a la API. |
| API | FastAPI | Valida datos, aplica la lógica de negocio, guarda y consulta información. |
| Lógica | Python | Cálculo del scoring y detección de competencias faltantes. |
| Persistencia | Archivos JSON | Almacenamiento de estudiantes, ofertas, resultados y recomendaciones. |
| Automatización | n8n | Webhooks, validaciones, llamadas a FastAPI y generación de recomendaciones con IA. |
| IA | Google Gemini | Genera recomendaciones a partir de los resultados calculados por Nextia. |

---

### Flujo de datos
 
```
Streamlit  ──(JSON / HTTP)──▶  FastAPI  ──▶  scoring.py (reglas)
 (interfaz)                       │
                                  ▼
                           data/*.json (persistencia)

n8n ──(webhook / HTTP)──▶ FastAPI ──▶ data/*.json
```

## 3. Workflows de n8n

El proyecto incluye cuatro workflows exportados o disponibles en la carpeta `n8n/`:

| Workflow | Archivo | Responsabilidad | Decisión |
|---|---|---|---|
| Alta automatizada de estudiantes | `n8n/alta-estudiantes.json` | Recibe los datos de un estudiante y los registra mediante FastAPI. | Valida que nombre, carrera y competencias estén presentes. |
| Compatibilidad automática | `n8n/compatibilidad-automatica.json` | Recibe un estudiante y una oferta, calcula su compatibilidad y guarda el resultado. | Valida que ambos IDs estén presentes. |
| Recomendaciones con IA | `n8n/recomendaciones-ia.json` | Obtiene un resultado, consulta Gemini y guarda una recomendación en la API. | Verifica que el resultado solicitado exista. |
| Alta automatizada de ofertas | `n8n/alta-ofertas.json` | Recibe los datos de una oferta y los registra mediante FastAPI. | Valida que título, empresa y requisitos obligatorios estén presentes. |

Todos los workflows pueden comunicarse con FastAPI mediante `http://host.docker.internal:8000`, que permite al contenedor de n8n acceder al servicio ejecutado en el equipo anfitrión.

Los workflows incluidos tienen respuestas HTTP 400 o 404 para solicitudes inválidas y deben exportarse/importarse nuevamente si se realizan cambios posteriores en n8n.

### 3.1 Iniciar n8n

Desde la raíz del proyecto:

```powershell
docker compose -f n8n/compose.yaml up -d
```

n8n queda disponible en:

```text
http://localhost:5678
```

Para importar los workflows:

1. Abrir n8n en el navegador.
2. Seleccionar **Workflows > Import from File**.
3. Importar cada archivo de la carpeta `n8n/`.
4. Guardar y activar el workflow correspondiente.
5. Configurar las credenciales necesarias para el workflow de recomendaciones.

Los archivos exportados están configurados como activos (`active: true`). Igualmente, deben activarse desde la interfaz de n8n si esta muestra el workflow como inactivo después de importarlo o reiniciar el entorno.

### 3.2 Alta automatizada de estudiantes

Webhook configurado como:

```text
POST /webhook/registrar-estudiante
```

Ejemplo de solicitud:

```json
{
  "nombre": "Ana López",
  "carrera": "Analista de Sistemas",
  "competencias": ["python", "sql", "git"]
}
```

El nodo `IF` rechaza solicitudes incompletas. Si los datos son válidos, n8n llama a `POST /estudiantes` y devuelve al cliente el estudiante creado por FastAPI.

Prueba desde PowerShell:

```powershell
$body = @{
  nombre = "Ana López"
  carrera = "Analista de Sistemas"
  competencias = @("python", "sql", "git")
} | ConvertTo-Json

Invoke-RestMethod `
  -Uri "http://localhost:5678/webhook/registrar-estudiante" `
  -Method Post `
  -ContentType "application/json" `
  -Body $body
```

### 3.3 Compatibilidad automática

Webhook configurado como:

```text
POST /webhook/calcular-compatibilidad
```

Ejemplo de solicitud:

```json
{
  "estudiante_id": 1,
  "oferta_id": 1
}
```

El workflow llama a `POST /compatibilidad`. FastAPI calcula el score, identifica las competencias faltantes y guarda el resultado.

Prueba desde PowerShell:

```powershell
$body = @{
  estudiante_id = 1
  oferta_id = 1
} | ConvertTo-Json

Invoke-RestMethod `
  -Uri "http://localhost:5678/webhook/calcular-compatibilidad" `
  -Method Post `
  -ContentType "application/json" `
  -Body $body
```

### 3.4 Recomendaciones con IA

Webhook configurado como:

```text
POST /webhook/generar-recomendacion
```

Ejemplo de solicitud:

```json
{
  "resultado_id": 9
}
```

El workflow obtiene el resultado mediante `GET /resultados/{id}`. Un nodo `IF` verifica que el resultado exista; en ese caso, la rama verdadera envía el score y las competencias faltantes a Google Gemini mediante un `Basic LLM Chain`. La respuesta generada se guarda con `POST /recomendaciones` y `modelo: "gemini"`.

Prueba desde PowerShell:

```powershell
$body = @{
  resultado_id = 9
} | ConvertTo-Json

Invoke-RestMethod `
  -Uri "http://localhost:5678/webhook/generar-recomendacion" `
  -Method Post `
  -ContentType "application/json" `
  -Body $body
```

La recomendación se identifica en la API como `generado por IA (requiere revisión humana)`. El proyecto no guarda la API key dentro de los archivos exportados; debe configurarse como credencial privada en n8n.

### 3.5 Alta automatizada de ofertas

Webhook configurado como:

```text
POST /webhook/registrar-oferta
```

Ejemplo de solicitud:

```json
{
  "titulo": "Desarrollador Junior",
  "empresa": "Empresa NextIA",
  "requisitos_obligatorios": ["python", "sql"],
  "requisitos_deseables": ["git", "docker"]
}
```

El flujo utiliza los siguientes nodos:

```text
Webhook
  → IF
  ├─ True → HTTP Request: POST /ofertas → Respond to Webhook
  └─ False → Respond to Webhook con error 400
```

El nodo `IF` verifica que `titulo`, `empresa` y `requisitos_obligatorios` estén presentes y que la lista de requisitos obligatorios no esté vacía.

En la rama verdadera, n8n llama a `POST /ofertas` mediante:

```text
http://host.docker.internal:8000/ofertas
```

Prueba desde PowerShell:

```powershell
$body = @{
  titulo = "Desarrollador Junior"
  empresa = "Empresa NextIA"
  requisitos_obligatorios = @("python", "sql")
  requisitos_deseables = @("git", "docker")
} | ConvertTo-Json

Invoke-RestMethod `
  -Uri "http://localhost:5678/webhook/registrar-oferta" `
  -Method Post `
  -ContentType "application/json" `
  -Body $body
```

Si la solicitud tiene datos incompletos, el workflow responde con estado `400` y el mensaje:

```json
{
  "error": "Debes enviar titulo, empresa y al menos un requisito obligatorio"
}
```

## 4. Requisitos
 
- Python 3.10 o superior
- Git
- Librerías: `fastapi`, `uvicorn`, `streamlit`, `requests` (ver `requirements.txt`)
## 5. Instalación
 
```bash
# 1. Clonar el repositorio
git clone <URL_DEL_REPOSITORIO>
cd nextia
 
# 2. Crear y activar el entorno virtual
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Mac / Linux:
source .venv/bin/activate
 
# 3. Instalar dependencias
pip install -r requirements.txt
```
 
## 6. Ejecución
 
Se necesitan **tres terminales abiertas desde la raíz del proyecto**.
 
### Terminal 1: API FastAPI
 
```bash
# Activar el entorno virtual solo en Windows PowerShell
.\.venv\Scripts\Activate.ps1

python -m uvicorn app.main:app --reload
```
 
- API: http://127.0.0.1:8000
- Documentación interactiva (Swagger): http://127.0.0.1:8000/docs

### Terminal 2: interfaz Streamlit

```bash
# Activar el entorno virtual solo en Windows PowerShell
.\.venv\Scripts\Activate.ps1

python -m streamlit run interfaz/streamlit_app.py
```

- Interfaz: http://localhost:8501

Por defecto la interfaz busca la API en `http://127.0.0.1:8000` y n8n en `http://127.0.0.1:5678/webhook`. Si alguno corre en otro puerto, se puede cambiar con variables de entorno antes de iniciar Streamlit:

```powershell
$env:NEXTIA_API_URL = "http://127.0.0.1:8001"
$env:NEXTIA_N8N_URL = "http://127.0.0.1:5678/webhook"
```

### Terminal 3: n8n con Docker

```bash
docker compose -f n8n/compose.yaml up -d
```

- n8n: http://localhost:5678

Comandos útiles:
  
```bash
# Detener n8n
docker compose -f n8n/compose.yaml down

# Reiniciar n8n
docker compose -f n8n/compose.yaml restart

# Consultar el estado de los contenedores
docker compose -f n8n/compose.yaml ps
```
 
Para detener FastAPI o Streamlit, presionar `Ctrl + C` en la terminal correspondiente. Para detener n8n, utilizar el comando `docker compose -f n8n/compose.yaml down`.
 
> Si la API debe ser accesible desde otro equipo o contenedor de la red local, iniciarla con `--host 0.0.0.0`.
 
## 7. Funcionalidades principales
 
La interfaz tiene cinco pestañas:
 
1. **Estudiantes**: alta de perfiles, listado y modificación de competencias.
2. **Ofertas**: alta de ofertas con requisitos obligatorios y deseables, listado y modificación.
3. **Compatibilidad**: se elige un estudiante y una oferta y se calcula el score, con barra de progreso y competencias faltantes.
4. **Resultados**: historial de compatibilidades calculadas y generación de recomendaciones con IA.
5. **Recomendaciones IA**: historial de recomendaciones generadas, con filtros por resultado y por estado, y **revisión humana**: cada recomendación nace `pendiente` y una persona la aprueba o la rechaza dejando su nombre y un comentario.
### Cómo se calcula el score
 
El puntaje va de 0 a 100 y se compone de dos partes:
 
| Criterio | Puntos máximos | Cálculo |
|---|---|---|
| Requisitos obligatorios | 70 | `70 × (obligatorios cumplidos / obligatorios totales)` |
| Requisitos deseables | 30 | `30 × (deseables cumplidos / deseables totales)` |
 
- Las competencias se comparan sin distinguir mayúsculas ni espacios sobrantes (`"Python "` equivale a `"python"`).
- Si la oferta no tiene requisitos deseables, se otorgan los 30 puntos completos.
- Una oferta sin requisitos obligatorios se rechaza con error.
- Se informan las competencias faltantes, diferenciando las obligatorias.
**Ejemplo:** estudiante con `Python, Git, Excel` frente a una oferta que exige `python, sql, excel` (obligatorios) y `power bi, git` (deseables):
 
- Obligatorios: 2 de 3 → 46,7 puntos
- Deseables: 1 de 2 → 15 puntos
- **Score: 61,7** · Faltantes: `power bi`, `sql`
## 8. Endpoints de la API
 
| Método | Ruta | Descripción | Respuestas |
|---|---|---|---|
| GET | `/status` | Verifica que la API esté activa | 200 |
| POST | `/estudiantes` | Registra un estudiante | 201, 422 |
| GET | `/estudiantes` | Lista los estudiantes | 200 |
| PUT | `/estudiantes/{id}` | Modifica un estudiante | 200, 404, 422 |
| POST | `/ofertas` | Registra una oferta | 201, 422 |
| GET | `/ofertas` | Lista las ofertas | 200 |
| PUT | `/ofertas/{id}` | Modifica una oferta | 200, 404, 422 |
| POST | `/compatibilidad` | Calcula y guarda el scoring de un estudiante frente a una oferta | 201, 400, 404, 422 |
| GET | `/resultados` | Lista los resultados (filtro opcional `?estudiante_id=`) | 200 |
| GET | `/resultados/{id}` | Obtiene un resultado puntual | 200, 404 |
| POST | `/recomendaciones` | Guarda una recomendación asociada a un resultado (queda `pendiente`) | 201, 404, 422 |
| GET | `/recomendaciones` | Lista recomendaciones (filtros opcionales `?resultado_id=` y `?estado=`) | 200 |
| PUT | `/recomendaciones/{id}/revision` | Una persona aprueba o rechaza la recomendación | 200, 404, 422 |

## 9. Integración de inteligencia artificial en el sistema

### Qué hace la IA

El workflow **Recomendaciones IA** toma un resultado ya calculado por las reglas de Python (score y competencias faltantes) y le pide a un modelo de lenguaje una **recomendación de formación**: si conviene postularse y qué acciones concretas tomar para cubrir las competencias faltantes. La IA no calcula el score ni decide nada: interpreta un resultado determinista y lo traduce a una sugerencia en lenguaje natural.

### Modelo elegido: Google Gemini (`gemini-3.5-flash-lite`)

Se usa a través de los nodos de n8n **Basic LLM Chain** + **Google Gemini Chat Model**.

| Criterio | Por qué Gemini |
|---|---|
| Costo | Tiene cuota gratuita con una API key de Google AI Studio, sin tarjeta. Cumple el requisito de no exigir pagos. |
| Integración | n8n trae un nodo nativo: no hay que programar un cliente HTTP ni manejar el formato de la API. |
| Hardware | Corre en la nube: no exige GPU ni descargar modelos de varios GB, como pasaría con Ollama en las computadoras del grupo. |
| Idioma | Genera texto en español de buena calidad. |
| Variante *flash-lite* | Es la más rápida y liviana. Alcanza para textos cortos y rinde más dentro de la cuota gratuita. |

Alternativa: **Ollama con un modelo local** (por ejemplo Llama o Mistral). Tiene la ventaja de que los datos no salen de la máquina y funciona sin internet, pero necesita más hardware y responde más lento. Como el sistema usa datos ficticios, se priorizó la simplicidad de Gemini.

### Límites conocidos

- **Cuota gratuita limitada**: tiene un máximo de solicitudes por minuto y por día. Si se supera, el workflow falla y la interfaz muestra el error. El resto del sistema sigue funcionando.
- **Depende de internet y de una credencial**: sin conexión o sin API key configurada en n8n no se generan recomendaciones.
- **Privacidad**: los datos se envían a Google y, en el plan gratuito, pueden usarse para mejorar sus servicios. Por eso **solo se usan datos ficticios**.
- **No es determinista**: el mismo resultado puede dar textos distintos en cada ejecución.
- **Puede equivocarse o inventar**: en las pruebas, las recomendaciones 9, 10 y 11 de `data/recomendaciones.json` están asociadas al resultado 1, pero el texto generado habla del "Resultado ID 12". Por eso ninguna recomendación se da por válida sin revisión humana.

### Validación y supervisión humana

1. **Prompt acotado**: se le pasan solo el score y las competencias faltantes, con la instrucción explícita de no inventar información.
2. **Validación previa en n8n**: un nodo `IF` verifica que el resultado exista antes de llamar a la IA, así no se gasta cuota en pedidos inválidos.
3. **Validación en la API**: `POST /recomendaciones` exige que el resultado exista y rechaza textos vacíos o expresiones de n8n sin evaluar (respuesta 422).
4. **Origen identificado**: los resultados llevan `calculado con reglas de Python` y las recomendaciones `generado por IA (requiere revisión humana)`.
5. **Revisión humana obligatoria**: cada recomendación nace `pendiente`. Una persona la aprueba o la rechaza desde la pestaña **Recomendaciones IA**, y queda registrado quién la revisó, cuándo y con qué comentario (`PUT /recomendaciones/{id}/revision`).
6. **Independencia**: el scoring no depende de la IA. Si Gemini no está disponible, el registro, el cálculo de compatibilidad y la consulta de resultados siguen funcionando.

## 10. Uso de inteligencia artificial en el desarrollo

Durante el desarrollo se utilizó GitHub Copilot como herramienta de asistencia para completar tareas técnicas, siempre con revisión, prueba y corrección por parte del grupo. Las principales aplicaciones fueron:

| Uso | Cómo colaboró la IA | Verificación realizada |
|---|---|---|
| Validación de errores en workflows de n8n | Ayudó a revisar la configuración de los nodos, las conexiones entre pasos y la detección de errores en las validaciones y respuestas HTTP. | Se importaron los workflows, se probaron rutas válidas y inválidas y se verificaron las respuestas del sistema. |
| Elaboración de la interfaz con Streamlit | Apoyó en la organización de pestañas, formularios, tablas, mensajes de estado y la comunicación con FastAPI y n8n. | Se probaron manualmente los formularios, las llamadas HTTP, la actualización de datos y los casos de error desde la interfaz. |

La IA no reemplazó la decisión ni la responsabilidad del grupo sobre el funcionamiento final. Cada cambio fue probado, ajustado y integrado al proyecto antes de considerarlo correcto. Además, la IA integrada al sistema mediante Gemini genera recomendaciones de formación; el scoring corresponde a una lógica determinista desarrollada en Python y puede funcionar independientemente.
 
