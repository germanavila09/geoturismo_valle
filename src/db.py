import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

from .config import ATTRACTIONS_TABLE, DB_CONFIG, MUNICIPALITIES_TABLE, SCHEMA, TABLE

try:
    import geopandas as gpd
except ImportError:
    gpd = None


def crear_engine():
    cfg = DB_CONFIG
    url = URL.create(
        "postgresql+psycopg2",
        username=cfg["user"],
        password=cfg["password"],
        host=cfg["host"],
        port=int(cfg["port"]),
        database=cfg["dbname"],
    )
    return create_engine(url)


def cargar_datos(engine):
    query = text(f"""
        SELECT
            *,
            CASE WHEN geom IS NOT NULL THEN ST_Y(ST_Centroid(geom)) END AS lat,
            CASE WHEN geom IS NOT NULL THEN ST_X(ST_Centroid(geom)) END AS lng
        FROM "{SCHEMA}"."{TABLE}"
    """)
    if gpd is None:
        try:
            return pd.read_sql(query, engine)
        except Exception:
            return pd.read_sql(text(f'SELECT * FROM "{SCHEMA}"."{TABLE}"'), engine)
    try:
        return gpd.read_postgis(query, engine, geom_col="geom")
    except Exception:
        try:
            return pd.read_sql(query, engine)
        except Exception:
            return pd.read_sql(text(f'SELECT * FROM "{SCHEMA}"."{TABLE}"'), engine)


def cargar_atractivos(engine):
    query = text(f"""
        SELECT
            *,
            CASE
                WHEN geom IS NULL THEN NULL
                WHEN ST_SRID(geom) IN (0, 4326) THEN ST_Y(geom)
                ELSE ST_Y(ST_Transform(geom, 4326))
            END AS lat,
            CASE
                WHEN geom IS NULL THEN NULL
                WHEN ST_SRID(geom) IN (0, 4326) THEN ST_X(geom)
                ELSE ST_X(ST_Transform(geom, 4326))
            END AS lng
        FROM "{SCHEMA}"."{ATTRACTIONS_TABLE}"
    """)
    try:
        return pd.read_sql(query, engine)
    except Exception:
        if gpd is not None:
            try:
                return gpd.read_postgis(query, engine, geom_col="geom")
            except Exception:
                pass
        return pd.read_sql(text(f'SELECT * FROM "{SCHEMA}"."{ATTRACTIONS_TABLE}"'), engine)


def cargar_municipios_valle(engine):
    query = text(f"""
        SELECT
            *,
            ST_AsGeoJSON(ST_Transform(geom, 4326)) AS geom_geojson
        FROM "{SCHEMA}"."{MUNICIPALITIES_TABLE}"
    """)
    try:
        return pd.read_sql(query, engine)
    except Exception:
        return pd.DataFrame()


def cargar_valle_mun(engine, anio=None):
    """Carga la capa de municipios del Valle del Cauca (MultiPolygon, SRID 3857).

    Columnas: DPTO_CCDGO, MPIO_CCDGO, MPIO_CNMBR, anio, poblacion,
              conteo_dengue, incidencia_dengue, geom, id.
    Si se pasa `anio`, filtra por ese año; de lo contrario devuelve todos los registros.
    """
    if anio is not None:
        query = text('SELECT * FROM public.valle_mun WHERE anio = :anio')
        params = {"anio": anio}
    else:
        query = text("SELECT * FROM public.valle_mun")
        params = {}

    if gpd is None:
        return pd.read_sql(query, engine, params=params)
    try:
        return gpd.read_postgis(query, engine, geom_col="geom", params=params)
    except Exception:
        return pd.read_sql(query, engine, params=params)
