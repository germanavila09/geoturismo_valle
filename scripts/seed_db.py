"""
TerrarIA - Observatorio GeoTurismo
Crea la base de datos 'terrarIA', habilita PostGIS y pobla las tablas
turismo_municipal y atractivos_turisticos desde el Excel de fuentes.

Uso:
    python scripts/seed_db.py

Variables de entorno usadas (o valores por defecto):
    DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
"""

import os
import sys
from pathlib import Path

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import pandas as pd

# ── Credenciales ──────────────────────────────────────────────────────────────
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "terrarIA")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

EXCEL_PATH = (
    Path(__file__).parent.parent
    / "fuentes"
    / "Sitios Turísticos y Municipios del Valle del Cauca.xlsx"
)

# ── Coordenadas de municipios (centroides WGS84) ──────────────────────────────
COORDS = {
    "SANTIAGO DE CALI":    (3.4516, -76.5320),
    "GUADALAJARA DE BUGA": (3.8999, -76.2987),
    "BUENAVENTURA":        (3.8801, -77.0310),
    "CALIMA - EL DARIÉN":  (3.9291, -76.4735),
    "EL CERRITO":          (3.6899, -76.2748),
    "ROLDANILLO":          (4.4027, -76.1548),
    "LA UNIÓN":            (4.5377, -76.1068),
    "DAGUA":               (3.6588, -76.6892),
    "JAMUNDÍ":             (3.2622, -76.5376),
    "EL CAIRO":            (4.9340, -76.2518),
    "TULUÁ":               (4.0839, -76.2003),
    "SEVILLA":             (4.2681, -75.9378),
    "PALMIRA":             (3.5395, -76.3035),
    "CARTAGO":             (4.7450, -75.9122),
    "LA CUMBRE":           (3.6447, -76.5633),
    "YOTOCO":              (3.8777, -76.4075),
    "GUACARÍ":             (3.7672, -76.3288),
    "EL DOVIO":            (4.5233, -76.2789),
    "GINEBRA":             (3.7369, -76.2753),
    "ANSERMANUEVO":        (4.8013, -76.0489),
    "ALCALÁ":              (4.6783, -75.7786),
    "RESTREPO":            (3.8267, -76.5247),
    "RIOFRÍO":             (4.1158, -76.2949),
    "TRUJILLO":            (4.2322, -76.3264),
    "LA VICTORIA":         (4.5177, -76.0352),
    "VIJES":               (3.6863, -76.4700),
    "YUMBO":               (3.5906, -76.4952),
    "CAICEDONIA":          (4.3320, -75.8268),
    "ZARZAL":              (4.3934, -76.0744),
}

# ── Datos base de turismo (año 2024) ──────────────────────────────────────────
# visitantes: total anual | atractivos: sitios catalogados
# ocupacion_hotelera: % | gasto_estimado: COP miles | indice_seguridad: 0-1
# tiempo_acceso_min: minutos desde Cali
TURISMO_BASE = {
    "SANTIAGO DE CALI":    dict(visitantes=2_800_000, atractivos=45, ocupacion_hotelera=72.5, gasto_estimado=850_000, indice_seguridad=0.62, tiempo_acceso_min=15),
    "GUADALAJARA DE BUGA": dict(visitantes=850_000,   atractivos=18, ocupacion_hotelera=68.0, gasto_estimado=320_000, indice_seguridad=0.75, tiempo_acceso_min=75),
    "BUENAVENTURA":        dict(visitantes=620_000,   atractivos=22, ocupacion_hotelera=55.0, gasto_estimado=280_000, indice_seguridad=0.45, tiempo_acceso_min=145),
    "CALIMA - EL DARIÉN":  dict(visitantes=480_000,   atractivos=12, ocupacion_hotelera=62.0, gasto_estimado=210_000, indice_seguridad=0.80, tiempo_acceso_min=90),
    "EL CERRITO":          dict(visitantes=180_000,   atractivos=8,  ocupacion_hotelera=42.0, gasto_estimado=95_000,  indice_seguridad=0.70, tiempo_acceso_min=50),
    "ROLDANILLO":          dict(visitantes=210_000,   atractivos=9,  ocupacion_hotelera=50.0, gasto_estimado=110_000, indice_seguridad=0.72, tiempo_acceso_min=165),
    "LA UNIÓN":            dict(visitantes=95_000,    atractivos=6,  ocupacion_hotelera=38.0, gasto_estimado=58_000,  indice_seguridad=0.68, tiempo_acceso_min=200),
    "DAGUA":               dict(visitantes=145_000,   atractivos=7,  ocupacion_hotelera=40.0, gasto_estimado=72_000,  indice_seguridad=0.65, tiempo_acceso_min=60),
    "JAMUNDÍ":             dict(visitantes=320_000,   atractivos=14, ocupacion_hotelera=55.0, gasto_estimado=185_000, indice_seguridad=0.73, tiempo_acceso_min=30),
    "EL CAIRO":            dict(visitantes=42_000,    atractivos=4,  ocupacion_hotelera=30.0, gasto_estimado=28_000,  indice_seguridad=0.78, tiempo_acceso_min=300),
    "TULUÁ":               dict(visitantes=450_000,   atractivos=20, ocupacion_hotelera=60.0, gasto_estimado=230_000, indice_seguridad=0.66, tiempo_acceso_min=110),
    "SEVILLA":             dict(visitantes=280_000,   atractivos=16, ocupacion_hotelera=52.0, gasto_estimado=155_000, indice_seguridad=0.74, tiempo_acceso_min=155),
    "PALMIRA":             dict(visitantes=520_000,   atractivos=19, ocupacion_hotelera=58.0, gasto_estimado=265_000, indice_seguridad=0.67, tiempo_acceso_min=25),
    "CARTAGO":             dict(visitantes=380_000,   atractivos=15, ocupacion_hotelera=56.0, gasto_estimado=195_000, indice_seguridad=0.70, tiempo_acceso_min=225),
    "LA CUMBRE":           dict(visitantes=98_000,    atractivos=5,  ocupacion_hotelera=35.0, gasto_estimado=48_000,  indice_seguridad=0.82, tiempo_acceso_min=55),
    "YOTOCO":              dict(visitantes=75_000,    atractivos=5,  ocupacion_hotelera=32.0, gasto_estimado=38_000,  indice_seguridad=0.77, tiempo_acceso_min=80),
    "GUACARÍ":             dict(visitantes=88_000,    atractivos=6,  ocupacion_hotelera=36.0, gasto_estimado=44_000,  indice_seguridad=0.73, tiempo_acceso_min=65),
    "EL DOVIO":            dict(visitantes=35_000,    atractivos=3,  ocupacion_hotelera=28.0, gasto_estimado=22_000,  indice_seguridad=0.76, tiempo_acceso_min=290),
    "GINEBRA":             dict(visitantes=120_000,   atractivos=7,  ocupacion_hotelera=44.0, gasto_estimado=65_000,  indice_seguridad=0.79, tiempo_acceso_min=70),
    "ANSERMANUEVO":        dict(visitantes=48_000,    atractivos=4,  ocupacion_hotelera=31.0, gasto_estimado=30_000,  indice_seguridad=0.75, tiempo_acceso_min=245),
    "ALCALÁ":              dict(visitantes=62_000,    atractivos=4,  ocupacion_hotelera=33.0, gasto_estimado=35_000,  indice_seguridad=0.77, tiempo_acceso_min=265),
    "RESTREPO":            dict(visitantes=115_000,   atractivos=8,  ocupacion_hotelera=42.0, gasto_estimado=62_000,  indice_seguridad=0.80, tiempo_acceso_min=100),
    "RIOFRÍO":             dict(visitantes=55_000,    atractivos=4,  ocupacion_hotelera=30.0, gasto_estimado=32_000,  indice_seguridad=0.76, tiempo_acceso_min=130),
    "TRUJILLO":            dict(visitantes=145_000,   atractivos=9,  ocupacion_hotelera=46.0, gasto_estimado=78_000,  indice_seguridad=0.74, tiempo_acceso_min=160),
    "LA VICTORIA":         dict(visitantes=42_000,    atractivos=3,  ocupacion_hotelera=28.0, gasto_estimado=25_000,  indice_seguridad=0.78, tiempo_acceso_min=210),
    "VIJES":               dict(visitantes=52_000,    atractivos=3,  ocupacion_hotelera=29.0, gasto_estimado=28_000,  indice_seguridad=0.79, tiempo_acceso_min=45),
    "YUMBO":               dict(visitantes=195_000,   atractivos=8,  ocupacion_hotelera=48.0, gasto_estimado=102_000, indice_seguridad=0.64, tiempo_acceso_min=20),
    "CAICEDONIA":          dict(visitantes=88_000,    atractivos=6,  ocupacion_hotelera=38.0, gasto_estimado=48_000,  indice_seguridad=0.73, tiempo_acceso_min=185),
    "ZARZAL":              dict(visitantes=110_000,   atractivos=7,  ocupacion_hotelera=40.0, gasto_estimado=58_000,  indice_seguridad=0.71, tiempo_acceso_min=195),
}

# Factor de crecimiento por año respecto a 2024
GROWTH = {2022: 0.84, 2023: 0.92, 2024: 1.00, 2025: 1.08}


# ── Helpers ───────────────────────────────────────────────────────────────────

def conectar(dbname="postgres"):
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT,
        dbname=dbname, user=DB_USER, password=DB_PASSWORD,
    )


def crear_base_datos(conn):
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_NAME,))
    if cur.fetchone():
        print(f"  [OK] Base de datos '{DB_NAME}' ya existe.")
    else:
        cur.execute(f'CREATE DATABASE "{DB_NAME}"')
        print(f"  [OK] Base de datos '{DB_NAME}' creada.")
    cur.close()


def ejecutar_sql(conn, sql, params=None):
    cur = conn.cursor()
    cur.execute(sql, params)
    cur.close()


def crear_esquema(conn):
    schema_sql = """
    CREATE EXTENSION IF NOT EXISTS postgis;

    CREATE TABLE IF NOT EXISTS public.turismo_municipal (
        id                  SERIAL PRIMARY KEY,
        municipio           TEXT        NOT NULL,
        anio                INTEGER     NOT NULL,
        visitantes          NUMERIC     DEFAULT 0,
        atractivos          INTEGER     DEFAULT 0,
        ocupacion_hotelera  NUMERIC     DEFAULT 0,
        gasto_estimado      NUMERIC     DEFAULT 0,
        indice_seguridad    NUMERIC     DEFAULT 0,
        tiempo_acceso_min   NUMERIC     DEFAULT 0,
        geom                GEOMETRY(Point, 4326),
        creado_en           TIMESTAMPTZ DEFAULT now()
    );

    CREATE INDEX IF NOT EXISTS idx_turismo_municipio ON public.turismo_municipal (municipio);
    CREATE INDEX IF NOT EXISTS idx_turismo_anio      ON public.turismo_municipal (anio);
    CREATE INDEX IF NOT EXISTS idx_turismo_geom      ON public.turismo_municipal USING GIST (geom);

    CREATE TABLE IF NOT EXISTS public.atractivos_turisticos (
        id              SERIAL PRIMARY KEY,
        municipio       TEXT,
        nombre          TEXT,
        actividades     TEXT,
        altitud         TEXT,
        temperatura     TEXT,
        descripcion     TEXT,
        costo_entrada   TEXT,
        fuente          TEXT,
        geom            GEOMETRY(Point, 4326),
        creado_en       TIMESTAMPTZ DEFAULT now()
    );

    CREATE INDEX IF NOT EXISTS idx_atractivos_municipio ON public.atractivos_turisticos (municipio);
    CREATE INDEX IF NOT EXISTS idx_atractivos_geom      ON public.atractivos_turisticos USING GIST (geom);
    """
    cur = conn.cursor()
    cur.execute(schema_sql)
    conn.commit()
    cur.close()
    print("  [OK] Esquema y tablas creados.")


def insertar_turismo_municipal(conn):
    insert_sql = """
    INSERT INTO public.turismo_municipal
        (municipio, anio, visitantes, atractivos, ocupacion_hotelera,
         gasto_estimado, indice_seguridad, tiempo_acceso_min, geom)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s,
            ST_SetSRID(ST_MakePoint(%s, %s), 4326))
    ON CONFLICT DO NOTHING;
    """
    rows = []
    for municipio, base in TURISMO_BASE.items():
        lat, lon = COORDS.get(municipio, (3.45, -76.53))
        for anio, factor in GROWTH.items():
            rows.append((
                municipio, anio,
                round(base["visitantes"] * factor),
                base["atractivos"],
                round(base["ocupacion_hotelera"] * factor, 2),
                round(base["gasto_estimado"] * factor),
                round(base["indice_seguridad"] * (1 + (factor - 1) * 0.3), 4),
                base["tiempo_acceso_min"],
                lon, lat,
            ))

    cur = conn.cursor()
    cur.executemany(insert_sql, rows)
    conn.commit()
    cur.close()
    print(f"  [OK] {len(rows)} registros insertados en turismo_municipal.")


def insertar_atractivos(conn):
    if not EXCEL_PATH.exists():
        print(f"  [WARN] Excel no encontrado en {EXCEL_PATH}. Omitiendo atractivos.")
        return

    df = pd.read_excel(EXCEL_PATH, sheet_name="Table 1")
    df.columns = ["municipio", "nombre", "actividades", "altitud",
                  "temperatura", "descripcion", "costo_entrada", "fuente"]

    insert_sql = """
    INSERT INTO public.atractivos_turisticos
        (municipio, nombre, actividades, altitud, temperatura,
         descripcion, costo_entrada, fuente, geom)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s,
            ST_SetSRID(ST_MakePoint(%s, %s), 4326));
    """
    rows = []
    for _, row in df.iterrows():
        municipio_upper = str(row["municipio"]).strip().upper()
        lat, lon = COORDS.get(municipio_upper, (3.45, -76.53))
        rows.append((
            str(row["municipio"]).strip(),
            str(row["nombre"]).strip(),
            str(row["actividades"]).strip() if pd.notna(row["actividades"]) else None,
            str(row["altitud"]).strip()     if pd.notna(row["altitud"])     else None,
            str(row["temperatura"]).strip() if pd.notna(row["temperatura"]) else None,
            str(row["descripcion"]).strip() if pd.notna(row["descripcion"]) else None,
            str(row["costo_entrada"]).strip() if pd.notna(row["costo_entrada"]) else None,
            str(row["fuente"]).strip()      if pd.notna(row["fuente"])      else None,
            lon, lat,
        ))

    cur = conn.cursor()
    cur.executemany(insert_sql, rows)
    conn.commit()
    cur.close()
    print(f"  [OK] {len(rows)} registros insertados en atractivos_turisticos.")


def verificar(conn):
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM public.turismo_municipal;")
    n_turismo = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM public.atractivos_turisticos;")
    n_atractivos = cur.fetchone()[0]
    cur.execute("SELECT version();")
    version = cur.fetchone()[0].split(",")[0]
    cur.close()
    print(f"\n  PostgreSQL : {version}")
    print(f"  turismo_municipal      : {n_turismo} filas")
    print(f"  atractivos_turisticos  : {n_atractivos} filas")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  TerrarIA – Setup base de datos GeoTurismo")
    print("=" * 60)

    print(f"\n[1/4] Conectando a PostgreSQL ({DB_USER}@{DB_HOST}:{DB_PORT})...")
    try:
        conn_admin = conectar("postgres")
    except psycopg2.OperationalError as e:
        print(f"  [ERROR] No se pudo conectar: {e}")
        sys.exit(1)

    print(f"[2/4] Creando base de datos '{DB_NAME}'...")
    crear_base_datos(conn_admin)
    conn_admin.close()

    print(f"[3/4] Creando esquema y tablas en '{DB_NAME}'...")
    conn = conectar(DB_NAME)
    crear_esquema(conn)

    print("[4/4] Insertando datos...")
    insertar_turismo_municipal(conn)
    insertar_atractivos(conn)

    print("\n[OK] Verificacion final:")
    verificar(conn)
    conn.close()

    print("\n" + "=" * 60)
    print("  Base de datos lista. Conexion configurada en .env")
    print("=" * 60)


if __name__ == "__main__":
    main()
