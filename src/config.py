from pathlib import Path
from dotenv import load_dotenv
import os

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "dbname": os.getenv("DB_NAME", "terrarIA"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
}

SCHEMA = os.getenv("DB_SCHEMA", "public")
TABLE = os.getenv("DB_TABLE", "turismo_municipal")
ATTRACTIONS_TABLE = os.getenv("DB_ATTRACTIONS_TABLE", "atractivos_turisticos")
MUNICIPALITIES_TABLE = os.getenv("DB_MUNICIPALITIES_TABLE", "valle_mun")

ANIO = int(os.getenv("ANIO_DEFAULT", "2025"))
MUNICIPIO = os.getenv("MUNICIPIO_DEFAULT", "CALI").upper()
RUTA_SALIDA = Path(os.getenv("RUTA_SALIDA", "outputs"))
if not RUTA_SALIDA.is_absolute():
    RUTA_SALIDA = BASE_DIR / RUTA_SALIDA

RUTA_FRONTEND = BASE_DIR / "frontend"
