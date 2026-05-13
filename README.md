# GeoTurismo — Observatorio de Turismo Inteligente

**Laboratorio TerrarIA · Universidad del Valle · Valle del Cauca, Colombia**

Sistema de inteligencia territorial para el análisis y visualización del turismo en los 29 municipios del Valle del Cauca (2022–2025).

---

## ¿Qué hace este proyecto?

> *¿Dónde se concentran las oportunidades turísticas? ¿Qué territorios tienen mayor potencial y qué factores limitan o habilitan su desarrollo?*

GeoTurismo responde estas preguntas combinando datos PostGIS, visualizaciones interactivas y un chatbot con inteligencia artificial.

---

## Arquitectura general

```
PostgreSQL/PostGIS (terrarIA)
        │
        ▼
src/db.py + src/transform.py
        │
        ├── outputs/indicadores_turisticos.csv
        ├── outputs/priorizacion_destinos.csv
        │
        ▼
src/viz.py + src/mapa.py
        │
        ├── outputs/graficas/
        └── outputs/mapa_actual.html
        │
        ▼
frontend/                        chatbot/
  index.html  (Dashboard)          server.py (FastAPI :8081)
  geovisor.html (Mapa interactivo)    └── geoturismo_agent/
  asistente.js (Chat IA)                  ├── agent.py (orquestador)
                                          ├── agents/turismo_agent.py
                                          ├── agents/viz_agent.py
                                          └── agents/ui_agent.py
```

---

## Stack tecnológico

| Capa | Tecnología |
|------|-----------|
| Base de datos | PostgreSQL 17 + PostGIS |
| Backend IA | Google ADK + Gemini 2.0 Flash |
| API bridge | FastAPI + Uvicorn |
| Visualizaciones | Matplotlib + Seaborn |
| Frontend | HTML5 + CSS3 + JS vanilla |
| Mapas | Leaflet.js + GeoJSON |

---

## Estructura del proyecto

```
geoturismo_valle/
├── src/                        # Pipeline de datos
│   ├── db.py                   # Conexión PostgreSQL/PostGIS
│   ├── config.py               # Variables de entorno
│   ├── transform.py            # Limpieza e indicadores
│   ├── viz.py                  # Gráficas matplotlib
│   └── mapa.py                 # Mapa Folium
│
├── chatbot/                    # Chatbot con Google ADK
│   ├── server.py               # API FastAPI (puerto 8081)
│   └── geoturismo_agent/
│       ├── agent.py            # Orquestador principal
│       ├── tools.py            # 9 tools de datos turísticos
│       ├── viz_tools.py        # 6 tools de visualización (PNG)
│       ├── ui_tools.py         # 3 tools de control de interfaz
│       ├── ui_actions.py       # Contratos de acciones UI
│       ├── callbacks.py        # Logging JSON de tool calls
│       └── agents/
│           ├── turismo_agent.py
│           ├── viz_agent.py
│           └── ui_agent.py
│
├── frontend/                   # Dashboard web
│   ├── index.html              # Panel de control principal
│   ├── geovisor.html           # Visor geoespacial interactivo
│   ├── asistente.js            # Panel de chat IA (drawer)
│   ├── panel.js                # Lógica del dashboard
│   ├── panel.css               # Estilos (tema dark verde)
│   ├── geoturismo-data.js      # Datos livianos exportados desde PostgreSQL
│   └── geoturismo-municipios.js # Polígonos generados localmente (no versionar si pesa >100 MB)
│
├── scripts/                    # Utilidades y carga de datos
├── outputs/                    # CSVs e imágenes generadas
│   └── graficas/
├── docs/
│   └── ARCHITECTURE.md
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## Datos disponibles

- **Tabla** `turismo_municipal`: 116 filas · 29 municipios · años 2022–2025
- **Tabla** `atractivos_turisticos`: 39 atractivos georreferenciados
- **Tipos de turismo**: Ecoturismo · Cultural · Religioso · Aventura · Gastronómico · Náutico · Rural
- **Variables principales**: `visitantes`, `ocupacion_hotelera`, `gasto_estimado`, `indice_oportunidad_turistica`, `atractivos`, `indice_seguridad`, `tiempo_acceso_min`

---

## Chatbot IA — Capacidades

El asistente responde en lenguaje natural y puede:

| Tipo de consulta | Ejemplo |
|-----------------|---------|
| Datos por municipio | "¿Cuántos visitantes tuvo Cali en 2024?" |
| Rankings | "Top 5 municipios más visitados en 2023" |
| Series históricas | "Evolución de Palmira 2022–2025" |
| Resumen departamental | "Resumen del Valle del Cauca en 2024" |
| Atractivos | "¿Qué se puede visitar en Buga?" |
| Por tipo de turismo | "¿Qué municipios tienen ecoturismo?" |
| Gráficas PNG | "Muéstrame el perfil radar de Cali" |
| Acciones de UI | "Abre el mapa de visitantes en 2024" |

Funciona en **modo fallback local** (sin LLM, solo consulta a PostgreSQL) cuando la cuota de Gemini está agotada.

---

## Inicio rápido

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
pip install google-adk google-genai fastapi uvicorn python-dotenv
```

### 2. Configurar variables de entorno

```bash
# Raíz del proyecto
cp .env.example .env
# Editar .env con credenciales de PostgreSQL

# Chatbot
cp chatbot/geoturismo_agent/.env.example chatbot/geoturismo_agent/.env
# Editar con GOOGLE_API_KEY desde https://aistudio.google.com/apikey
```

### 3. Ejecutar pipeline de datos

```powershell
python scripts/run_all.py
```

El pipeline genera `frontend/geoturismo-data.js` y `frontend/geoturismo-municipios.js`.
Para GitHub conviene versionar `geoturismo-data.js` y excluir `geoturismo-municipios.js` cuando el archivo supere 100 MB.
En despliegue remoto inicial, el geovisor funciona sin polígonos municipales y conserva puntos, rankings e indicadores.

### 4. Iniciar servidor del chatbot

```bash
cd chatbot
uvicorn server:app --host 0.0.0.0 --port 8081 --reload
```

### 5. Abrir el dashboard

Abrir `frontend/index.html` en el navegador → clic en **Asistente IA** en el sidebar.

### 6. Verificar funcionamiento

```bash
python test_chatbot.py
```

---

## Variables de entorno

### `.env` (raíz)
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=terrarIA
DB_USER=postgres
DB_PASSWORD=tu_contrasena
```

### `chatbot/geoturismo_agent/.env`
```env
GOOGLE_GENAI_USE_VERTEXAI=FALSE
GOOGLE_API_KEY=tu_api_key_aqui
GEMINI_MODEL=gemini-2.0-flash
CHATBOT_PORT=8081
```

---

## Modelos Gemini soportados (cuotas gratuitas)

| Modelo | RPD | RPM |
|--------|-----|-----|
| `gemini-2.0-flash` | 1.500 | 15 |
| `gemini-2.5-flash-lite` | 1.000 | 15 |
| `gemini-2.5-flash` | 20 | 5 |

---

## Estado del proyecto · v0.1 piloto

- [x] Pipeline de datos PostGIS → CSV → gráficas → frontend
- [x] Dashboard interactivo (Panel, Indicadores, Tendencias, Priorización)
- [x] Geovisor con capas de municipios y atractivos (Leaflet)
- [x] Chatbot multi-agente Google ADK (orquestador + turismo + viz + ui)
- [x] Modo fallback local (sin dependencia de Gemini)
- [x] Logging de tool calls a JSON
- [x] Panel Asistente IA integrado en el frontend (drawer)
- [ ] Corrección aliases municipios en viz_agent
- [ ] Persistencia de sesiones en PostgreSQL
- [ ] Despliegue en servidor

---

## Publicación en GitHub

Antes de hacer push:

```powershell
python scripts/run_all.py
```

No subir:

- `.env`
- `chatbot/geoturismo_agent/.env`
- `__pycache__/`
- `outputs/`
- `frontend/geoturismo-municipios.js` si pesa más de 100 MB
- archivos Excel fuente en `fuentes/`

Repositorio remoto sugerido:

```powershell
git remote add origin https://github.com/germanavila09/geoturismo_valle.git
git branch -M main
git push -u origin main
```

---

*Piloto v0.1 — Laboratorio TerrarIA, Universidad del Valle*
