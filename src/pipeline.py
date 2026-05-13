from pathlib import Path

import pandas as pd

from .config import ANIO, MUNICIPIO, RUTA_FRONTEND, RUTA_SALIDA
from .db import cargar_atractivos, cargar_datos, cargar_municipios_valle, crear_engine
from .frontend_export import exportar_geovisor_js
from .mapa import generar_mapa_html
from .modelo import construir_escenarios
from .transform import (
    calcular_distribucion_tipo_turismo,
    calcular_analisis_geoespacial_turismo,
    calcular_indicadores_por_tipo,
    calcular_indice_oportunidad,
    calcular_priorizacion,
    construir_pivot,
    limpiar_datos,
)
from .viz import graficar_top_destinos, graficar_visitantes_por_anio


def ejecutar(anio=None, municipio=None, ruta_salida=None):
    anio = anio or ANIO
    municipio = (municipio or MUNICIPIO).upper()
    ruta = Path(ruta_salida or RUTA_SALIDA)
    graficas = ruta / "graficas"
    ruta.mkdir(parents=True, exist_ok=True)
    graficas.mkdir(parents=True, exist_ok=True)

    engine = crear_engine()
    try:
        gdf = limpiar_datos(cargar_datos(engine))
    except Exception:
        gdf = pd.DataFrame()
    df_atractivos = cargar_atractivos(engine)
    df_municipios = cargar_municipios_valle(engine)

    gdf = calcular_indice_oportunidad(gdf)
    pivot = construir_pivot(gdf)
    priorizacion = calcular_priorizacion(gdf)
    escenarios = construir_escenarios(priorizacion)

    dist_tipo, dist_tipo_mun = calcular_distribucion_tipo_turismo(df_atractivos)
    indicadores_tipo = calcular_indicadores_por_tipo(gdf)
    geo_tipo, geo_municipios = calcular_analisis_geoespacial_turismo(df_atractivos)

    if not gdf.empty:
        gdf.to_csv(ruta / "indicadores_turisticos.csv", index=False)
    if not priorizacion.empty:
        priorizacion.to_csv(ruta / "priorizacion_destinos.csv", index=False)
    if not escenarios.empty:
        escenarios.to_csv(ruta / "escenarios_turisticos.csv", index=False)
    if not dist_tipo.empty:
        dist_tipo.to_csv(ruta / "distribucion_tipo_turismo.csv", index=False)
    if not dist_tipo_mun.empty:
        dist_tipo_mun.to_csv(ruta / "tipo_turismo_por_municipio.csv", index=False)
    if not indicadores_tipo.empty:
        indicadores_tipo.to_csv(ruta / "indicadores_por_tipo.csv", index=False)
    if not geo_tipo.empty:
        geo_tipo.to_csv(ruta / "analisis_geoespacial_tipos.csv", index=False)
    if not geo_municipios.empty:
        geo_municipios.to_csv(ruta / "potencial_turistico_por_inventario.csv", index=False)

    if not gdf.empty:
        graficar_visitantes_por_anio(gdf, graficas)
    if not priorizacion.empty:
        graficar_top_destinos(priorizacion, graficas)
    ruta_frontend_data = exportar_geovisor_js(gdf, df_atractivos, RUTA_FRONTEND, df_municipios)
    try:
        ruta_mapa = generar_mapa_html(gdf, ruta)
    except Exception:
        ruta_mapa = None

    return {
        "gdf": gdf,
        "pivot": pivot,
        "priorizacion": priorizacion,
        "dist_tipo_turismo": dist_tipo,
        "dist_tipo_por_municipio": dist_tipo_mun,
        "indicadores_por_tipo": indicadores_tipo,
        "analisis_geoespacial_tipos": geo_tipo,
        "potencial_turistico_por_inventario": geo_municipios,
        "ruta_mapa": ruta_mapa,
        "ruta_frontend_data": ruta_frontend_data,
        "municipio": municipio,
        "anio": anio,
    }
