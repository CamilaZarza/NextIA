# Nextia

Plataforma de vinculación y desarrollo profesional entre estudiantes, graduados y organizaciones que ofrecen oportunidades laborales.

Nextia registra perfiles y ofertas, calcula su compatibilidad mediante reglas explícitas en Python y puede generar recomendaciones de formación con IA. El cálculo del score es determinista; las recomendaciones generadas por IA requieren revisión humana.

## Funcionalidades

- Registro y consulta de estudiantes, competencias y ofertas laborales.
- Cálculo del score de compatibilidad y detección de competencias faltantes.
- Consulta del diagnóstico técnico y del historial de compatibilidades.
- Generación y consulta de recomendaciones personalizadas mediante Google Gemini y n8n.
- Workflows de n8n para registrar estudiantes y ofertas, calcular compatibilidades y generar recomendaciones.

## Componentes y flujo de datos

| Componente | Tecnología | Responsabilidad |
|---|---|---|
| Interfaz | Streamlit | Formularios, diagnósticos, recomendaciones y tablas. Se comunica con FastAPI y con los webhooks de n8n. |
| API | FastAPI | Valida datos, aplica la lógica de negocio y guarda y consulta información. |
| Lógica | Python | Calcula el score y detecta competencias faltantes. |
| Persistencia | Archivos JSON | Almacena estudiantes, ofertas, resultados y recomendaciones en `data/`. |
| Automatización | n8n | Expone webhooks, llama a FastAPI y coordina la generación de recomendaciones. |
| IA | Google Gemini | Genera recomendaciones a partir de resultados calculados por Nextia. |

```text
Streamlit ──HTTP──▶ FastAPI ──▶ reglas de compatibilidad
    │                   │
    └──webhooks──▶ n8n ─┘
                        │
                        ▼
                   data/*.json
```

## Requisitos

Para ejecutar todo el sistema con Docker:

- Git
- Docker con Docker Compose

Para ejecutar FastAPI y Streamlit localmente:

- Python 3.10 o superior
- Git
- Dependencias de `requirements.txt`

## Instalación

Clona el repositorio y entra en su directorio:

```bash
git clone <URL_DEL_REPOSITORIO>
cd nextia
```

Para la ejecucion local, crea y activa un entorno virtual e instala las dependencias:

```powershell
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

En macOS o Linux, activa el entorno con:

```bash
source .venv/bin/activate
```

## Ejecución

### Opción 1: sistema completo con Docker Compose

Desde la raiz del proyecto, inicia FastAPI, Streamlit y n8n:

```bash
docker compose up -d
```

Accesos locales:

| Servicio | URL |
|---|---|
| Streamlit | http://localhost:8501 |
| FastAPI y documentacion Swagger | http://localhost:8000/docs |
| n8n | http://localhost:5678 |

En esta configuración, Streamlit accede a FastAPI mediante `http://api:8000` y a n8n mediante `http://n8n:5678/webhook`. n8n accede a FastAPI mediante `http://host.docker.internal:8000`. Los datos JSON se conservan en `data/` y n8n conserva su estado en un volumen de Docker.

Comandos utiles:

```bash
docker compose ps
docker compose logs -f
docker compose logs -f api
docker compose logs -f streamlit
docker compose logs -f n8n
docker compose restart
docker compose down
```

### Opción 2: desarrollo local con n8n en Docker

Inicia solamente n8n desde la raiz del proyecto:

```bash
docker compose -f n8n/compose.yaml up -d
```

En terminales separadas, activa el entorno virtual en cada terminal y ejecuta la API y la interfaz:

```powershell
# Terminal 1: API
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload
```

```powershell
# Terminal 2: Streamlit
.\.venv\Scripts\Activate.ps1
python -m streamlit run interfaz/streamlit_app.py
```

La API queda disponible en http://127.0.0.1:8000 y Streamlit en http://localhost:8501. La documentación de la API se encuentra en `/docs`.

En macOS o Linux, activa el entorno en cada terminal con `source .venv/bin/activate`.

## Workflows de n8n

Los cuatro workflows se encuentran en `n8n/`:

| Workflow | Archivo | Responsabilidad |
|---|---|---|
| Alta automatizada de estudiantes | `n8n/alta-estudiantes.json` | Valida y registra un estudiante mediante FastAPI. |
| Compatibilidad automática | `n8n/compatibilidad-automatica.json` | Valida los identificadores, calcula la compatibilidad y guarda el resultado. |
| Recomendaciones con IA | `n8n/recomendaciones-ia.json` | Obtiene un resultado, consulta Gemini y guarda la recomendación. |
| Alta automatizada de ofertas | `n8n/alta-ofertas.json` | Valida y registra una oferta mediante FastAPI. |

Para usarlos:

1. Inicia n8n con una de las opciones de ejecución anteriores.
2. Abre http://localhost:5678 y selecciona **Workflows > Import from File**.
3. Importa los archivos JSON desde `n8n/`.
4. Guarda y activa cada workflow. Si n8n lo muestra inactivo después de importarlo o reiniciarlo, actívalo desde la interfaz.
5. Configura en n8n las credenciales privadas requeridas por el workflow de recomendaciones. No se incluye una API key en los archivos exportados.

Los workflows llaman a FastAPI mediante `http://host.docker.internal:8000`. Devuelven errores HTTP 400 o 404 para solicitudes inválidas. Si modificas un workflow en n8n, vuelve a exportarlo para actualizar el archivo versionado.

### Registrar un estudiante

Webhook: `POST /webhook/registrar-estudiante`

```json
{
  "nombre": "Ana López",
  "carrera": "Analista de Sistemas",
  "competencias": ["python", "sql", "git"]
}
```

El workflow valida que nombre, carrera y competencias estén presentes. Si la solicitud es válida, llama a `POST /estudiantes` y devuelve el estudiante creado.

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

### Calcular compatibilidad

Webhook: `POST /webhook/calcular-compatibilidad`

```json
{
  "estudiante_id": 1,
  "oferta_id": 1
}
```

El workflow valida que ambos identificadores estén presentes y llama a `POST /compatibilidad`. FastAPI calcula el score, identifica las competencias faltantes y guarda el resultado.

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

### Generar una recomendación con IA

Webhook: `POST /webhook/generar-recomendacion`

```json
{
  "resultado_id": 9
}
```

El workflow obtiene el resultado mediante `GET /resultados/{id}` y verifica que exista. Luego envía el score y las competencias faltantes a Google Gemini mediante un `Basic LLM Chain` y guarda la respuesta con `POST /recomendaciones` y `modelo: "gemini"`.

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

La API identifica estas respuestas como `generado por IA (requiere revisión humana)`.

### Registrar una oferta

Webhook: `POST /webhook/registrar-oferta`

```json
{
  "titulo": "Desarrollador Junior",
  "empresa": "Empresa NextIA",
  "requisitos_obligatorios": ["python", "sql"],
  "requisitos_deseables": ["git", "docker"]
}
```

El workflow verifica que título, empresa y al menos un requisito obligatorio estén presentes. Si son válidos, llama a `POST /ofertas`; si no, responde con estado 400:

```json
{
  "error": "Debes enviar titulo, empresa y al menos un requisito obligatorio"
}
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

## Cálculo de compatibilidad

El score va de 0 a 100 y combina requisitos obligatorios y deseables:

| Criterio | Puntos máximos | Cálculo |
|---|---:|---|
| Requisitos obligatorios | 70 | `70 x (obligatorios cumplidos / obligatorios totales)` |
| Requisitos deseables | 30 | `30 x (deseables cumplidos / deseables totales)` |

- Las competencias se comparan sin distinguir mayúsculas ni espacios sobrantes (`"Python "` equivale a `"python"`).
- Si la oferta no tiene requisitos deseables, se otorgan los 30 puntos completos.
- Una oferta sin requisitos obligatorios se rechaza con error.
- Las competencias faltantes se informan diferenciando las obligatorias.

Ejemplo: un estudiante tiene `Python, Git, Excel`; la oferta requiere `python, sql, excel` como obligatorias y `power bi, git` como deseables:

- Obligatorios: 2 de 3 = 46,7 puntos.
- Deseables: 1 de 2 = 15 puntos.
- **Score: 61,7**. Faltan `power bi` y `sql`.

## Endpoints de la API

| Método | Ruta | Descripción | Respuestas |
|---|---|---|---|
| GET | `/status` | Verifica que la API esté activa. | 200 |
| POST | `/estudiantes` | Registra un estudiante. | 201, 422 |
| GET | `/estudiantes` | Lista los estudiantes. | 200 |
| PUT | `/estudiantes/{id}` | Modifica un estudiante. | 200, 404, 422 |
| POST | `/ofertas` | Registra una oferta. | 201, 422 |
| GET | `/ofertas` | Lista las ofertas. | 200 |
| POST | `/compatibilidad` | Calcula y guarda la compatibilidad. | 201, 400, 404, 422 |
| GET | `/resultados` | Lista resultados; permite `?estudiante_id=`. | 200 |
| GET | `/resultados/{id}` | Obtiene un resultado. | 200, 404 |
| POST | `/recomendaciones` | Guarda una recomendación asociada a un resultado. | 201, 404, 422 |
| GET | `/recomendaciones` | Lista recomendaciones; permite `?resultado_id=`. | 200 |

## Uso de inteligencia artificial

Google Gemini se utiliza para generar recomendaciones de formación mediante n8n. Estas recomendaciones deben revisarse por una persona. El score y la detección de competencias faltantes se calculan con reglas deterministas de Python y no dependen de la IA.

Durante el desarrollo se utilizó GitHub Copilot como asistencia para analizar, implementar y revisar partes del sistema. La bitácora registra aportes concretos y cómo el grupo verificó las propuestas:

| Área | Aporte concreto con asistencia de IA | Decisión, corrección o revisión del grupo | Verificación |
|---|---|---|---|
| Lógica de compatibilidad | Se revisó la normalización de competencias y el cálculo separado de requisitos obligatorios y deseables, incluyendo la lista de competencias faltantes. | Se mantuvo el score como cálculo determinista en Python y separado de las recomendaciones generadas por IA. | Se contrastaron ejemplos de competencias coincidentes y faltantes con el score esperado. |
| Persistencia JSON | Se organizó la lectura, escritura y asignación de identificadores en funciones reutilizables para estudiantes, ofertas, resultados y recomendaciones. | Se eligieron archivos JSON como persistencia sencilla para el alcance del prototipo y los datos de demostración. | Se verificó que los registros guardados pudieran volver a consultarse desde la API y aparecer en la interfaz. |
| Validación y manejo de errores | Se revisaron las validaciones de entrada, las respuestas HTTP de FastAPI y las respuestas de error de los workflows de n8n. | Se contemplaron datos incompletos, identificadores inexistentes y errores de conexión; la interfaz muestra mensajes en lugar de dejar la operación sin explicación. | Se probaron solicitudes inválidas y casos de error durante la integración. |
| Integración Streamlit, FastAPI y n8n | Se revisó el recorrido desde los formularios hasta los webhooks, la API y el almacenamiento, además de la consulta de resultados y recomendaciones. | Se conservaron identificadores de origen para distinguir el score calculado por reglas de Python de las recomendaciones generadas por Gemini. | Se comprobó el flujo de alta, cálculo y consulta desde la interfaz, además de las respuestas de los workflows. |
| Interfaz de resultados | Se recibió asistencia para organizar la vista de diagnóstico, competencias faltantes, recomendaciones de IA e historial. | El grupo revisó los textos y mantuvo visible que la recomendación automática requiere revisión humana. | Se comprobó la visualización con resultados que incluyen brechas y recomendaciones asociadas. |

El grupo revisó y corrigió las propuestas antes de incorporarlas al proyecto. La IA no reemplazó las pruebas ni la responsabilidad del equipo. Las verificaciones descritas corresponden a pruebas manuales de integración; no implican que exista una suite automatizada de tests.
