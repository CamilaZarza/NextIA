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

---

### Flujo de datos
 
```
Streamlit  ──(JSON / HTTP)──▶  FastAPI  ──▶  scoring.py (reglas)
 (interfaz)                       │
                                  ▼
                           data/*.json (persistencia)
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
 
Se necesitan **dos terminales**, con el entorno virtual activado en ambas y ubicadas en la raíz del proyecto.
 
**Terminal 1: API**
 
```bash
python -m uvicorn app.main:app --reload
```
 
- API: http://127.0.0.1:8000
- Documentación interactiva (Swagger): http://127.0.0.1:8000/docs
**Terminal 2: Interfaz**
 
```bash
python -m streamlit run interfaz/streamlit_app.py
```
 
- Interfaz: http://localhost:8501
Para detener cualquiera de los dos servicios, presionar `Ctrl + C` en su terminal.
 
> Si la API debe ser accesible desde otro equipo o contenedor de la red local, iniciarla con `--host 0.0.0.0`.
 
## 7. Funcionalidades principales
 
La interfaz tiene cuatro pestañas:
 
1. **Estudiantes**: alta de perfiles, listado y modificación de competencias.
2. **Ofertas**: alta de ofertas con requisitos obligatorios y deseables, y listado.
3. **Compatibilidad**: se elige un estudiante y una oferta y se calcula el score, con barra de progreso y competencias faltantes.
4. **Resultados**: historial de compatibilidades calculadas.
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
| POST | `/compatibilidad` | Calcula y guarda el scoring de un estudiante frente a una oferta | 201, 400, 404, 422 |
| GET | `/resultados` | Lista los resultados (filtro opcional `?estudiante_id=`) | 200 |
| GET | `/resultados/{id}` | Obtiene un resultado puntual | 200, 404 |
| POST | `/recomendaciones` | Guarda una recomendación asociada a un resultado | 201, 404, 422 |
| GET | `/recomendaciones` | Lista recomendaciones (filtro opcional `?resultado_id=`) | 200 |
 
