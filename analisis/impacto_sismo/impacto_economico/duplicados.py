"""Deteccion de doble notificacion en la base de reportes empresariales.

POR QUE IMPORTA
Si un mismo negocio reporta dos veces, cuenta dos veces en el total, dos veces
en su municipio y dos veces en cada porcentaje. La deduplicacion inicial fue
conservadora —solo fusiono 131 de 14.372 registros usando NIT o nombre
exacto— y dejaba pasar el caso mas comun: la misma persona que vuelve a llenar
el formulario y escribe el nombre distinto.

============================ DOS ERRORES A EVITAR ============================

1. FUSIONAR DE MENOS. Es lo que hacia la version anterior.

2. FUSIONAR DE MAS. Un primer intento con similitud difusa de razon social y
   cierre transitivo produjo un grupo de 200 reportes con 199 telefonos
   distintos en 13 municipios. El encadenamiento («A se parece a B, B a C»)
   une negocios que no tienen nada que ver. Tambien fallaba agrupar por
   «razon social + municipio»: los grupos mas grandes eran AGROPECUARIA,
   NINGUNO, VENDEDOR AMBULANTE y COMERCIANTE — personas que describieron su
   oficio en vez de nombrar un negocio.

============================ LA SEÑAL Y SU GUARDA ============================

Se agrupa solo por identificadores fuertes: telefono, correo, NIT y documento.
Pero compartir un telefono no basta, porque aparece un tercer patron:

   · un telefono en 107 reportes, 15 municipios, 176 razones sociales
   · un correo en 35 reportes, 1 municipio, 35 negocios y 26 documentos

Eso no es duplicidad: es un GESTOR que diligencio el formulario para muchos
negocios y puso sus propios datos de contacto. Colapsarlos borraria 106
establecimientos reales.

Un grupo se acepta como duplicado solo si ademas es coherente como una sola
unidad economica:
   · a lo sumo un numero de documento distinto, y
   · a lo sumo dos razones sociales distintas

Si no cumple, se marca como patron de gestor y NO se fusiona; se cuenta aparte
porque tambien es informacion util sobre como se levanto el registro.

Los campos de contacto se usan SOLO para detectar. No se publican, no salen en
ningun archivo de resultados y no aparecen en el informe.
"""
import json
import re
import unicodedata
import warnings

import pandas as pd

warnings.filterwarnings("ignore")

import sys as _sys; from pathlib import Path as _Path
_sys.path.insert(0, str(next(p for p in _Path(__file__).resolve().parents if (p / "rutas.py").is_file())))
from rutas import fuente, GEORIESGO  # rutas relativas del laboratorio (antes /sessions/.../mnt)
RUTA = fuente("reportes_emergencia_2026-09-01.xlsx")
df = pd.read_excel(RUTA, sheet_name="Reportes").reset_index(drop=True)
N0 = len(df)

MAX_DOCS = 1        # documentos distintos tolerados dentro de un grupo
MAX_NOMBRES = 2     # razones sociales distintas toleradas


def norm(s):
    if pd.isna(s):
        return ""
    s = unicodedata.normalize("NFD", str(s).replace("�", "n").upper())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9 ]", " ", s)).strip()


def dig(s):
    if pd.isna(s):
        return ""
    d = re.sub(r"\D", "", str(s))
    return d[-10:] if len(d) >= 10 else d


df["_tel"] = df["Teléfono de contacto"].map(dig)
df["_mail"] = df["Correo electrónico de contacto"].map(
    lambda x: str(x).strip().lower() if pd.notna(x) else "")
df["_nit"] = df["NIT"].map(dig)
df["_doc"] = df["Documento de identificación"].map(dig)
df["_emp"] = df["Empresa"].map(norm)
df["_mun"] = df["Municipio"].map(norm)

padre = list(range(N0))


def raiz(a):
    while padre[a] != a:
        padre[a] = padre[padre[a]]
        a = padre[a]
    return a


def unir(a, b):
    ra, rb = raiz(a), raiz(b)
    if ra != rb:
        padre[max(ra, rb)] = min(ra, rb)


def coherente(sub):
    """¿El grupo puede ser un solo establecimiento?"""
    docs = sub["_doc"][sub["_doc"].str.len() >= 6].nunique()
    noms = sub["_emp"][sub["_emp"].str.len() >= 4].nunique()
    return docs <= MAX_DOCS and noms <= MAX_NOMBRES


SENALES = [("teléfono", "_tel", 7), ("correo", "_mail", 5),
           ("NIT", "_nit", 7), ("documento", "_doc", 6)]

detalle, gestores = {}, []
for etiqueta, col, minlen in SENALES:
    base = df[df[col].str.len() >= minlen]
    if col == "_mail":
        base = base[base._mail.str.contains("@", na=False)]
    ok = extra = desc = 0
    for val, idxs in base.groupby(col).indices.items():
        if len(idxs) < 2:
            continue
        sub = df.loc[idxs]
        if not coherente(sub):
            desc += 1
            gestores.append({"senal": etiqueta, "reportes": int(len(idxs)),
                             "municipios": int(sub.Municipio.nunique()),
                             "razones_sociales": int(sub["_emp"].nunique()),
                             "documentos": int(sub["_doc"][sub["_doc"].str.len() >= 6].nunique())})
            continue
        ok += 1
        extra += len(idxs) - 1
        for i in range(1, len(idxs)):
            unir(int(idxs[0]), int(idxs[i]))
    detalle[etiqueta] = {"grupos_duplicados": ok, "registros_extra": extra,
                         "grupos_descartados": desc}

df["_grupo"] = [raiz(i) for i in range(N0)]
tam = df.groupby("_grupo").size()
dup = tam[tam > 1]
extras = int((tam - 1).sum())

# ── efecto sobre las metricas ─────────────────────────────────────────────
# Al colapsar se conserva el reporte con la severidad mas alta: entre dos
# notificaciones del mismo negocio, se asume el peor estado declarado.
ORDEN = {"Crítica": 0, "Grave": 1, "Moderada": 2, "Baja": 3,
         "Sin clasificación": 4, "no_afectado": 5}
df["_o"] = df["Nivel de afectación"].map(ORDEN).fillna(9)
dedup = df.sort_values("_o").drop_duplicates("_grupo", keep="first")

SEV = ["Crítica", "Grave"]


def metricas(d):
    cont = d["Continuidad operativa"].dropna()
    perd = d["Pérdidas económicas"].dropna()
    return {
        "n": len(d),
        "pct_severo": round(100 * d["Nivel de afectación"].isin(SEV).mean(), 2),
        "pct_no_opera": round(100 * (cont == "No puede operar").mean(), 2),
        "pct_no_normal": round(100 * (cont != "Sí, normalmente").mean(), 2),
        "pct_perd_alta": round(100 * perd.isin(
            ["Más de $20 y hasta $100 millones.", "Más de $100 millones."]).mean(), 2),
    }


antes, despues = metricas(df), metricas(dedup)

# ── municipios mas afectados por la duplicidad ────────────────────────────
por_mun = []
for mun, g in df.groupby("Municipio"):
    d = dedup[dedup.Municipio == mun]
    if len(g) < 20:
        continue
    por_mun.append({"municipio": mun, "reportes": len(g), "unicos": len(d),
                    "dup": len(g) - len(d),
                    "pct": round(100 * (len(g) - len(d)) / len(g), 1)})
por_mun.sort(key=lambda x: -x["pct"])

mil = lambda x: f"{x:,}".replace(",", ".")
print("=" * 70)
print(f"REPORTES EN LA BASE          {mil(N0)}")
print(f"ESTABLECIMIENTOS DISTINTOS   {mil(int(df._grupo.nunique()))}")
print(f"DOBLE NOTIFICACIÓN           {mil(extras)}  ({100*extras/N0:.1f} % de la base)")
print("=" * 70)
print(f"\n{'señal':14} {'grupos dup.':>12} {'registros de más':>18} {'descartados':>13}")
for k, v in detalle.items():
    print(f"  {k:12} {v['grupos_duplicados']:>12} {v['registros_extra']:>18} "
          f"{v['grupos_descartados']:>13}")

print(f"\nGRUPOS CON PATRÓN DE GESTOR (no se fusionan): {len(gestores)}")
for g in sorted(gestores, key=lambda x: -x["reportes"])[:5]:
    print(f"  {g['reportes']:4} reportes · {g['municipios']:2} municipios · "
          f"{g['razones_sociales']:3} razones sociales  ({g['senal']})")

print(f"\nTAMAÑO DE LOS GRUPOS DUPLICADOS ({mil(len(dup))} grupos)")
for t, c in dup.value_counts().sort_index().items():
    print(f"  {t} reportes del mismo establecimiento : {mil(c)}")

print("\nEFECTO SOBRE LAS MÉTRICAS")
print(f"  {'indicador':22} {'con duplicados':>15} {'sin duplicados':>15} {'dif':>7}")
for k in ["n", "pct_severo", "pct_no_opera", "pct_no_normal", "pct_perd_alta"]:
    a, b = antes[k], despues[k]
    d = f"{b-a:+.2f}" if k != "n" else f"{b-a:+,}".replace(",", ".")
    print(f"  {k:22} {mil(a) if k=='n' else f'{a:.2f} %':>15} "
          f"{mil(b) if k=='n' else f'{b:.2f} %':>15} {d:>7}")

print("\nMUNICIPIOS CON MÁS DOBLE NOTIFICACIÓN (de 20 reportes en adelante)")
for m in por_mun[:8]:
    print(f"  {m['municipio'][:20]:22} {m['reportes']:5} → {m['unicos']:5}  "
          f"({m['dup']} duplicados, {m['pct']} %)")

json.dump({"n0": N0, "n_unicos": int(df._grupo.nunique()), "extras": extras,
           "pct": round(100 * extras / N0, 1), "senales": detalle,
           "gestores": len(gestores),
           "gestor_max": max((g["reportes"] for g in gestores), default=0),
           "gestor_detalle": sorted(gestores, key=lambda x: -x["reportes"])[:5],
           "tam_grupos": {int(k): int(v) for k, v in dup.value_counts().sort_index().items()},
           "max_grupo": int(tam.max()), "n_grupos_dup": int(len(dup)),
           "antes": antes, "despues": despues, "por_municipio": por_mun},
          open("duplicados.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# Solo se guardan columnas NO sensibles del conjunto depurado.
COLS = ["Número de reporte", "Municipio", "Actividad económica/sector",
        "Tamaño de empresa", "Continuidad operativa", "Pérdidas económicas",
        "Empleos afectados o en riesgo", "Principal necesidad",
        "Apoyo financiero", "Nivel de afectación"]
dedup[COLS].to_pickle("dedup.pkl")
print(f"\ndedup.pkl guardado · {len(dedup)} filas · solo columnas no sensibles")
