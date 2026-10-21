"""Analisis de la base de reportes de emergencia empresarial, corte 1-sep-2026.

Reglas que se aplican y por que, para que el informe pueda citarlas:

  · TURISMO = «Alojamiento y servicios de comida» + «Transporte y almacenamiento».
    Es la definicion del informe del 26 de agosto y se conserva para que los dos
    cortes sean comparables. Se declara que es una aproximacion: la actividad
    economica de la fuente no distingue un hotel de una fonda de barrio ni un
    transportador turistico de uno de carga.

  · UNIDAD = establecimiento. Un mismo negocio puede haber reportado dos veces.
    Se deduplica por (NIT) cuando hay NIT, y por (nombre normalizado + municipio)
    cuando no lo hay.

  · Los porcentajes se calculan SOLO sobre quien respondio esa pregunta, y se
    publica la base de cada uno. Varias columnas tienen 20-25% de vacios.
"""
import json, re, unicodedata, warnings
import pandas as pd
warnings.filterwarnings("ignore")

import sys as _sys; from pathlib import Path as _Path
_sys.path.insert(0, str(next(p for p in _Path(__file__).resolve().parents if (p / "rutas.py").is_file())))
from rutas import fuente, GEORIESGO  # rutas relativas del laboratorio (antes /sessions/.../mnt)
RUTA = fuente("reportes_emergencia_2026-09-01.xlsx")
df = pd.read_excel(RUTA, sheet_name="Reportes")

# ── fechas: 861 filas vienen con dia y mes intercambiados ──────────────────
f = pd.to_datetime(df["Fecha de reporte"], errors="coerce")
mal = f > "2026-09-01"
f_corr = f.copy()
f_corr[mal] = f[mal].apply(lambda x: pd.Timestamp(2026, 8, x.month))
df["_fecha"] = f_corr
df["_fecha_corregida"] = mal

def norm(s):
    s = unicodedata.normalize("NFD", str(s or "").upper())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^A-Z0-9 ]", " ", s).strip()

# ── unidad de analisis: establecimiento ────────────────────────────────────
df["_nit"] = df["NIT"].astype(str).str.strip().replace({"nan": ""})
df["_clave"] = df.apply(
    lambda r: f"NIT:{r['_nit']}" if r["_nit"]
    else f"NOM:{norm(r['Empresa']) or norm(r['Nombre completo'])}|{norm(r['Municipio'])}",
    axis=1)

TURISMO = ["Alojamiento y servicios de comida", "Transporte y almacenamiento"]
df["_turismo"] = df["Actividad económica/sector"].isin(TURISMO)
SEVERO = ["Crítica", "Grave"]
df["_severo"] = df["Nivel de afectación"].isin(SEVERO)

est = df.sort_values("Nivel de afectación").drop_duplicates("_clave", keep="first")
tur = df[df["_turismo"]]
tur_est = est[est["_turismo"]]

R = {}
R["total_reportes"] = len(df)
R["total_establecimientos"] = len(est)
R["dup_removidos"] = len(df) - len(est)
R["municipios"] = int(df["Municipio"].nunique())
R["fechas_corregidas"] = int(mal.sum())
R["turismo_reportes"] = len(tur)
R["turismo_establecimientos"] = len(tur_est)
R["turismo_municipios"] = int(tur_est["Municipio"].nunique())
R["turismo_pct_base"] = round(100*len(tur_est)/len(est), 2)

def perfil(d, nombre):
    p = {"n": len(d)}
    for col, etiqueta in [("Nivel de afectación","severidad"),
                          ("Continuidad operativa","continuidad"),
                          ("Pérdidas económicas","perdidas"),
                          ("Empleos afectados o en riesgo","empleos"),
                          ("Tamaño de empresa","tamano")]:
        s = d[col].dropna()
        p[etiqueta] = {"base": len(s), "cuenta": s.value_counts().to_dict()}
    return {nombre: p}

R.update(perfil(est, "todos"))
R.update(perfil(tur_est, "turismo"))

# ── municipios ─────────────────────────────────────────────────────────────
gm = tur_est.groupby("Municipio").agg(
    n=("Número de reporte","size"),
    severos=("_severo","sum")).reset_index()
gm["pct_severo"] = (100*gm.severos/gm.n).round(1)
R["turismo_por_municipio"] = gm.sort_values("severos", ascending=False).to_dict("records")

gt = est.groupby("Municipio").agg(
    n=("Número de reporte","size"),
    severos=("_severo","sum")).reset_index()
gt["pct_severo"] = (100*gt.severos/gt.n).round(1)
R["todos_por_municipio"] = gt.sort_values("severos", ascending=False).to_dict("records")

# ── multirespuesta ─────────────────────────────────────────────────────────
def multi(col, d):
    c = {}
    for v in d[col].dropna():
        for p in re.split(r"[;\n]", str(v)):
            p = p.strip(" .")
            if p: c[p] = c.get(p, 0) + 1
    return dict(sorted(c.items(), key=lambda x: -x[1]))
R["turismo_afectaciones"] = multi("Afectaciones al negocio", tur_est)
R["turismo_necesidades"] = multi("Principal necesidad", tur_est)
R["turismo_apoyo"] = multi("Apoyo financiero", tur_est)

# ── serie temporal ─────────────────────────────────────────────────────────
serie = df[df["_fecha"].notna()].groupby(df["_fecha"].dt.date).size()
R["serie"] = {str(k): int(v) for k, v in serie.items()}
R["cobertura_fecha"] = round(100*df["_fecha"].notna().mean(), 1)

json.dump(R, open("resultados.json","w",encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
est.to_pickle("est.pkl"); tur_est.to_pickle("tur.pkl"); df.to_pickle("df.pkl")

print(f"reportes            {R['total_reportes']:6}")
print(f"establecimientos    {R['total_establecimientos']:6}  (se fusionaron {R['dup_removidos']})")
print(f"turismo · reportes  {R['turismo_reportes']:6}")
print(f"turismo · estableci {R['turismo_establecimientos']:6}  ({R['turismo_pct_base']}% de la base)")
print(f"municipios turismo  {R['turismo_municipios']:6}")
print(f"fechas corregidas   {R['fechas_corregidas']:6}")
