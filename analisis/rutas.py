"""Rutas compartidas de los análisis de turismo de GeoTurismo.

Reemplaza las rutas fijas de la sesión anterior (/sessions/.../mnt/...) por rutas
relativas al laboratorio, para que los scripts corran en cualquier equipo.

Las fuentes (RNT, reportes de emergencia) se buscan, en orden, en:
  1. Las carpetas de la variable de entorno TURISMO_FUENTES (separadas por ';' en Windows).
  2. geoturismo/fuentes/turismo/
  3. georiesgo/docs/  (donde ya están 'rnt valle.xlsx' y 'reportes_emergencia_2026-09-01.xlsx')
"""
import os
from pathlib import Path

ANALISIS = Path(__file__).resolve().parent
GEOTURISMO = ANALISIS.parent
LAB = GEOTURISMO.parent.parent
GEORIESGO = LAB / "observatorios" / "georiesgo"

CARPETAS_FUENTES = [Path(p) for p in os.environ.get("TURISMO_FUENTES", "").split(os.pathsep) if p] + [
    GEOTURISMO / "fuentes" / "turismo",
    GEORIESGO / "docs",
]


def fuente(nombre: str) -> str:
    """Ruta del archivo fuente; si no existe en ninguna carpeta, devuelve la ruta esperada."""
    for carpeta in CARPETAS_FUENTES:
        ruta = carpeta / nombre
        if ruta.exists():
            return str(ruta)
    return str(GEOTURISMO / "fuentes" / "turismo" / nombre)


if __name__ == "__main__":
    for n in ["rnt valle.xlsx", "reportes_emergencia_2026-09-01.xlsx", "reportes_emergencia_2026-09-03.xlsx"]:
        r = fuente(n)
        print(("OK      " if Path(r).exists() else "FALTA   ") + r)
    print(("OK      " if (GEORIESGO / "fuentes" / "municipios_valle.geojson").exists() else "FALTA   ") + str(GEORIESGO / "fuentes" / "municipios_valle.geojson"))
