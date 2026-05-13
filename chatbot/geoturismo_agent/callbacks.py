"""Callbacks de logging compartidos por todos los agentes ADK del Observatorio GeoTurismo.

Cada llamada a una tool se registra como línea JSON en
outputs/adk_tool_calls.log — útil para auditar invocaciones sin depender de adk web.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

_LOG_FILE = Path(__file__).resolve().parents[3] / "outputs" / "adk_tool_calls.log"
_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

_logger = logging.getLogger("observatorio_geoturismo.tools")
_logger.setLevel(logging.INFO)
if not _logger.handlers:
    _handler = logging.FileHandler(_LOG_FILE, encoding="utf-8")
    _handler.setFormatter(logging.Formatter("%(message)s"))
    _logger.addHandler(_handler)


def _log_event(event: str, **fields: Any) -> None:
    record = {
        "ts": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "event": event,
        **fields,
    }
    _logger.info(json.dumps(record, ensure_ascii=False, default=str))


def before_tool(tool, args, tool_context) -> None:
    _log_event(
        "tool_call",
        agent=getattr(tool_context, "agent_name", None),
        tool=tool.name,
        args=args,
        invocation_id=getattr(tool_context, "invocation_id", None),
    )
    return None


def after_tool(tool, args, tool_context, tool_response) -> None:
    is_dict = isinstance(tool_response, dict)
    _log_event(
        "tool_response",
        agent=getattr(tool_context, "agent_name", None),
        tool=tool.name,
        status=tool_response.get("status") if is_dict else None,
        response_keys=list(tool_response.keys()) if is_dict else None,
        invocation_id=getattr(tool_context, "invocation_id", None),
    )
    return None
