"""
TerrarIA - Observatorio GeoTurismo
Migración: agrega clasificación por tipo de turismo.

Cambios en BD:
  - atractivos_turisticos: columnas tipo_turismo, tipo_secundario
  - turismo_municipal:     columna tipo_turismo_predominante

Uso:
    python scripts/agregar_tipo_turismo.py
"""

import os
import sys
import psycopg2

DB_HOST     = os.getenv("DB_HOST",     "localhost")
DB_PORT     = os.getenv("DB_PORT",     "5432")
DB_NAME     = os.getenv("DB_NAME",     "terrarIA")
DB_USER     = os.getenv("DB_USER",     "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

# ── Clasificación manual por id de atractivo ──────────────────────────────────
# Fuente: análisis de actividades y nombre de cada sitio.
# Categorías:
#   Ecoturismo              – naturaleza, senderismo, avistamiento, reservas
#   Turismo de Aventura     – deportes extremos, parapente, buceo, trekking técnico
#   Turismo Nautico         – deportes náuticos, acuáticos, pesca deportiva
#   Turismo Cultural        – museos, arqueología, arte, historia, literatura
#   Turismo Religioso       – iglesias, basílicas, peregrinaciones
#   Turismo Gastronomico    – gastronomía local, enología, vinos
#   Turismo Rural           – campo, cabalgatas, haciendas vivas, agroturismo
#
# Formato: nombre_parcial → (tipo_turismo, tipo_secundario | None)
# Se usa búsqueda ILIKE %nombre_parcial% para mayor robustez.

CLASIFICACION_NOMBRE = [
    # ── Ecoturismo ────────────────────────────────────────────────────────
    ("Piedras de Moler",            ("Ecoturismo",           "Turismo Rural")),
    ("Uramba",                      ("Ecoturismo",           "Turismo de Aventura")),
    ("San Cipriano",                ("Ecoturismo",           "Turismo de Aventura")),
    ("Isla de Malpelo",             ("Turismo de Aventura",  "Ecoturismo")),
    ("Heliconias",                  ("Ecoturismo",           None)),
    ("Charco El Oasis",             ("Ecoturismo",           None)),
    ("7 Charcos",                   ("Ecoturismo",           "Turismo de Aventura")),
    ("Los Paraguas",                ("Ecoturismo",           None)),
    ("Cascada El Salto",            ("Ecoturismo",           None)),
    ("Puente Piedra",               ("Ecoturismo",           None)),
    ("El Vinculo",                  ("Ecoturismo",           None)),
    ("Parque Regional",             ("Ecoturismo",           None)),
    ("Bitaco",                      ("Ecoturismo",           "Turismo Rural")),
    ("Piedra Pintada",              ("Ecoturismo",           None)),
    ("Pico de Loro",                ("Ecoturismo",           "Turismo de Aventura")),
    ("Ecoparque",                   ("Ecoturismo",           None)),
    ("Mariposario",                 ("Ecoturismo",           None)),
    ("Jardin Botanico",             ("Ecoturismo",           None)),
    ("Bosque de Yotoco",            ("Ecoturismo",           None)),
    ("Dapa",                        ("Ecoturismo",           "Turismo Rural")),
    ("Zoologico",                   ("Ecoturismo",           None)),
    # ── Turismo de Aventura ───────────────────────────────────────────────
    ("Wayra",                       ("Turismo de Aventura",  "Ecoturismo")),
    ("Parapente",                   ("Turismo de Aventura",  None)),
    # ── Turismo Náutico ───────────────────────────────────────────────────
    ("Lago Calima",                 ("Turismo Nautico",      "Turismo de Aventura")),
    ("Lago Dulce",                  ("Turismo Nautico",      None)),
    # ── Turismo Cultural ──────────────────────────────────────────────────
    ("Museo Arqueologico",          ("Turismo Cultural",     None)),
    ("Casa del Virrey",             ("Turismo Cultural",     None)),
    ("Hacienda El Paraiso",         ("Turismo Cultural",     None)),
    ("Piedechinche",                ("Turismo Cultural",     "Ecoturismo")),
    ("Museo Aereo",                 ("Turismo Cultural",     None)),
    ("Cultura Prehispanica",        ("Turismo Cultural",     None)),
    ("Museo Rayo",                  ("Turismo Cultural",     None)),
    ("Piedra del Sol",              ("Turismo Cultural",     None)),
    ("Mirador Alto",                ("Turismo Rural",        "Ecoturismo")),
    # ── Turismo Religioso ─────────────────────────────────────────────────
    ("Casa Cural",                  ("Turismo Religioso",    "Turismo Cultural")),
    ("Basilica",                    ("Turismo Religioso",    None)),
    ("Capilla de San",              ("Turismo Religioso",    None)),
    ("Iglesia de Nuestra",          ("Turismo Religioso",    None)),
    # ── Turismo Gastronómico ──────────────────────────────────────────────
    ("Cholado",                     ("Turismo Gastronomico", None)),
    ("Uva",                         ("Turismo Gastronomico", "Turismo Rural")),
]

# Tipo predominante por municipio (para turismo_municipal)
# Se calcula automáticamente desde atractivos_turisticos.


def conectar():
    return psycopg2.connect(
        host=DB_HOST, port=int(DB_PORT),
        dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD,
    )


def agregar_columnas(conn):
    cur = conn.cursor()
    cur.execute("""
        ALTER TABLE public.atractivos_turisticos
            ADD COLUMN IF NOT EXISTS tipo_turismo   TEXT,
            ADD COLUMN IF NOT EXISTS tipo_secundario TEXT;
    """)
    cur.execute("""
        ALTER TABLE public.turismo_municipal
            ADD COLUMN IF NOT EXISTS tipo_turismo_predominante TEXT;
    """)
    conn.commit()
    cur.close()
    print("  [OK] Columnas agregadas a las tablas.")


def clasificar_atractivos(conn):
    cur = conn.cursor()
    cur.execute("SELECT id, nombre FROM public.atractivos_turisticos;")
    filas = cur.fetchall()

    actualizados = 0
    sin_clasificar = []

    for id_, nombre in filas:
        tipo = None
        secundario = None
        nombre_norm = (nombre or "").lower()

        for clave, (t, s) in CLASIFICACION_NOMBRE:
            # Normaliza la clave también para comparar sin tildes ni mayúsculas
            clave_norm = clave.lower()
            # Matching flexible: clave sin tildes vs nombre sin tildes
            if _normalizar(clave_norm) in _normalizar(nombre_norm):
                tipo = t
                secundario = s
                break

        if tipo is None:
            sin_clasificar.append((id_, nombre))
            tipo = "Sin clasificar"

        cur.execute(
            """UPDATE public.atractivos_turisticos
               SET tipo_turismo = %s, tipo_secundario = %s
               WHERE id = %s;""",
            (tipo, secundario, id_),
        )
        actualizados += 1

    conn.commit()
    cur.close()

    print(f"  [OK] {actualizados} atractivos clasificados.")
    if sin_clasificar:
        print(f"  [WARN] {len(sin_clasificar)} sin clasificar:")
        for id_, nombre in sin_clasificar:
            print(f"         id={id_} – {nombre}")


def _normalizar(texto):
    reemplazos = str.maketrans("áéíóúàèìòùäëïöüñ", "aeiouaeiouaeioun")
    return texto.translate(reemplazos)


def actualizar_tipo_predominante(conn):
    """
    Calcula el tipo_turismo más frecuente por municipio en atractivos_turisticos
    y lo asigna a turismo_municipal.tipo_turismo_predominante.
    """
    sql_predominante = """
    WITH conteo AS (
        SELECT
            UPPER(municipio) AS municipio,
            tipo_turismo,
            COUNT(*)         AS total
        FROM public.atractivos_turisticos
        WHERE tipo_turismo IS NOT NULL
          AND tipo_turismo <> 'Sin clasificar'
        GROUP BY UPPER(municipio), tipo_turismo
    ),
    ranking AS (
        SELECT *,
               ROW_NUMBER() OVER (PARTITION BY municipio
                                  ORDER BY total DESC) AS rn
        FROM conteo
    )
    UPDATE public.turismo_municipal tm
    SET tipo_turismo_predominante = r.tipo_turismo
    FROM ranking r
    WHERE r.municipio = tm.municipio
      AND r.rn = 1;
    """
    cur = conn.cursor()
    cur.execute(sql_predominante)
    conn.commit()
    cur.close()
    print("  [OK] tipo_turismo_predominante actualizado en turismo_municipal.")


def mostrar_resumen(conn):
    cur = conn.cursor()

    print("\n  Distribucion de tipos de turismo (atractivos):")
    print("  " + "-" * 48)
    cur.execute("""
        SELECT tipo_turismo, COUNT(*) AS n
        FROM public.atractivos_turisticos
        GROUP BY tipo_turismo
        ORDER BY n DESC;
    """)
    for tipo, n in cur.fetchall():
        barra = "#" * n
        print(f"  {tipo or 'NULL':<30} {n:>2}  {barra}")

    print("\n  Tipo predominante por municipio (turismo_municipal):")
    print("  " + "-" * 48)
    cur.execute("""
        SELECT municipio, tipo_turismo_predominante
        FROM public.turismo_municipal
        WHERE anio = 2024
        ORDER BY municipio;
    """)
    for municipio, tipo in cur.fetchall():
        print(f"  {municipio:<30} {tipo or '—'}")

    cur.close()


def main():
    print("=" * 60)
    print("  TerrarIA - Migracion: tipo de turismo")
    print("=" * 60)

    conn = conectar()

    print("\n[1/4] Agregando columnas...")
    agregar_columnas(conn)

    print("[2/4] Clasificando atractivos...")
    clasificar_atractivos(conn)

    print("[3/4] Calculando tipo predominante por municipio...")
    actualizar_tipo_predominante(conn)

    print("[4/4] Resumen:")
    mostrar_resumen(conn)

    conn.close()
    print("\n  Migracion completada.\n")


if __name__ == "__main__":
    main()
