"""Turismo: censo de afectación y RNT, comparados SOLO por municipio.

POR QUE SE RETIRO EL CRUCE POR NOMBRE
La version anterior emparejaba razon social entre las dos bases y solo lograba
174 coincidencias sobre 1.789 reportes. Con tan pocos casos, cualquier cifra
por municipio quedaba sobre bases de dos o tres registros: no se puede decir
nada firme y el numero invitaba a leerse mal («solo 174 negocios turisticos
tienen RNT»), cuando en realidad medía la calidad del emparejamiento, no la
formalidad del sector.

QUE SE HACE EN SU LUGAR
Se comparan agregados municipales, que no dependen de emparejar nada:

  · cuantos prestadores con RNT vigente hay en el municipio   (oferta formal)
  · cuantos negocios turisticos reportaron daño alli          (afectacion)
  · la razon entre ambos, por cada 100 inscritos              (intensidad)

QUE ES Y QUE NO ES LA INTENSIDAD
«Reportes por cada 100 prestadores inscritos» NO es el porcentaje del RNT
afectado. Las dos cifras miden universos distintos: el censo recoge cualquier
negocio turistico, con RNT o sin el, y el RNT incluye viviendas turisticas que
casi nunca reportan. El indicador sirve para comparar municipios entre si
—donde el reporte de daño turistico pesa mas frente al tamaño de la oferta
formal— y no para leerse como una tasa de afectacion del registro.

UNIVERSO DE TURISMO
Definicion del censo: «Alojamiento y servicios de comida» + «Transporte y
almacenamiento». Es el criterio con el que se construyo la cifra de 784 ya
socializada, aplicado ahora a la base depurada de doble notificacion.
"""
import json
import re
import unicodedata
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

import sys as _sys; from pathlib import Path as _Path
_sys.path.insert(0, str(next(p for p in _Path(__file__).resolve().parents if (p / "rutas.py").is_file())))
from rutas import fuente, GEORIESGO  # rutas relativas del laboratorio (antes /sessions/.../mnt)
REPORTES = fuente("reportes_emergencia_2026-09-01.xlsx")
RNT = fuente("rnt valle.xlsx")
ANO_VIGENTE = 2026
SEC_TURISMO = ["Alojamiento y servicios de comida", "Transporte y almacenamiento"]


def norm(s):
    s = unicodedata.normalize("NFD", str(s or "").upper())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9 ]", " ", s)).strip()


ALIAS = {"GUADALAJARA DE BUGA": "BUGA", "CALIMA EL DARIEN": "CALIMA",
         "CALIMA DARIEN": "CALIMA", "SANTIAGO DE CALI": "CALI"}
nmun = lambda s: ALIAS.get(norm(s), norm(s))

raw = pd.read_excel(REPORTES, sheet_name="Reportes")
dedup = pd.read_pickle("dedup.pkl")
R = raw[raw["Número de reporte"].isin(dedup["Número de reporte"])].copy()
R["_mun"] = R.Municipio.map(nmun)
TUR = R[R["Actividad económica/sector"].isin(SEC_TURISMO)].copy()

rnt = pd.read_excel(RNT, sheet_name="Data")
V = rnt[rnt.ANO == ANO_VIGENTE].drop_duplicates("CODIGO_RNT").copy()
V["_mun"] = V.MUNICIPIO.map(nmun)

# ── cotas de perdidas y empleo ───────────────────────────────────────────
# El tramo abierto entra en la cota alta por su piso: si se omite, la cota
# alta puede quedar por debajo de la baja.
PLO = {"Menos de $5 millones.": 0, "Entre $5 y $20 millones.": 5,
       "Más de $20 y hasta $100 millones.": 20, "Más de $100 millones.": 0}
PHI = {"Menos de $5 millones.": 5, "Entre $5 y $20 millones.": 20,
       "Más de $20 y hasta $100 millones.": 100, "Más de $100 millones.": 100}
ELO = {"Ninguno": 0, "Entre 1 y 5": 1, "Entre 6 y 20": 6,
       "Entre 21 y 50": 21, "Más de 50": 51}
EHI = {"Ninguno": 0, "Entre 1 y 5": 5, "Entre 6 y 20": 20, "Entre 21 y 50": 50,
       "Más de 50": 51}
SEV = ["Crítica", "Grave"]
ALTA = ["Más de $20 y hasta $100 millones.", "Más de $100 millones."]

CAT_NEC = [("Capital de trabajo o insumos", ["capital de trabajo", "inventario",
                                             "insumo", "capital semilla"]),
           ("Reparar instalaciones o equipos", ["reparar", "maquinaria", "equipo",
                                                "instalacion"]),
           ("Recuperar clientes y ventas", ["cliente", "venta"]),
           ("Facilitar trámites", ["tramite"]),
           ("Restablecer servicios o logística", ["servicio", "logistica"])]
CAT_APO = [("Capital semilla (no reembolsable)", ["capital semilla", "no reembolsable"]),
           ("Alivio de obligaciones", ["alivio", "obligacion"]),
           ("Nuevo crédito", ["credito", "financiacion"]),
           ("No requiere apoyo", ["no requiere", "ninguno"])]


def desnuda(s):
    s = unicodedata.normalize("NFD", str(s).lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def multiple(serie, cats):
    c = {k: 0 for k, _ in cats}
    for x in serie.dropna():
        vistos = set()
        for p in str(x).split(";"):
            t = desnuda(p)
            for k, claves in cats:
                if any(cl in t for cl in claves) and k not in vistos:
                    c[k] += 1
                    vistos.add(k)
                    break
    return c


def resumen(d):
    p = d["Pérdidas económicas"].dropna()
    e = d["Empleos afectados o en riesgo"].dropna()
    cont = d["Continuidad operativa"].dropna()
    nec = d["Principal necesidad"].dropna()
    apo = d["Apoyo financiero"].dropna()
    lo, hi = int(sum(PLO[x] for x in p)), int(sum(PHI.get(x, 0) for x in p))
    ab = int((p == "Más de $100 millones.").sum())
    elo, ehi = int(sum(ELO[x] for x in e)), int(sum(EHI.get(x, 0) for x in e))
    assert elo <= ehi and lo + 100 * ab <= hi + 1e-9 or ab == 0
    niv = d["Nivel de afectación"]
    return {
        "n": int(len(d)),
        "critica": int((niv == "Crítica").sum()), "grave": int((niv == "Grave").sum()),
        "moderada": int((niv == "Moderada").sum()), "baja": int((niv == "Baja").sum()),
        "sin_clasif": int((niv == "Sin clasificación").sum()),
        "sev": int(niv.isin(SEV).sum()),
        "pct_sev": round(100 * niv.isin(SEV).mean(), 1) if len(d) else None,
        "base_cont": int(len(cont)),
        "no_opera": int((cont == "No puede operar").sum()),
        "pct_no_opera": round(100 * (cont == "No puede operar").mean(), 1) if len(cont) else None,
        "pct_no_normal": round(100 * (cont != "Sí, normalmente").mean(), 1) if len(cont) else None,
        "base_perd": int(len(p)), "perd_lo": lo, "perd_hi": hi, "perd_ab": ab,
        "perd_min": lo + 100 * ab,
        "pct_perd_alta": round(100 * p.isin(ALTA).mean(), 1) if len(p) else None,
        "base_empl": int(len(e)), "empl_lo": elo, "empl_hi": ehi,
        "empl_ab": int((e == "Más de 50").sum()),
        "pct_empl": round(100 * (e != "Ninguno").mean(), 1) if len(e) else None,
        # Tramos de establecimientos, no de empleos: se cuentan negocios, que
        # es lo unico que la encuesta permite contar sin acotar intervalos.
        # «Ninguno» queda fuera: no tiene empleo comprometido.
        "empl_ninguno": int((e == "Ninguno").sum()),
        "empl_t1": int((e == "Entre 1 y 5").sum()),
        "empl_t2": int((e == "Entre 6 y 20").sum()),
        "empl_t3": int(e.isin(["Entre 21 y 50", "Más de 50"]).sum()),
        "base_nec": int(len(nec)), "nec": multiple(nec, CAT_NEC),
        "base_apo": int(len(apo)), "apo": multiple(apo, CAT_APO),
    }


res = {
    "corte": "2026-09-01",
    "definicion": SEC_TURISMO,
    "rnt": {"ano": ANO_VIGENTE, "vigentes": int(len(V)),
            "historicos": int(rnt.CODIGO_RNT.nunique()),
            "empleos_rnt": int(V.NUM_EMP.sum()),
            "municipios": int(V._mun.nunique()),
            "categorias": {k: int(v) for k, v in V.CATEGORIA.value_counts().items()}},
    "turismo": resumen(TUR), "todos": resumen(R),
}
res["intensidad_dpto"] = round(100 * res["turismo"]["n"] / res["rnt"]["vigentes"], 1)

# ── tabla municipal ──────────────────────────────────────────────────────
rnt_mun = V.groupby("_mun").agg(rnt_vigentes=("CODIGO_RNT", "size"),
                                empleos_rnt=("NUM_EMP", "sum"))
filas = []
for m in sorted(set(TUR._mun) | set(rnt_mun.index)):
    g = TUR[TUR._mun == m]
    f = {"municipio": m}
    f.update(resumen(g) if len(g) else {k: (0 if k in
             ("n", "critica", "grave", "moderada", "baja", "sin_clasif", "sev",
              "base_cont", "no_opera", "base_perd", "perd_lo", "perd_hi",
              "perd_ab", "perd_min", "base_empl", "empl_lo", "empl_hi",
              "empl_ab", "empl_ninguno", "empl_t1", "empl_t2", "empl_t3",
              "base_nec", "base_apo") else None)
             for k in resumen(TUR)})
    f["rnt_vigentes"] = int(rnt_mun.rnt_vigentes.get(m, 0))
    f["empleos_rnt"] = int(rnt_mun.empleos_rnt.get(m, 0))
    f["reportes_x100_rnt"] = (round(100 * f["n"] / f["rnt_vigentes"], 1)
                              if f["rnt_vigentes"] else None)
    f["n_total_mun"] = int((R._mun == m).sum())
    f["pct_del_censo"] = (round(100 * f["n"] / f["n_total_mun"], 1)
                          if f["n_total_mun"] else None)
    filas.append(f)
MU = pd.DataFrame(filas).sort_values("n", ascending=False).reset_index(drop=True)

COLS = ["municipio", "n", "rnt_vigentes", "empleos_rnt", "reportes_x100_rnt",
        "n_total_mun", "pct_del_censo", "critica", "grave", "moderada", "baja",
        "sin_clasif", "sev", "pct_sev", "no_opera", "pct_no_opera",
        "perd_min", "perd_lo", "perd_hi", "perd_ab", "base_perd",
        "pct_perd_alta", "empl_lo", "empl_hi", "pct_empl", "base_empl",
        "empl_ninguno", "empl_t1", "empl_t2", "empl_t3"]
MU[COLS].to_csv("turismo_municipal.csv", index=False)
res["municipios"] = MU[COLS].to_dict("records")
res["sin_reportes"] = MU[(MU.n == 0) & (MU.rnt_vigentes >= 20)][
    ["municipio", "rnt_vigentes"]].to_dict("records")


def limpio(o):
    if isinstance(o, dict):
        return {k: limpio(v) for k, v in o.items()}
    if isinstance(o, list):
        return [limpio(v) for v in o]
    if isinstance(o, float) and np.isnan(o):
        return None
    return o


json.dump(limpio(res), open("turismo_mun.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1, default=str)

mil = lambda x: f"{x:,}".replace(",", ".")
T, TD = res["turismo"], res["todos"]
print("=" * 76)
print(f"RNT VIGENTE {ANO_VIGENTE}   {mil(res['rnt']['vigentes'])} prestadores · "
      f"{mil(res['rnt']['empleos_rnt'])} empleos · {res['rnt']['municipios']} municipios")
print(f"TURISMO AFECTADO   {mil(T['n'])} establecimientos "
      f"({round(100*T['n']/TD['n'],1)} % del censo de {mil(TD['n'])})")
print("=" * 76)
print(f"  crítico o grave        {mil(T['sev'])}  ({T['pct_sev']} %)   "
      f"vs {TD['pct_sev']} % de toda la economía")
print(f"  no puede operar        {mil(T['no_opera'])}  ({T['pct_no_opera']} %)   "
      f"vs {TD['pct_no_opera']} %")
print(f"  empleos comprometidos  {mil(T['empl_lo'])}–{mil(T['empl_hi'])}  ({T['pct_empl']} %)")
print(f"  pérdidas, piso         ${mil(T['perd_min'])} millones · {T['perd_ab']} sin techo")
print(f"  intensidad dptal       {res['intensidad_dpto']} reportes por cada 100 inscritos")
print(f"\nMUNICIPIOS: {len(MU)}")
print(MU.head(16)[["municipio", "n", "rnt_vigentes", "reportes_x100_rnt",
                   "sev", "pct_sev", "empl_lo", "perd_min"]].to_string(index=False))
print("\nMayor intensidad (20 o más inscritos):")
q = MU[MU.rnt_vigentes >= 20].nlargest(10, "reportes_x100_rnt")
print(q[["municipio", "n", "rnt_vigentes", "reportes_x100_rnt"]].to_string(index=False))
print(f"\nCon RNT y sin un solo reporte turístico: {res['sin_reportes']}")
