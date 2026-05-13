-- =============================================================
-- TerrarIA - Laboratorio de Observatorios Geoespaciales
-- Esquema de base de datos: observatorio_geoturismo
-- Base de datos: terrarIA  |  Usuario: postgres
-- =============================================================
-- PASO 1: Ejecutar conectado a la BD "postgres":
--   CREATE DATABASE "terrarIA";
--
-- PASO 2: Conectar a "terrarIA" y ejecutar el resto:
-- =============================================================

-- Extensión PostGIS (geoespacial)
CREATE EXTENSION IF NOT EXISTS postgis;

-- =============================================================
-- TABLA PRINCIPAL: turismo_municipal
-- Estadísticas turísticas por municipio y año
-- =============================================================
CREATE TABLE IF NOT EXISTS public.turismo_municipal (
    id                  SERIAL PRIMARY KEY,
    municipio           TEXT        NOT NULL,
    anio                INTEGER     NOT NULL,
    visitantes          NUMERIC     DEFAULT 0,
    atractivos          INTEGER     DEFAULT 0,
    ocupacion_hotelera  NUMERIC     DEFAULT 0,   -- porcentaje 0-100
    gasto_estimado      NUMERIC     DEFAULT 0,   -- COP miles de pesos
    indice_seguridad    NUMERIC     DEFAULT 0,   -- índice 0.0 - 1.0
    tiempo_acceso_min   NUMERIC     DEFAULT 0,   -- minutos desde Cali
    geom                GEOMETRY(Point, 4326),
    creado_en           TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_turismo_municipio ON public.turismo_municipal (municipio);
CREATE INDEX IF NOT EXISTS idx_turismo_anio      ON public.turismo_municipal (anio);
CREATE INDEX IF NOT EXISTS idx_turismo_geom      ON public.turismo_municipal USING GIST (geom);

-- =============================================================
-- TABLA SECUNDARIA: atractivos_turisticos
-- Sitios y atractivos turísticos del Valle del Cauca
-- =============================================================
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
