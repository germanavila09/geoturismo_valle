import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.db import crear_engine
from src.config import ATTRACTIONS_TABLE, MUNICIPALITIES_TABLE, SCHEMA, TABLE


def main():
    engine = crear_engine()
    with engine.connect() as conn:
        version = conn.exec_driver_sql("SELECT version()").scalar()
        tablas = [TABLE, ATTRACTIONS_TABLE, MUNICIPALITIES_TABLE]
        resumen = []
        for tabla in tablas:
            existe = conn.exec_driver_sql(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = %s AND table_name = %s
                )
                """,
                (SCHEMA, tabla),
            ).scalar()
            if not existe:
                resumen.append((tabla, "no existe", 0, []))
                continue

            total = conn.exec_driver_sql(f'SELECT COUNT(*) FROM "{SCHEMA}"."{tabla}"').scalar()
            columnas = conn.exec_driver_sql(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = %s AND table_name = %s
                ORDER BY ordinal_position
                """,
                (SCHEMA, tabla),
            ).scalars().all()
            resumen.append((tabla, "ok", total, columnas))

    print("Conexion OK")
    print(version)
    for tabla, estado, total, columnas in resumen:
        print(f"\nTabla: {SCHEMA}.{tabla} - {estado}")
        if estado == "ok":
            print(f"Registros: {total}")
            print("Columnas:", ", ".join(columnas))


if __name__ == "__main__":
    main()
