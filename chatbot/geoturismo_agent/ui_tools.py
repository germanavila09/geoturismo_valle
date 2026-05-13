"""Tools ADK para controlar módulos visuales del Observatorio GeoTurismo.

Devuelven acciones estructuradas que el frontend entiende mediante
window.applyGeoTurismoChatAction(action).
"""

from __future__ import annotations

from typing import Any

from google.adk.tools import ToolContext

from .ui_actions import coropletico_action, geovisor_action, navigate_action


def _ok(mensaje: str, action: dict[str, Any]) -> dict:
    return {"status": "success", "mensaje": mensaje, "actions": [action]}


def abrir_modulo_observatorio(
    modulo: str,
    tool_context: ToolContext,
    anio: int = 0,
) -> dict:
    """Abre un módulo principal del Observatorio GeoTurismo.

    Args:
        modulo: Uno de "dashboard", "indicadores", "tendencias",
            "priorizacion", "geovisor", "coropletico" o "atractivos".
        anio: Año opcional para sincronizar los controles globales.
            Usa 0 si el usuario no pidió un año específico.
    """
    aliases = {
        "panel":        "dashboard",
        "dashboard":    "dashboard",
        "control":      "dashboard",
        "inicio":       "dashboard",
        "indicador":    "indicadores",
        "indicadores":  "indicadores",
        "tendencia":    "tendencias",
        "tendencias":   "tendencias",
        "priorizacion": "priorizacion",
        "prioridad":    "priorizacion",
        "priorizar":    "priorizacion",
        "geovisor":     "geovisor",
        "mapa":         "coropletico",
        "coropletico":  "coropletico",
        "coropleticos": "coropletico",
        "atractivos":   "atractivos",
        "sitios":       "atractivos",
    }
    section = aliases.get((modulo or "").strip().lower(), "dashboard")
    if anio:
        tool_context.state["last_anio"] = int(anio)
    return _ok(f"Listo. Abrí {section}.", navigate_action(section, anio or None))


def mostrar_mapa_coropletico(
    tool_context: ToolContext,
    anio: int = 2024,
    variable: str = "visitantes",
    incluir_cali: bool = True,
) -> dict:
    """Muestra el mapa coroplético del Valle del Cauca con datos de turismo.

    Args:
        anio: Año de consulta (2022-2025).
        variable: "visitantes", "indice_oportunidad", "ocupacion_hotelera"
            o "gasto_estimado".
        incluir_cali: True para incluir Cali, False para excluirlo y mejorar
            la escala de color en los municipios pequeños.
    """
    action = coropletico_action(variable=variable, anio=anio, incluir_cali=incluir_cali)
    tool_context.state["last_anio"] = int(action["anio"])
    tool_context.state["last_ui_module"] = "coropletico"
    return _ok("Listo. Actualicé el mapa coroplético.", action)


def mostrar_geovisor(
    tool_context: ToolContext,
    anio: int = 2024,
    modo: str = "burbujas",
    variable: str = "visitantes",
    incluir_cali: bool = True,
) -> dict:
    """Abre el geovisor y configura modo, variable y año.

    Args:
        anio: Año de consulta (2022-2025).
        modo: "burbujas", "coropletico" o "calor".
        variable: "visitantes", "indice_oportunidad", "ocupacion_hotelera"
            o "gasto_estimado".
        incluir_cali: True para incluir Cali.
    """
    action = geovisor_action(mode=modo, variable=variable, anio=anio, incluir_cali=incluir_cali)
    tool_context.state["last_anio"] = int(action["anio"])
    tool_context.state["last_ui_module"] = "geovisor"
    return _ok("Listo. Actualicé el geovisor.", action)
