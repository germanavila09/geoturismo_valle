"""Contratos de acciones para controlar la interfaz del Observatorio GeoTurismo.

Funciones puras (sin ADK). Las usa el servidor local para responder sin cuota
y las envuelven las tools ADK de ui_tools.py.
"""

from __future__ import annotations

VALID_YEARS = {2022, 2023, 2024, 2025}

SECTION_LABELS = {
    "dashboard":   "panel de control",
    "indicadores": "indicadores",
    "tendencias":  "tendencias",
    "priorizacion": "priorización",
    "geovisor":    "geovisor",
    "coropletico": "coropléticos",
    "atractivos":  "atractivos turísticos",
}

# Variables disponibles en turismo_municipal
VARIABLES = {
    "visitantes":           "visitantes",
    "atractivos":           "atractivos",
    "ocupacion":            "ocupacion_hotelera",
    "ocupacion_hotelera":   "ocupacion_hotelera",
    "gasto":                "gasto_estimado",
    "gasto_estimado":       "gasto_estimado",
    "seguridad":            "indice_seguridad",
    "indice_seguridad":     "indice_seguridad",
    "indice":               "indice_oportunidad_turistica",
    "oportunidad":          "indice_oportunidad_turistica",
    "indice_oportunidad":   "indice_oportunidad_turistica",
    "indice_oportunidad_turistica": "indice_oportunidad_turistica",
}

GEOVISOR_MODES = {"burbujas", "coropletico", "calor"}


def normalize_year(anio: int | None, default: int = 2024) -> int:
    year = int(anio or default)
    return year if year in VALID_YEARS else default


def normalize_variable(variable: str | None, default: str = "visitantes") -> str:
    key = (variable or default).strip().lower()
    return VARIABLES.get(key, default)


def navigate_action(section: str, anio: int | None = None) -> dict:
    section = section if section in SECTION_LABELS else "dashboard"
    action: dict = {"type": "navigate", "section": section}
    if anio is not None:
        action["anio"] = normalize_year(anio)
    return action


def coropletico_action(
    variable: str = "visitantes",
    anio: int | None = 2024,
    incluir_cali: bool | None = None,
) -> dict:
    action = {
        "type": "show_geovisor",
        "mode": "coropletico",
        "variable": normalize_variable(variable),
        "anio": normalize_year(anio),
    }
    if incluir_cali is not None:
        action["includeCali"] = bool(incluir_cali)
    return action


def geovisor_action(
    mode: str = "burbujas",
    variable: str = "visitantes",
    anio: int | None = 2024,
    incluir_cali: bool | None = None,
) -> dict:
    mode = (mode or "burbujas").strip().lower()
    if mode not in GEOVISOR_MODES:
        mode = "burbujas"
    action = {
        "type": "show_geovisor",
        "mode": mode,
        "variable": normalize_variable(variable),
        "anio": normalize_year(anio),
    }
    if incluir_cali is not None:
        action["includeCali"] = bool(incluir_cali)
    return action
