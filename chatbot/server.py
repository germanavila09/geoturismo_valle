"""Servidor FastAPI — puente entre el frontend GeoTurismo y el agente ADK.

Endpoints:
  POST /chat            → { session_id, message } → { reply, artifacts, actions }
  GET  /artifacts/{fn}  → sirve el PNG como ADK Artifact
  GET  /health          → estado del servidor

Arranque:
    cd observatorios/geoturismo/chatbot
    uvicorn server:app --host 0.0.0.0 --port 8081 --reload
"""

from __future__ import annotations

import io
import os
import re
import sys
import unicodedata
from pathlib import Path

_CHATBOT_DIR  = Path(__file__).resolve().parent
_PROJECT_ROOT = _CHATBOT_DIR.parent

for _p in (_CHATBOT_DIR, _PROJECT_ROOT):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from dotenv import load_dotenv
load_dotenv(_PROJECT_ROOT / ".env")
load_dotenv(_CHATBOT_DIR / "geoturismo_agent" / ".env", override=False)

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

try:
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.adk.artifacts import InMemoryArtifactService
    from google.genai import types as genai_types
    ADK_AVAILABLE = True
    ADK_IMPORT_ERROR: Exception | None = None
except Exception as exc:
    Runner = None
    InMemorySessionService = None
    InMemoryArtifactService = None
    genai_types = None
    ADK_AVAILABLE = False
    ADK_IMPORT_ERROR = exc

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from geoturismo_agent.ui_actions import coropletico_action, geovisor_action, navigate_action
from geoturismo_agent.tools import (
    listar_municipios as _t_listar,
    consultar_municipio_anio as _t_consultar,
    top_municipios_turismo as _t_top,
    serie_temporal_municipio as _t_serie,
    resumen_anio as _t_resumen,
    atractivos_municipio as _t_atractivos,
    municipios_por_tipo_turismo as _t_tipo,
)

try:
    from geoturismo_agent.agent import root_agent
except Exception as exc:
    root_agent = None
    ADK_AVAILABLE = False
    ADK_IMPORT_ERROR = exc

APP_NAME = "observatorio_geoturismo"
USER_ID  = "frontend_user"

session_service = InMemorySessionService() if ADK_AVAILABLE else None
artifact_service = InMemoryArtifactService() if ADK_AVAILABLE else None
fallback_artifacts: dict[tuple[str, str], bytes] = {}
local_context: dict[str, dict] = {}

runner = (
    Runner(
        agent=root_agent,
        app_name=APP_NAME,
        session_service=session_service,
        artifact_service=artifact_service,
    )
    if ADK_AVAILABLE
    else None
)

app = FastAPI(
    title="Observatorio GeoTurismo — Chatbot API",
    description="Puente entre el dashboard frontend y el agente ADK de turismo.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# ── Schemas ────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    reply: str
    artifacts: list[str]
    session_id: str
    actions: list[dict] = Field(default_factory=list)


# ── Helpers ────────────────────────────────────────────────────────────────────

async def _ensure_session(session_id: str) -> None:
    if session_service is None:
        return
    existing = await session_service.get_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=session_id
    )
    if existing is None:
        await session_service.create_session(
            app_name=APP_NAME, user_id=USER_ID, session_id=session_id
        )


def _chart_cache(state: dict) -> set[str]:
    return set((state or {}).get("_chart_cache", {}).keys())


def _plain(text: str) -> str:
    norm = unicodedata.normalize("NFKD", text.lower())
    return "".join(ch for ch in norm if not unicodedata.combining(ch))


def _fig_to_bytes(fig) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


def _extract_year(text: str) -> int | None:
    m = re.search(r"\b(2022|2023|2024|2025)\b", text)
    return int(m.group(1)) if m else None


def _extract_top_n(text: str, default: int = 5) -> int:
    m = re.search(r"\btop\s*(\d{1,2})\b|\b(\d{1,2})\s+municipios\b", text)
    if not m:
        return default
    return max(1, min(int(m.group(1) or m.group(2)), 29))


def _is_quota_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return "resource_exhausted" in msg or "429" in msg or "quota" in msg


def _extract_actions_from_part(part) -> list[dict]:
    actions: list[dict] = []
    fn_resp = getattr(part, "function_response", None)
    response = getattr(fn_resp, "response", None) if fn_resp else None
    if response is not None and not isinstance(response, dict) and hasattr(response, "model_dump"):
        response = response.model_dump()
    if isinstance(response, dict) and isinstance(response.get("actions"), list):
        actions.extend(a for a in response["actions"] if isinstance(a, dict))
    return actions


# ── Modo local — herramientas directas sin ADK ────────────────────────────────

class _LocalCtx:
    """Duck-type de ToolContext para llamadas locales."""
    def __init__(self) -> None:
        self.state: dict = {}


# Patrones de búsqueda (texto sin tildes, minúsculas) → nombre exacto en DB
_MUNI_PATTERNS: list[tuple[str, str]] = sorted([
    ("calima - el darien",  "CALIMA - EL DARIÉN"),
    ("guadalajara de buga", "GUADALAJARA DE BUGA"),
    ("santiago de cali",    "SANTIAGO DE CALI"),
    ("la cumbre",           "LA CUMBRE"),
    ("la union",            "LA UNIÓN"),
    ("la victoria",         "LA VICTORIA"),
    ("ansermanuevo",        "ANSERMANUEVO"),
    ("buenaventura",        "BUENAVENTURA"),
    ("caicedonia",          "CAICEDONIA"),
    ("cartago",             "CARTAGO"),
    ("dagua",               "DAGUA"),
    ("el cairo",            "EL CAIRO"),
    ("el cerrito",          "EL CERRITO"),
    ("el dovio",            "EL DOVIO"),
    ("ginebra",             "GINEBRA"),
    ("palmira",             "PALMIRA"),
    ("restrepo",            "RESTREPO"),
    ("roldanillo",          "ROLDANILLO"),
    ("sevilla",             "SEVILLA"),
    ("trujillo",            "TRUJILLO"),
    ("vijes",               "VIJES"),
    ("yotoco",              "YOTOCO"),
    ("yumbo",               "YUMBO"),
    ("zarzal",              "ZARZAL"),
    # aliases
    ("cali",     "SANTIAGO DE CALI"),
    ("buga",     "GUADALAJARA DE BUGA"),
    ("calima",   "CALIMA - EL DARIÉN"),
    ("darien",   "CALIMA - EL DARIÉN"),
    ("jamundi",  "JAMUNDÍ"),
    ("guacari",  "GUACARÍ"),
    ("tulua",    "TULUÁ"),
    ("alcala",   "ALCALÁ"),
    ("riofrio",  "RIOFRÍO"),
], key=lambda x: len(x[0]), reverse=True)  # longer patterns first


def _find_muni(text: str) -> str | None:
    for pat, full in _MUNI_PATTERNS:
        if pat in text:
            return full
    return None


_TIPOS_KW: list[tuple[str, str]] = [
    ("ecoturismo",   "Ecoturismo"),
    ("cultural",     "Turismo Cultural"),
    ("religioso",    "Turismo Religioso"),
    ("aventura",     "Turismo de Aventura"),
    ("gastronomic",  "Turismo Gastronomico"),
    ("nautico",      "Turismo Nautico"),
    ("rural",        "Turismo Rural"),
]


def _fv(v: int) -> str:
    return f"{v:,}".replace(",", ".")


def _fmt_local(d: dict) -> str:
    if d.get("status") == "error":
        return d.get("error_message", "No se encontraron datos.")
    d2 = {k: v for k, v in d.items() if k != "status"}

    if "ranking" in d2:
        labels = {"visitantes": "visitantes", "indice_oportunidad": "índice de oportunidad",
                  "ocupacion_hotelera": "ocupación hotelera", "gasto_estimado": "gasto estimado"}
        met = labels.get(d2.get("metrica", ""), d2.get("metrica", ""))
        lines = [f"Top {len(d2['ranking'])} municipios por {met} ({d2['anio']})"]
        for i, r in enumerate(d2["ranking"], 1):
            val = r.get("valor_metrica")
            vs = _fv(int(val)) if val and val > 10 else f"{val:.4f}" if val else "—"
            tipo = f" [{r['tipo_turismo']}]" if r.get("tipo_turismo") else ""
            lines.append(f"{i}. {r['municipio'].title()}{tipo} — {vs}")
        return "\n".join(lines)

    if "serie" in d2:
        lines = [f"Serie histórica de {d2['municipio'].title()} (2022-2025)"]
        for s in d2["serie"]:
            ocu = f", ocupación {s['ocupacion_hotelera']}%" if s.get("ocupacion_hotelera") else ""
            idx = f", índice {s['indice_oportunidad']:.4f}" if s.get("indice_oportunidad") else ""
            lines.append(f"  {s['anio']}: {_fv(s['visitantes'])} visitantes{ocu}{idx}")
        return "\n".join(lines)

    if "total_visitantes" in d2:
        mv = d2.get("municipio_mas_visitantes", {})
        mi = d2.get("municipio_mayor_indice", {})
        dt = d2.get("distribucion_tipos", {})
        tipos_str = ", ".join(f"{k}: {v}" for k, v in dt.items()) if dt else "—"
        return (
            f"Resumen turístico Valle del Cauca — {d2['anio']}\n"
            f"  Total visitantes: {_fv(d2['total_visitantes'])}\n"
            f"  Municipios: {d2['n_municipios']}, ocupación prom: {d2['promedio_ocupacion_hotelera_pct']}%\n"
            f"  Más visitado: {mv.get('nombre','').title()} ({_fv(mv.get('visitantes',0))})\n"
            f"  Mayor índice: {mi.get('nombre','').title()} ({mi.get('indice',0):.4f})\n"
            f"  Tipos: {tipos_str}"
        )

    if "atractivos" in d2 and "total" in d2 and "municipio" in d2:
        lines = [f"Atractivos de {d2['municipio'].title()} ({d2['total']} registros)"]
        for a in d2["atractivos"]:
            tipo = a.get("tipo_turismo", "")
            costo = " — libre" if a.get("costo_entrada") == 0 else f" — ${a['costo_entrada']:,.0f}" if a.get("costo_entrada") else ""
            lines.append(f"  • {a['nombre']} [{tipo}]{costo}")
            if a.get("actividades"):
                lines.append(f"    {a['actividades']}")
        return "\n".join(lines)

    if "municipios" in d2 and "tipo_buscado" in d2:
        lines = [f"Municipios con {d2['tipo_buscado']} ({d2['total']} encontrados)"]
        for m in d2["municipios"]:
            lines.append(f"  • {m['municipio'].title()} — {_fv(m['visitantes_promedio'])} vis./año")
        return "\n".join(lines)

    if "municipios" in d2 and "total" in d2:
        munis = ", ".join(m.title() for m in d2["municipios"])
        return f"El observatorio cubre {d2['total']} municipios:\n{munis}"

    if "visitantes" in d2 and "municipio" in d2 and "anio" in d2:
        lines = [f"{d2['municipio'].title()} — {d2['anio']}"]
        lines.append(f"  Visitantes:  {_fv(d2['visitantes'])}")
        if d2.get("atractivos"):
            lines.append(f"  Atractivos:  {d2['atractivos']}")
        if d2.get("ocupacion_hotelera") is not None:
            lines.append(f"  Ocupación:   {d2['ocupacion_hotelera']}%")
        if d2.get("gasto_estimado_cop"):
            lines.append(f"  Gasto est.:  ${_fv(d2['gasto_estimado_cop'])} COP")
        if d2.get("tipo_turismo_predominante"):
            lines.append(f"  Tipo:        {d2['tipo_turismo_predominante']}")
        return "\n".join(lines)

    return str(d2)


def _local_data_response(req: ChatRequest) -> ChatResponse | None:
    """Resuelve consultas de datos directamente desde la DB, sin pasar por Gemini."""
    text = _plain(req.message)
    anio = _extract_year(text) or 2024
    n    = _extract_top_n(text, default=5)
    ctx  = _LocalCtx()

    if any(w in text for w in ("indice", "oportunidad")):
        metrica = "indice_oportunidad"
    elif any(w in text for w in ("ocupacion", "hotel")):
        metrica = "ocupacion_hotelera"
    elif "gasto" in text:
        metrica = "gasto_estimado"
    else:
        metrica = "visitantes"

    result: dict | None = None

    # Listar municipios
    if ("listar" in text or "lista" in text) and "municipio" in text:
        result = _t_listar(ctx)
    elif any(p in text for p in ("que municipios", "municipios tiene", "municipios cubre", "municipios disponible")):
        result = _t_listar(ctx)

    # Top / ranking
    elif "top" in text or ("ranking" in text) or ("mejores" in text and "municipio" in text) or ("principales" in text and "municipio" in text):
        result = _t_top(anio=anio, tool_context=ctx, n=n, metrica=metrica)

    # Serie temporal
    elif any(w in text for w in ("serie", "tendencia", "evolucion", "historico", "historica", "anos", "por ano")):
        muni = _find_muni(text)
        if muni:
            result = _t_serie(municipio=muni, tool_context=ctx)

    # Atractivos
    elif any(w in text for w in ("atractivo", "que ver", "que visitar", "lugares")):
        muni = _find_muni(text)
        if muni:
            result = _t_atractivos(municipio=muni, tool_context=ctx)

    # Tipo de turismo
    elif any(kw in text for kw, _ in _TIPOS_KW):
        for kw, tipo_full in _TIPOS_KW:
            if kw in text:
                result = _t_tipo(tipo=tipo_full, tool_context=ctx)
                break

    # Resumen anual
    elif any(w in text for w in ("resumen", "panorama", "estadistica", "total")):
        result = _t_resumen(anio=anio, tool_context=ctx)

    # Consulta de indicadores de un municipio específico
    else:
        muni = _find_muni(text)
        if muni:
            result = _t_consultar(municipio=muni, anio=anio, tool_context=ctx)

    if result is None:
        return None
    return ChatResponse(
        reply=_fmt_local(result),
        artifacts=[],
        session_id=req.session_id,
    )


# ── Respuestas locales (sin cuota Gemini) ──────────────────────────────────────

def _local_observatory_action_response(req: ChatRequest) -> ChatResponse | None:
    text = _plain(req.message)
    anio = _extract_year(text)
    include_cali = None
    if any(p in text for p in ("incluye cali", "incluir cali", "con cali")):
        include_cali = True
    elif any(p in text for p in ("sin cali", "excluye cali")):
        include_cali = False

    # Mapa coroplético
    if any(w in text for w in ("mapa", "coropletico", "coropleticos", "valle del cauca")):
        if any(w in text for w in ("visitante", "visita", "turista")):
            variable, label = "visitantes", "visitantes"
        elif any(w in text for w in ("indice", "oportunidad")):
            variable, label = "indice_oportunidad", "índice de oportunidad"
        elif any(w in text for w in ("ocupacion", "hotel")):
            variable, label = "ocupacion_hotelera", "ocupación hotelera"
        elif any(w in text for w in ("gasto")):
            variable, label = "gasto_estimado", "gasto estimado"
        else:
            variable, label = "visitantes", "visitantes"
        action = coropletico_action(variable=variable, anio=anio or 2024, incluir_cali=include_cali)
        return ChatResponse(
            reply=f"Listo. Actualicé el mapa coroplético para {label} en {anio or 2024}.",
            artifacts=[],
            session_id=req.session_id,
            actions=[action],
        )

    # Geovisor
    if any(w in text for w in ("geovisor", "burbujas", "calor")):
        mode = "calor" if "calor" in text else "coropletico" if "coropletico" in text else "burbujas"
        variable = "indice_oportunidad" if "indice" in text else "visitantes"
        action = geovisor_action(mode=mode, variable=variable, anio=anio or 2024, incluir_cali=include_cali)
        return ChatResponse(
            reply=f"Listo. Abrí el geovisor en modo {mode} para {anio or 2024}.",
            artifacts=[],
            session_id=req.session_id,
            actions=[action],
        )

    # Navegación a sección
    section_aliases = [
        (("panel", "dashboard", "inicio"),          "dashboard",    "panel de control"),
        (("indicador", "indicadores"),              "indicadores",  "indicadores"),
        (("priorizacion", "priorizar", "prioridad"), "priorizacion", "priorización"),
        (("tendencia", "tendencias"),               "tendencias",   "tendencias"),
        (("atractivos", "sitios"),                  "atractivos",   "atractivos turísticos"),
    ]
    for words, section, label in section_aliases:
        if any(w in text for w in words):
            action = navigate_action(section, anio)
            return ChatResponse(
                reply=f"Listo. Abrí {label}" + (f" para {anio}." if anio else "."),
                artifacts=[],
                session_id=req.session_id,
                actions=[action],
            )

    return None


def _local_response(req: ChatRequest) -> ChatResponse | None:
    resp = _local_observatory_action_response(req)
    if resp is not None:
        return resp
    return _local_data_response(req)


# ── Endpoints ──────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    payload = {
        "status": "ok",
        "mode": "adk" if ADK_AVAILABLE else "local",
        "agent": getattr(root_agent, "name", "local_fallback"),
        "app": APP_NAME,
    }
    if not ADK_AVAILABLE:
        payload["detail"] = f"ADK no disponible: {ADK_IMPORT_ERROR}"
    return payload


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    # UI y consultas estructuradas se resuelven primero en local para que el
    # asistente funcione aun sin Gemini/ADK o sin cuota disponible.
    local_resp = _local_response(req)
    if local_resp is not None:
        return local_resp

    if not ADK_AVAILABLE or runner is None or session_service is None:
        return ChatResponse(
            reply=(
                "Estoy funcionando en modo local. Puedo responder consultas sobre "
                "municipios, visitantes, atractivos, tipos de turismo, rankings, "
                "series temporales y mapas. Prueba: 'top 5 municipios en 2025', "
                "'municipios con ecoturismo' o 'atractivos de Buga'."
            ),
            artifacts=[],
            session_id=req.session_id,
        )

    await _ensure_session(req.session_id)

    session_before = await session_service.get_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=req.session_id
    )
    cache_before = _chart_cache(getattr(session_before, "state", {}) or {})

    user_msg = genai_types.Content(
        role="user",
        parts=[genai_types.Part.from_text(text=req.message)],
    )

    final_text = ""
    ui_actions: list[dict] = []
    try:
        async for event in runner.run_async(
            user_id=USER_ID,
            session_id=req.session_id,
            new_message=user_msg,
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    ui_actions.extend(_extract_actions_from_part(part))
            if event.is_final_response():
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, "text") and part.text:
                            final_text += part.text
    except Exception as exc:
        print(f"[AGENT ERROR] {type(exc).__name__}: {exc}", flush=True)
        if _is_quota_error(exc):
            # Cuota agotada: intentar resolver localmente (UI + datos DB)
            local_resp = _local_response(req)
            if local_resp is not None:
                return local_resp
            return ChatResponse(
                reply=(
                    "Cuota de Gemini agotada. Puedo responder consultas locales: "
                    "top municipios, serie temporal, atractivos, resumen anual, mapas."
                ),
                artifacts=[],
                session_id=req.session_id,
            )
        raise HTTPException(status_code=500, detail=f"Error en el agente: {exc}")

    if not final_text:
        final_text = "El agente no generó respuesta de texto. Intenta reformular la pregunta."

    session_after = await session_service.get_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=req.session_id
    )
    cache_after = _chart_cache(getattr(session_after, "state", {}) or {})
    new_artifacts = sorted(cache_after - cache_before)

    return ChatResponse(
        reply=final_text,
        artifacts=new_artifacts,
        session_id=req.session_id,
        actions=ui_actions,
    )


@app.get("/artifacts/{filename}")
async def get_artifact(filename: str, session_id: str):
    fallback = fallback_artifacts.get((session_id, filename))
    if fallback is not None:
        return Response(content=fallback, media_type="image/png",
                        headers={"Cache-Control": "private, max-age=3600"})

    if artifact_service is None:
        raise HTTPException(status_code=404, detail="Artifacts no disponibles en modo local.")

    artifact = await artifact_service.load_artifact(
        app_name=APP_NAME, user_id=USER_ID,
        session_id=session_id, filename=filename,
    )
    if artifact is None:
        raise HTTPException(status_code=404, detail=f"Artifact '{filename}' no encontrado.")

    return Response(content=artifact.inline_data.data, media_type="image/png",
                    headers={"Cache-Control": "private, max-age=3600"})


# ── Arranque directo ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("CHATBOT_PORT", "8081"))
    print(f"\n  GeoTurismo Chatbot API  ->  http://localhost:{port}")
    print(f"   Modo   : {'ADK/Gemini' if ADK_AVAILABLE else 'local'}")
    print(f"   Agente : {getattr(root_agent, 'name', 'local_fallback')}")
    print(f"   Docs   : http://localhost:{port}/docs\n")
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=True)
