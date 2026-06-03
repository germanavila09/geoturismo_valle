"""Tools de visualización del agente ADK del Observatorio GeoTurismo.

Genera gráficas con Seaborn/Matplotlib y las guarda como ADK Artifacts (PNG).
Mismo patrón de caché por sesión que GeoSalud:
  - Nombre de archivo determinista basado en parámetros.
  - Hit  → devuelve referencia sin tocar la DB.
  - Miss → genera, guarda como artifact ADK y registra en state["_chart_cache"].
"""

from __future__ import annotations

import io
import sys
from pathlib import Path
from typing import Any, Callable

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

sns.set_theme(style="whitegrid", palette="tab10")

from google.adk.tools import ToolContext
from google.genai import types as genai_types
from sqlalchemy import text

from src.db import crear_engine

_CACHE_STATE_KEY = "_chart_cache"


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


def _norm_list(municipios: list[str] | str) -> list[str]:
    if isinstance(municipios, str):
        municipios = municipios.replace(" y ", ",").split(",")
    vistos: set[str] = set()
    result: list[str] = []
    for m in municipios:
        u = _norm(str(m))
        if u and u not in vistos:
            vistos.add(u)
            result.append(u)
    return result


def _fig_to_bytes(fig) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, bbox_inches="tight")
    plt.close("all")
    return buf.getvalue()


def _slug(municipios: list[str]) -> str:
    return "-".join(sorted(municipios))[:60]


def _cargar_turismo() -> pd.DataFrame:
    engine = crear_engine()
    return pd.read_sql(
        text("""
            SELECT municipio, anio, visitantes, atractivos,
                   ocupacion_hotelera, gasto_estimado,
                   indice_oportunidad_turistica, tipo_turismo_predominante
            FROM public.turismo_municipal
            ORDER BY municipio, anio;
        """),
        engine,
    )


def _cargar_atractivos() -> pd.DataFrame:
    engine = crear_engine()
    return pd.read_sql(
        text("SELECT municipio, nombre, tipo_turismo, tipo_secundario FROM public.atractivos_turisticos;"),
        engine,
    )


# ── Caché de gráficas ─────────────────────────────────────────────────────────

async def _get_or_create_artifact(
    tool_context: ToolContext,
    filename: str,
    fig_factory: Callable,
) -> dict:
    cache: dict = tool_context.state.setdefault(_CACHE_STATE_KEY, {})
    if filename in cache:
        return {"artifact_filename": filename, "artifact_version": cache[filename],
                "size_bytes": None, "reutilizada": True}
    fig = fig_factory()
    png = _fig_to_bytes(fig)
    part = genai_types.Part.from_bytes(data=png, mime_type="image/png")
    version = await tool_context.save_artifact(filename=filename, artifact=part)
    cache[filename] = version
    tool_context.state[_CACHE_STATE_KEY] = cache
    return {"artifact_filename": filename, "artifact_version": version,
            "size_bytes": len(png), "reutilizada": False}


# ── Tools de visualización ────────────────────────────────────────────────────

async def grafica_visitantes_por_anio(tool_context: ToolContext) -> dict:
    """Gráfica de barras con el total de visitantes del Valle del Cauca por año.

    Útil para "tendencia anual", "evolución general del turismo",
    "cómo ha crecido el turismo en el Valle".
    """
    try:
        filename = "visitantes_por_anio.png"

        def _make():
            df = _cargar_turismo()
            resumen = df.groupby("anio", as_index=False)["visitantes"].sum()
            fig, ax = plt.subplots(figsize=(9, 5))
            sns.barplot(data=resumen, x="anio", y="visitantes", ax=ax, palette="Blues_d")
            ax.set_title("Total de visitantes por año — Valle del Cauca", fontsize=13)
            ax.set_xlabel("Año")
            ax.set_ylabel("Visitantes")
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{int(x):,}"))
            plt.tight_layout()
            return fig

        meta = await _get_or_create_artifact(tool_context, filename, _make)
        return _ok(grafica="visitantes_por_anio",
                   descripcion="Total de visitantes por año en el Valle del Cauca", **meta)
    except Exception as exc:
        return _err(f"Error generando gráfica de visitantes por año: {exc}")


async def grafica_top_municipios(
    anio: int,
    tool_context: ToolContext,
    n: int = 10,
    metrica: str = "",
) -> dict:
    """Gráfica de barras horizontales con el top-N municipios de un año.

    Args:
        anio: Año a graficar (2022-2025).
        n: Cantidad de municipios (1-29). Default 10.
        metrica: "visitantes", "indice_oportunidad", "ocupacion_hotelera" o
            "gasto_estimado". Si llega vacía se usa state.metrica_preferida.

    Útil para "muéstrame los más visitados", "ranking visual",
    "top en gráfica", "quién tiene mejor índice".
    """
    try:
        if not metrica:
            metrica = tool_context.state.get("metrica_preferida", "visitantes")
        col_map = {
            "visitantes":         "visitantes",
            "indice_oportunidad": "indice_oportunidad_turistica",
            "ocupacion_hotelera": "ocupacion_hotelera",
            "gasto_estimado":     "gasto_estimado",
        }
        if metrica not in col_map:
            return _err(f"metrica debe ser una de: {', '.join(col_map)}.")
        n = max(1, min(int(n), 29))
        anio = int(anio)
        col = col_map[metrica]
        filename = f"top{n}_{metrica}_{anio}.png"

        def _make():
            df = _cargar_turismo()
            sub = df[df["anio"] == anio].nlargest(n, col)[["municipio", col]].copy()
            etiq = {
                "visitantes": "Visitantes",
                "indice_oportunidad_turistica": "Índice de oportunidad (0-1)",
                "ocupacion_hotelera": "Ocupación hotelera (%)",
                "gasto_estimado": "Gasto estimado (COP miles)",
            }
            fig, ax = plt.subplots(figsize=(10, max(4, n * 0.45)))
            sns.barplot(data=sub, y="municipio", x=col, ax=ax, palette="viridis")
            ax.set_title(f"Top {n} municipios por {metrica} — {anio}", fontsize=12)
            ax.set_xlabel(etiq.get(col, metrica))
            ax.set_ylabel("")
            plt.tight_layout()
            return fig

        meta = await _get_or_create_artifact(tool_context, filename, _make)
        tool_context.state["last_anio"] = anio
        return _ok(grafica="top_municipios", anio=anio, n=n, metrica=metrica,
                   descripcion=f"Top {n} municipios por {metrica} en {anio}", **meta)
    except Exception as exc:
        return _err(f"Error generando gráfica top municipios: {exc}")


async def grafica_serie_municipio(municipio: str, tool_context: ToolContext) -> dict:
    """Gráfica de línea con la serie histórica de visitantes de un municipio (2022-2025).

    Args:
        municipio: Nombre del municipio (ej. "CALI"). Se normaliza a mayúsculas.

    Útil para "evolución histórica de X", "cómo ha crecido X",
    "muéstrame el gráfico de X en el tiempo".
    """
    try:
        muni = _norm(municipio)
        filename = f"serie_{muni.lower().replace(' ', '_')}.png"

        def _make():
            df = _cargar_turismo()
            sub = df[df["municipio"] == muni].sort_values("anio")
            if sub.empty:
                raise ValueError(f"No hay datos para {muni!r}.")
            fig, ax = plt.subplots(figsize=(9, 5))
            ax.plot(sub["anio"], sub["visitantes"], marker="o", linewidth=2, color="steelblue")
            ax.fill_between(sub["anio"], sub["visitantes"], alpha=0.15, color="steelblue")
            ax.set_title(f"Evolución de visitantes — {muni}", fontsize=12)
            ax.set_xlabel("Año")
            ax.set_ylabel("Visitantes")
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{int(x):,}"))
            plt.tight_layout()
            return fig

        meta = await _get_or_create_artifact(tool_context, filename, _make)
        tool_context.state["last_municipio"] = muni
        return _ok(grafica="serie_municipio", municipio=muni,
                   descripcion=f"Serie histórica de visitantes en {muni}", **meta)
    except Exception as exc:
        return _err(f"Error generando serie del municipio: {exc}")


async def grafica_series_municipios(
    municipios: list[str],
    tool_context: ToolContext,
    metrica: str = "",
) -> dict:
    """Gráfica comparativa de la serie histórica para varios municipios.

    Args:
        municipios: Lista de municipios a comparar (ej. ["CALI", "PALMIRA"]).
            Máximo 12 por legibilidad.
        metrica: "visitantes" o "indice_oportunidad". Default "visitantes".

    Útil para "compara Cali y Palmira", "evolución de varios municipios".
    """
    try:
        if not municipios:
            return _err("Debes enviar al menos un municipio.")
        if not metrica:
            metrica = tool_context.state.get("metrica_preferida", "visitantes")
        col_map = {"visitantes": "visitantes", "indice_oportunidad": "indice_oportunidad_turistica"}
        if metrica not in col_map:
            metrica = "visitantes"
        col = col_map[metrica]

        munis = _norm_list(municipios)[:12]
        filename = f"series_{_slug(munis)}_{metrica}.png"

        def _make():
            df = _cargar_turismo()
            sub = df[df["municipio"].isin(munis)].sort_values(["municipio", "anio"])
            if sub.empty:
                raise ValueError("No hay datos para los municipios solicitados.")
            g = sns.relplot(data=sub, x="anio", y=col, hue="municipio",
                            kind="line", marker="o", height=5, aspect=2.0)
            g.set_axis_labels("Año", "Visitantes" if metrica == "visitantes" else "Índice oportunidad")
            g.figure.suptitle(f"Evolución de {metrica} por municipio", y=1.02)
            g.legend.set_title("Municipio")
            return g

        meta = await _get_or_create_artifact(tool_context, filename, _make)
        if munis:
            tool_context.state["last_municipio"] = munis[-1]
        return _ok(grafica="series_municipios", municipios=munis, metrica=metrica,
                   descripcion=f"Serie comparativa de {metrica} para {len(munis)} municipios", **meta)
    except Exception as exc:
        return _err(f"Error generando series comparativas: {exc}")


async def grafica_distribucion_tipo_turismo(tool_context: ToolContext) -> dict:
    """Gráfica de barras con la distribución de atractivos turísticos por tipo.

    Muestra cuántos atractivos hay de cada categoría (Ecoturismo,
    Turismo Cultural, Religioso, de Aventura, etc.) en el Valle del Cauca.

    Útil para "qué tipos de turismo hay", "distribución de atractivos",
    "cuántos sitios de ecoturismo existen".
    """
    try:
        filename = "distribucion_tipo_turismo.png"

        def _make():
            df = _cargar_atractivos()
            conteo = df["tipo_turismo"].value_counts().reset_index()
            conteo.columns = ["tipo_turismo", "cantidad"]
            fig, ax = plt.subplots(figsize=(10, 5))
            sns.barplot(data=conteo, x="tipo_turismo", y="cantidad", ax=ax, palette="Set2")
            ax.set_title("Distribución de atractivos turísticos por tipo — Valle del Cauca", fontsize=12)
            ax.set_xlabel("")
            ax.set_ylabel("Número de atractivos")
            plt.xticks(rotation=30, ha="right")
            plt.tight_layout()
            return fig

        meta = await _get_or_create_artifact(tool_context, filename, _make)
        return _ok(grafica="distribucion_tipo_turismo",
                   descripcion="Distribución de atractivos por tipo de turismo", **meta)
    except Exception as exc:
        return _err(f"Error generando distribución por tipo: {exc}")


async def grafica_radar_municipio(municipio: str, tool_context: ToolContext) -> dict:
    """Gráfica de radar (spider) con los indicadores normalizados de un municipio en 2024.

    Muestra visitantes, ocupación hotelera, gasto estimado, seguridad
    e índice de oportunidad en escala 0-1.

    Args:
        municipio: Nombre del municipio (ej. "CALI").

    Útil para "perfil turístico de X", "fortalezas y debilidades de X",
    "radar de X", "diagnóstico de X".
    """
    try:
        muni = _norm(municipio)
        filename = f"radar_{muni.lower().replace(' ', '_')}_2024.png"

        def _make():
            df = _cargar_turismo()
            sub = df[(df["municipio"] == muni) & (df["anio"] == 2024)]
            if sub.empty:
                raise ValueError(f"No hay datos de 2024 para {muni!r}.")
            r = sub.iloc[0]
            dims = df[df["anio"] == 2024]

            def norm_col(col):
                mn, mx = dims[col].min(), dims[col].max()
                return (r[col] - mn) / (mx - mn) if mx > mn else 0.0

            categorias = ["Visitantes", "Ocup. Hotelera", "Gasto", "Seguridad", "Índice Oport."]
            valores = [
                norm_col("visitantes"),
                norm_col("ocupacion_hotelera"),
                norm_col("gasto_estimado"),
                norm_col("indice_seguridad"),
                norm_col("indice_oportunidad_turistica"),
            ]
            import numpy as np
            N = len(categorias)
            angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
            valores_cierre = valores + [valores[0]]
            angles_cierre  = angles  + [angles[0]]

            fig, ax = plt.subplots(figsize=(6, 6), subplot_kw={"polar": True})
            ax.plot(angles_cierre, valores_cierre, "o-", linewidth=2, color="steelblue")
            ax.fill(angles_cierre, valores_cierre, alpha=0.2, color="steelblue")
            ax.set_thetagrids(np.degrees(angles), categorias, fontsize=10)
            ax.set_ylim(0, 1)
            ax.set_title(f"Perfil turístico — {muni} (2024)", fontsize=12, pad=20)
            plt.tight_layout()
            return fig

        meta = await _get_or_create_artifact(tool_context, filename, _make)
        tool_context.state["last_municipio"] = muni
        return _ok(grafica="radar_municipio", municipio=muni,
                   descripcion=f"Radar de indicadores turísticos normalizados para {muni} en 2024", **meta)
    except Exception as exc:
        return _err(f"Error generando radar del municipio: {exc}")
