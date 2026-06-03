# =============================================================================
# Dockerfile — Observatorio GeoTurismo (Laboratorio TerrarIA)
# Stack: FastAPI + Google ADK (Gemini) + GeoPandas + PostgreSQL client
# =============================================================================

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TZ=America/Bogota

# -----------------------------------------------------------------------------
# Dependencias del sistema:
#   - libgdal/geos/proj: geopandas, folium
#   - libspatialindex:   rtree (índices espaciales de geopandas)
#   - libpq + postgresql-client: psycopg2 + pg_restore para cargar el backup
#   - build-essential:   compilación de paquetes que no tienen wheel
#   - tzdata, curl:      utilidades varias
# -----------------------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libgdal-dev \
        libgeos-dev \
        libproj-dev \
        libspatialindex-dev \
        libpq-dev \
        postgresql-client \
        tzdata \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# -----------------------------------------------------------------------------
# Instalar dependencias Python en una capa separada para aprovechar la caché.
# Si requirements.txt no cambia, esta capa se reutiliza entre builds.
# -----------------------------------------------------------------------------
COPY requirements.txt ./
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# -----------------------------------------------------------------------------
# Copiar el código de la aplicación.
# En desarrollo, el docker-compose monta este directorio como volumen,
# por lo que los cambios en código se reflejan sin reconstruir la imagen.
# -----------------------------------------------------------------------------
COPY . .

EXPOSE 8081

# Healthcheck simple: el endpoint /health del server.py
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:8081/health || exit 1

# Comando por defecto: arranca FastAPI con recarga automática
# (en producción quita --reload y agrega --workers 2)
CMD ["uvicorn", "chatbot.server:app", "--host", "0.0.0.0", "--port", "8081", "--reload"]
