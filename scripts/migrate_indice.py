"""
TerrarIA - Migración de Base de Datos
Agrega la columna 'indice_oportunidad_turistica' a la tabla 'turismo_municipal'
y calcula sus valores para los registros existentes.

Uso:
    python scripts/migrate_indice.py
"""

import os
import sys
from pathlib import Path
import psycopg2
import pandas as pd

# Asegurar que el directorio raíz está en el path para importar src
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.transform import calcular_indice_oportunidad

# Credenciales desde variables de entorno o valores por defecto
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "terrarIA")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

def conectar():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )

def main():
    print("=" * 60)
    print("  TerrarIA – Migración: Columna de Índice de Oportunidad")
    print("=" * 60)

    try:
        conn = conectar()
        cur = conn.cursor()
    except Exception as e:
        print(f"  [ERROR] No se pudo conectar a la base de datos: {e}")
        sys.exit(1)

    print("\n[1/3] Agregando columna 'indice_oportunidad_turistica' si no existe...")
    try:
        cur.execute("""
            ALTER TABLE public.turismo_municipal
            ADD COLUMN IF NOT EXISTS indice_oportunidad_turistica NUMERIC DEFAULT 0;
        """)
        conn.commit()
        print("  [OK] Columna agregada.")
    except Exception as e:
        print(f"  [ERROR] Al agregar la columna: {e}")
        conn.rollback()
        cur.close()
        conn.close()
        sys.exit(1)

    print("\n[2/3] Cargando y calculando índices para los registros existentes...")
    try:
        df = pd.read_sql("SELECT * FROM public.turismo_municipal;", conn)
        if df.empty:
            print("  [WARN] La tabla turismo_municipal está vacía. Nada que migrar.")
            cur.close()
            conn.close()
            return
        
        # Calcular índices usando la lógica exacta del pipeline
        df_calculado = calcular_indice_oportunidad(df)
        print(f"  [OK] Índices calculados para {len(df_calculado)} filas.")
    except Exception as e:
        print(f"  [ERROR] Al calcular los índices: {e}")
        cur.close()
        conn.close()
        sys.exit(1)

    print("\n[3/3] Guardando índices en la base de datos...")
    try:
        update_sql = """
            UPDATE public.turismo_municipal
            SET indice_oportunidad_turistica = %s
            WHERE id = %s;
        """
        rows_to_update = []
        for _, row in df_calculado.iterrows():
            rows_to_update.append((
                float(row["indice_oportunidad_turistica"]),
                int(row["id"]),
            ))
        
        cur.executemany(update_sql, rows_to_update)
        conn.commit()
        print(f"  [OK] {len(rows_to_update)} filas actualizadas correctamente.")
    except Exception as e:
        print(f"  [ERROR] Al actualizar registros en la base de datos: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

    print("\n" + "=" * 60)
    print("  Migración completada con éxito.")
    print("=" * 60)

if __name__ == "__main__":
    main()
