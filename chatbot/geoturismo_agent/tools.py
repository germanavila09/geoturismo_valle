"""Tools del agente ADK del Observatorio GeoTurismo.

Cada función sigue las reglas de ADK:
  - Parámetros JSON-serializables.
  - Docstring claro para que el LLM decida cuándo invocarla.
  - Retorna siempre dict con clave "status" ("success" | "error").
  - Recibe tool_context: ToolContext para leer/escribir state de sesión.

Base de datos: terrarIA (PostgreSQL/PostGIS)
Tablas: turismo_municipal, atractivos_turisticos
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import pandas as pd
from sqlalchemy import text

from google.adk.tools import ToolContext

from src.db import crear_engine

# ── Claves de state ────────────────────────────────────────────────────────────
STATE_LAST_MUNI  = "last_municipio"
STATE_LAST_ANIO  = "last_anio"
STATE_METRICA    = "metrica_preferida"

METRICAS_VALIDAS = {"visitantes", "indice_oportunidad", "ocupacion_hotelera", "gasto_estimado"}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _ok(**payload: Any) -> dict:
    return {"status": "success", **payload}


def _err(message: str) -> dict:
    return {"status": "error", "error_message": message}


# Alias de nombres populares → nombre exacto en turismo_municipal
_ALIAS_MUNICIPIO: dict[str, str] = {
    "CALI":        "SANTIAGO DE CALI",
    "BUGA":        "GUADALAJARA DE BUGA",
    "CALIMA":      "CALIMA - EL DARIÉN",
    "EL DARIEN":   "CALIMA - EL DARIÉN",
    "DARIEN":      "CALIMA - EL DARIÉN",
    "JAMUNDI":     "JAMUNDÍ",
    "GUACARI":     "GUACARÍ",
    "TULUA":       "TULUÁ",
    "ALCALA":      "ALCALÁ",
    "RIOFRIO":     "RIOFRÍO",
}


def _norm(nombre: str) -> str:
    upper = nombre.strip().upper()
    return _ALIAS_MUNICIPIO.get(upper, upper)


def _remember(ctx: ToolContext, municipio: str | None = None, anio: int | None = None) -> None:
    if municipio is not None:
        ctx.state[STATE_LAST_MUNI] = municipio
    if anio is not None:
        ctx.state[STATE_LAST_ANIO] = int(anio)


# ── Tools expuestas ────────────────────────────────────────────────────────────

def listar_municipios(tool_context: ToolContext) -> dict:
    """Devuelve la lista de municipios disponibles en el Observatorio GeoTurismo.

    Usar cuando el usuario pregunte qué municipios cubre el sistema o
    cuando necesites validar un nombre antes de otra consulta.
    """
    try:
        engine = crear_engine()
        df = pd.read_sql(
            text("SELECT DISTINCT municipio FROM public.turismo_municipal ORDER BY municipio;"),
            engine,
        )
        return _ok(municipios=df["municipio"].tolist(), total=len(df))
    except Exception as exc:
        return _err(f"No se pudo consultar la lista de municipios: {exc}")


def consultar_municipio_anio(municipio: str, anio: int, tool_context: ToolContext) -> dict:
    """Indicadores turísticos de un municipio en un año específico.

    Devuelve visitantes, atractivos, ocupación hotelera, gasto estimado,
    índice de seguridad, tiempo de acceso e índice de oportunidad turística.

    Args:
        municipio: Nombre del municipio en mayúsculas (ej. "CALI", "PALMIRA").
        anio: Año de consulta (2022-2025).
    """
    try:
        muni = _norm(municipio)
        engine = crear_engine()
        df = pd.read_sql(
            text("""
                SELECT municipio, anio, visitantes, atractivos,
                       ocupacion_hotelera, gasto_estimado, indice_seguridad,
                       tiempo_acceso_min, tipo_turismo_predominante
                FROM public.turismo_municipal
                WHERE municipio = :muni AND anio = :anio;
            """),
            engine,
            params={"muni": muni, "anio": int(anio)},
        )
        if df.empty:
            return _err(
                f"No hay datos para municipio={muni!r} y anio={anio}. "
                "Verifica el nombre con listar_municipios."
            )
        r = df.iloc[0].to_dict()
        _remember(tool_context, municipio=muni, anio=int(anio))
        return _ok(
            municipio=r["municipio"],
            anio=int(r["anio"]),
            visitantes=int(r["visitantes"]) if pd.notna(r["visitantes"]) else 0,
            atractivos=int(r["atractivos"]) if pd.notna(r["atractivos"]) else 0,
            ocupacion_hotelera=round(float(r["ocupacion_hotelera"]), 1) if pd.notna(r["ocupacion_hotelera"]) else None,
            gasto_estimado_cop=int(r["gasto_estimado"]) if pd.notna(r["gasto_estimado"]) else 0,
            indice_seguridad=round(float(r["indice_seguridad"]), 3) if pd.notna(r["indice_seguridad"]) else None,
            tiempo_acceso_min=int(r["tiempo_acceso_min"]) if pd.notna(r["tiempo_acceso_min"]) else None,
            tipo_turismo_predominante=r.get("tipo_turismo_predominante"),
        )
    except Exception as exc:
        return _err(f"Error consultando indicadores: {exc}")


def top_municipios_turismo(anio: int, tool_context: ToolContext, n: int = 5, metrica: str = "") -> dict:
    """Top-N municipios del Valle del Cauca según una métrica turística en un año.

    Args:
        anio: Año a consultar (2022-2025).
        n: Número de municipios a devolver (1-29). Default 5.
        metrica: "visitantes", "indice_oportunidad", "ocupacion_hotelera" o
            "gasto_estimado". Si llega vacío se usa state.metrica_preferida
            (default "visitantes").
    """
    try:
        if not metrica:
            metrica = tool_context.state.get(STATE_METRICA, "visitantes")
        if metrica not in METRICAS_VALIDAS:
            return _err(f"metrica debe ser una de: {', '.join(METRICAS_VALIDAS)}.")
        n = max(1, min(int(n), 29))

        col_map = {
            "visitantes":          "visitantes",
            "indice_oportunidad":  "indice_oportunidad_turistica",
            "ocupacion_hotelera":  "ocupacion_hotelera",
            "gasto_estimado":      "gasto_estimado",
        }
        col = col_map[metrica]

        engine = crear_engine()
        df = pd.read_sql(
            text(f"""
                SELECT municipio, visitantes, atractivos,
                       ocupacion_hotelera, gasto_estimado,
                       tipo_turismo_predominante,
                       {col} AS valor_metrica
                FROM public.turismo_municipal
                WHERE anio = :anio AND {col} IS NOT NULL
                ORDER BY {col} DESC
                LIMIT :n;
            """),
            engine,
            params={"anio": int(anio), "n": n},
        )
        if df.empty:
            return _err(f"No hay datos para el año {anio}.")

        ranking = []
        for _, r in df.iterrows():
            ranking.append({
                "municipio":               r["municipio"],
                "visitantes":              int(r["visitantes"]) if pd.notna(r["visitantes"]) else 0,
                "ocupacion_hotelera":      round(float(r["ocupacion_hotelera"]), 1) if pd.notna(r["ocupacion_hotelera"]) else None,
                "tipo_turismo":            r.get("tipo_turismo_predominante"),
                "valor_metrica":           round(float(r["valor_metrica"]), 2) if pd.notna(r["valor_metrica"]) else None,
            })
        _remember(tool_context, anio=int(anio))
        return _ok(anio=int(anio), metrica=metrica, ranking=ranking)
    except Exception as exc:
        return _err(f"Error generando ranking turístico: {exc}")


def serie_temporal_municipio(municipio: str, tool_context: ToolContext) -> dict:
    """Serie histórica de indicadores turísticos de un municipio (2022-2025).

    Args:
        municipio: Nombre del municipio (ej. "CALI").
    """
    try:
        muni = _norm(municipio)
        engine = crear_engine()
        df = pd.read_sql(
            text("""
                SELECT anio, visitantes, atractivos,
                       ocupacion_hotelera, gasto_estimado,
                       indice_seguridad, indice_oportunidad_turistica
                FROM public.turismo_municipal
                WHERE municipio = :muni
                ORDER BY anio;
            """),
            engine,
            params={"muni": muni},
        )
        if df.empty:
            return _err(
                f"No hay serie histórica para {muni!r}. "
                "Usa listar_municipios para verificar el nombre."
            )
        serie = [
            {
                "anio":                   int(r["anio"]),
                "visitantes":             int(r["visitantes"]) if pd.notna(r["visitantes"]) else 0,
                "ocupacion_hotelera":     round(float(r["ocupacion_hotelera"]), 1) if pd.notna(r["ocupacion_hotelera"]) else None,
                "gasto_estimado_cop":     int(r["gasto_estimado"]) if pd.notna(r["gasto_estimado"]) else 0,
                "indice_oportunidad":     round(float(r["indice_oportunidad_turistica"]), 4) if pd.notna(r["indice_oportunidad_turistica"]) else None,
            }
            for _, r in df.iterrows()
        ]
        _remember(tool_context, municipio=muni)
        return _ok(municipio=muni, n_puntos=len(serie), serie=serie)
    except Exception as exc:
        return _err(f"Error consultando serie temporal: {exc}")


def resumen_anio(anio: int, tool_context: ToolContext) -> dict:
    """Resumen agregado del turismo en el Valle del Cauca para un año dado.

    Calcula totales, promedios y municipios extremos en visitantes e índice.

    Args:
        anio: Año a consultar (2022-2025).
    """
    try:
        engine = crear_engine()
        df = pd.read_sql(
            text("""
                SELECT municipio, visitantes, atractivos,
                       ocupacion_hotelera, gasto_estimado,
                       indice_oportunidad_turistica, tipo_turismo_predominante
                FROM public.turismo_municipal
                WHERE anio = :anio;
            """),
            engine,
            params={"anio": int(anio)},
        )
        if df.empty:
            return _err(f"No hay datos para el año {anio}.")

        total_visitantes = int(df["visitantes"].fillna(0).sum())
        prom_ocupacion   = round(float(df["ocupacion_hotelera"].fillna(0).mean()), 1)
        prom_indice      = round(float(df["indice_oportunidad_turistica"].fillna(0).mean()), 4)

        idx_max_vis = df["visitantes"].idxmax()
        idx_max_ind = df["indice_oportunidad_turistica"].idxmax()

        tipo_conteo = df["tipo_turismo_predominante"].value_counts().to_dict()

        _remember(tool_context, anio=int(anio))
        return _ok(
            anio=int(anio),
            total_visitantes=total_visitantes,
            promedio_ocupacion_hotelera_pct=prom_ocupacion,
            promedio_indice_oportunidad=prom_indice,
            n_municipios=len(df),
            municipio_mas_visitantes={
                "nombre":     df.loc[idx_max_vis, "municipio"],
                "visitantes": int(df.loc[idx_max_vis, "visitantes"]),
            },
            municipio_mayor_indice={
                "nombre":  df.loc[idx_max_ind, "municipio"],
                "indice":  round(float(df.loc[idx_max_ind, "indice_oportunidad_turistica"]), 4),
            },
            distribucion_tipos=tipo_conteo,
        )
    except Exception as exc:
        return _err(f"Error generando resumen anual: {exc}")


def atractivos_municipio(municipio: str, tool_context: ToolContext) -> dict:
    """Lista los atractivos turísticos registrados en un municipio.

    Incluye nombre, actividades, tipo de turismo y costo de entrada.

    Args:
        municipio: Nombre del municipio (ej. "CALI", "BUGA").
    """
    try:
        muni = _norm(municipio)
        engine = crear_engine()
        df = pd.read_sql(
            text("""
                SELECT nombre, actividades, tipo_turismo, tipo_secundario,
                       altitud, temperatura, costo_entrada
                FROM public.atractivos_turisticos
                WHERE UPPER(municipio) = :muni
                ORDER BY tipo_turismo, nombre;
            """),
            engine,
            params={"muni": muni},
        )
        if df.empty:
            return _err(
                f"No se encontraron atractivos para {muni!r}. "
                "Prueba con listar_municipios para verificar el nombre."
            )
        atractivos = [
            {
                "nombre":        r["nombre"],
                "actividades":   r["actividades"],
                "tipo_turismo":  r["tipo_turismo"],
                "tipo_secundario": r["tipo_secundario"],
                "costo_entrada": r["costo_entrada"],
            }
            for _, r in df.iterrows()
        ]
        _remember(tool_context, municipio=muni)
        return _ok(municipio=muni, total=len(atractivos), atractivos=atractivos)
    except Exception as exc:
        return _err(f"Error consultando atractivos: {exc}")


def municipios_por_tipo_turismo(tipo: str, tool_context: ToolContext) -> dict:
    """Devuelve los municipios cuyo tipo de turismo predominante coincide con el solicitado.

    Args:
        tipo: Tipo de turismo (ej. "Ecoturismo", "Turismo Cultural",
            "Turismo Religioso", "Turismo de Aventura", "Turismo Gastronomico",
            "Turismo Nautico", "Turismo Rural"). No distingue mayúsculas.
    """
    try:
        engine = crear_engine()
        df = pd.read_sql(
            text("""
                SELECT DISTINCT municipio, tipo_turismo_predominante,
                       AVG(visitantes)::int AS visitantes_promedio
                FROM public.turismo_municipal
                WHERE LOWER(tipo_turismo_predominante) LIKE LOWER(:tipo)
                GROUP BY municipio, tipo_turismo_predominante
                ORDER BY visitantes_promedio DESC;
            """),
            engine,
            params={"tipo": f"%{tipo.strip()}%"},
        )
        if df.empty:
            tipos_disponibles = [
                "Ecoturismo", "Turismo Cultural", "Turismo Religioso",
                "Turismo de Aventura", "Turismo Gastronomico",
                "Turismo Nautico", "Turismo Rural",
            ]
            return _err(
                f"No se encontraron municipios para tipo={tipo!r}. "
                f"Tipos disponibles: {', '.join(tipos_disponibles)}."
            )
        municipios = [
            {
                "municipio":           r["municipio"],
                "tipo_turismo":        r["tipo_turismo_predominante"],
                "visitantes_promedio": int(r["visitantes_promedio"]) if pd.notna(r["visitantes_promedio"]) else 0,
            }
            for _, r in df.iterrows()
        ]
        tool_context.state["last_tipo_turismo"] = tipo
        return _ok(tipo_buscado=tipo, total=len(municipios), municipios=municipios)
    except Exception as exc:
        return _err(f"Error consultando municipios por tipo: {exc}")


def mostrar_contexto(tool_context: ToolContext) -> dict:
    """Muestra el contexto actual de la conversación (state).

    Útil cuando el usuario pregunta "qué estábamos viendo?", "recuerdas
    el último municipio?" o cuando el agente necesita verificar su estado.
    """
    state = tool_context.state
    return _ok(
        last_municipio=state.get(STATE_LAST_MUNI),
        last_anio=state.get(STATE_LAST_ANIO),
        metrica_preferida=state.get(STATE_METRICA, "visitantes"),
        last_tipo_turismo=state.get("last_tipo_turismo"),
    )


def establecer_preferencia(metrica_default: str, tool_context: ToolContext) -> dict:
    """Guarda la métrica preferida del usuario para los siguientes turnos.

    Args:
        metrica_default: Una de "visitantes", "indice_oportunidad",
            "ocupacion_hotelera" o "gasto_estimado". Una vez fijada, las tools
            como top_municipios_turismo la usan automáticamente.
    """
    if metrica_default not in METRICAS_VALIDAS:
        return _err(f"metrica_default debe ser una de: {', '.join(METRICAS_VALIDAS)}.")
    tool_context.state[STATE_METRICA] = metrica_default
    return _ok(
        metrica_preferida=metrica_default,
        mensaje=f"Listo, reportaré por defecto en {metrica_default}.",
    )
