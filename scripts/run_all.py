import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.pipeline import ejecutar


def main():
    parser = argparse.ArgumentParser(description="Pipeline GeoTurismo")
    parser.add_argument("--anio", type=int, default=None)
    parser.add_argument("--municipio", type=str, default=None)
    parser.add_argument("--salida", type=str, default=None)
    args = parser.parse_args()
    resultado = ejecutar(anio=args.anio, municipio=args.municipio, ruta_salida=args.salida)
    export = resultado.get("ruta_frontend_data", {})
    if isinstance(export, dict):
        print("GeoTurismo actualizado")
        print(f"Municipios agregados: {export.get('municipios_count', 0)}")
        print(f"Atractivos leidos en base: {export.get('atractivos_db_count', 0)}")
        print(f"Atractivos exportados al mapa: {export.get('atractivos_count', 0)}")
        print(f"Tipos de turismo: {export.get('tipos_count', 0)}")
        print(f"Poligonos municipales: {export.get('poligonos_count', 0)}")
        print(f"Datos frontend: {export.get('data')}")
        print(f"Poligonos frontend: {export.get('municipios')}")


if __name__ == "__main__":
    main()
