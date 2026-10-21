"""Línea base de agroturismo para la convocatoria de subvenciones ICETEX
(proyecto UCEVA y aliados · innovación en destinos turísticos y agrícolas en
las zonas afectadas por el sismo del 10 de agosto de 2026).

QUÉ CONSTRUYE
1. Oferta agroturística formal por municipio, leída del RNT vigente 2026.
2. Afectación de la cadena de valor del turismo, del censo empresarial.
3. Afectación del sector agropecuario, del mismo censo.
4. Un índice de priorización reproducible que combina las tres cosas.

POR QUÉ «AGROTURÍSTICA» SE PUEDE MEDIR
El RNT no tiene una categoría llamada agroturismo, pero sí subcategorías que
describen alojamiento y atractivos en suelo rural: fincas turísticas, glamping,
campamentos, parques de ecoturismo y centros vacacionales. Ese conjunto es el
proxy que se usa aquí, y se declara siempre como proxy.

QUÉ NO SE PUEDE DECIR
El censo no identifica qué establecimiento turístico es agroturístico, así que
NO se puede contar «fincas agroturísticas afectadas». Lo que sí se puede es
cruzar, por municipio, dónde está la oferta rural formal y dónde se concentró
el daño. Esa es la lectura que soporta la línea base.

DATOS PERSONALES
Este archivo se construye solo con agregados municipales. No contiene nombre,
documento, teléfono, correo, NIT, dirección ni razón social de ningún
reportante. Los identificadores se leen únicamente para depurar doble
notificación y no salen del script.
"""
import json
import re
import unicodedata
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# Depuración de doble notificación y universo de turismo ya validados.
_h = open("cruce_rnt_0903.py").read().split("# ── 3 · marca")[0]
_g = {}
exec(_h, _g)
T, R, V, N0, DUPS = _g["T"], _g["R"], _g["V"], _g["N0"], _g["DUPS"]
nmun = _g["nmun"]

CORTE = "3 de septiembre de 2026"
SISMO = "10 de agosto de 2026"

# ── 1 · oferta agroturística formal (RNT) ────────────────────────────────
# Subcategorías del RNT que describen alojamiento o atractivo en suelo rural.
# Es un proxy de agroturismo, no una categoría oficial del registro.
SUB_RURAL = [
    "FINCAS TURÍSTICAS (ALOJAMIENTO RURAL)",
    "GLAMPING",
    "CAMPAMENTO",
    "PARQUE DE ECOTURISMO",
    "CENTRO VACACIONAL",
    "ALBERGUE",
]
V["rural"] = V.SUB_CATEGORIA.isin(SUB_RURAL)
RUR = V[V.rural]

# ── 2 · sector agropecuario afectado (censo) ─────────────────────────────
SEC_AGRO = "Agricultura, ganadería, caza, silvicultura y pesca"
AG = R[R["Actividad económica/sector"] == SEC_AGRO].copy()

# ── 3 · métricas comunes ─────────────────────────────────────────────────
SEV = ["Crítica", "Grave"]
PLO = {"Menos de $5 millones.": 0, "Entre $5 y $20 millones.": 5,
       "Más de $20 y hasta $100 millones.": 20, "Más de $100 millones.": 0}
ELO = {"Ninguno": 0, "Entre 1 y 5": 1, "Entre 6 y 20": 6,
       "Entre 21 y 50": 21, "Más de 50": 51}
EHI = {"Ninguno": 0, "Entre 1 y 5": 5, "Entre 6 y 20": 20,
       "Entre 21 y 50": 50, "Más de 50": 51}


def pct(a, b):
    return round(100 * a / b, 1) if b else None


def resumen(d):
    """Las cifras que pide la línea base: cuántos, qué tan golpeados, cuánto
    empleo y cuánta pérdida. El empleo va como intervalo porque la encuesta
    pregunta por rangos; el tramo abierto entra en ambas cotas por su piso."""
    niv = d["Nivel de afectación"]
    cont = d["Continuidad operativa"].dropna()
    p = d["Pérdidas económicas"].dropna()
    e = d["Empleos afectados o en riesgo"].dropna()
    ab = int((p == "Más de $100 millones.").sum())
    elo = int(sum(ELO[x] for x in e))
    ehi = int(sum(EHI[x] for x in e))
    assert elo <= ehi, "la cota alta de empleo no puede quedar bajo la baja"
    return {
        "n": int(len(d)),
        "sev": int(niv.isin(SEV).sum()), "pct_sev": pct(int(niv.isin(SEV).sum()), len(d)),
        "critica": int((niv == "Crítica").sum()),
        "base_cont": int(len(cont)),
        "no_opera": int((cont == "No puede operar").sum()),
        "pct_no_opera": pct(int((cont == "No puede operar").sum()), len(cont)),
        "parcial": int((cont == "Sí, pero parcialmente").sum()),
        "pct_restriccion": pct(int((cont != "Sí, normalmente").sum()), len(cont)),
        "base_empl": int(len(e)),
        "con_empleo": int((e != "Ninguno").sum()),
        "pct_empleo": pct(int((e != "Ninguno").sum()), len(e)),
        "empl_lo": elo, "empl_hi": ehi,
        "base_perd": int(len(p)),
        "perd_min": int(sum(PLO[x] for x in p) + 100 * ab),
        "perd_ab": ab,
    }


# ── 4 · tabla municipal ──────────────────────────────────────────────────
rnt_tot = V.groupby("zmun").size()
rnt_rur = RUR.groupby("zmun").size()
rnt_emp = V.groupby("zmun").NUM_EMP.sum()
hab = RUR.groupby("zmun").HABITACIONES.sum()
cam = RUR.groupby("zmun").CAMAS.sum()

filas = []
for m in sorted(set(T.zmun) | set(rnt_tot.index) | set(AG.zmun)):
    t = T[T.zmun == m]
    a = AG[AG.zmun == m]
    f = {"municipio": m}
    rt = resumen(t) if len(t) else {k: 0 for k in resumen(T)}
    ra = resumen(a) if len(a) else {k: 0 for k in resumen(T)}
    f["tur_n"] = rt["n"]
    f["tur_sev"] = rt["sev"]
    f["tur_pct_sev"] = rt["pct_sev"]
    f["tur_no_opera"] = rt["no_opera"]
    f["tur_pct_no_opera"] = rt["pct_no_opera"]
    f["tur_con_empleo"] = rt["con_empleo"]
    f["tur_empl_lo"] = rt["empl_lo"]
    f["tur_empl_hi"] = rt["empl_hi"]
    f["tur_perd_min"] = rt["perd_min"]
    f["agro_n"] = ra["n"]
    f["agro_sev"] = ra["sev"]
    f["agro_empl_lo"] = ra["empl_lo"]
    f["agro_perd_min"] = ra["perd_min"]
    f["rnt_vigentes"] = int(rnt_tot.get(m, 0))
    f["rnt_rural"] = int(rnt_rur.get(m, 0))
    f["pct_rural"] = pct(f["rnt_rural"], f["rnt_vigentes"])
    f["hab_rural"] = int(hab.get(m, 0))
    f["camas_rural"] = int(cam.get(m, 0))
    f["empleos_rnt"] = int(rnt_emp.get(m, 0))
    f["censo_mun"] = int((R.zmun == m).sum())
    filas.append(f)
MU = pd.DataFrame(filas)

# ── 5 · índice de priorización ───────────────────────────────────────────
# Tres componentes, pesos iguales y explícitos. Cada uno se lleva a 0-100
# dividiendo por el máximo del departamento, para que ningún componente mande
# solo por su escala. Se declara el peso porque el ranking es discutible y
# quien lo lea debe poder rehacerlo con otros pesos.
#
#   VOCACIÓN   oferta rural formal inscrita en el RNT      (potencial)
#   DAÑO       negocios turísticos que reportaron daño     (necesidad)
#   SEVERIDAD  % de esos negocios en crítico o grave       (urgencia)
#
# La severidad solo entra cuando hay al menos 10 reportes: sobre tres casos el
# porcentaje describe un puñado de negocios, no al municipio.
PESOS = {"vocacion": 1 / 3, "dano": 1 / 3, "severidad": 1 / 3}
MIN_REPORTES_SEV = 10

esc = lambda s: 100 * s / s.max() if s.max() else s * 0
MU["i_vocacion"] = esc(MU.rnt_rural.astype(float))
MU["i_dano"] = esc(MU.tur_n.astype(float))
sev = MU.tur_pct_sev.where(MU.tur_n >= MIN_REPORTES_SEV, 0).fillna(0)
MU["i_severidad"] = esc(sev)
MU["indice"] = (PESOS["vocacion"] * MU.i_vocacion
                + PESOS["dano"] * MU.i_dano
                + PESOS["severidad"] * MU.i_severidad).round(1)
for c in ("i_vocacion", "i_dano", "i_severidad"):
    MU[c] = MU[c].round(1)
MU = MU.sort_values("indice", ascending=False).reset_index(drop=True)
MU["rank"] = MU.index + 1

# Los seis que la Gobernación ya priorizó para la reactivación turística.
PRIORIZADOS = ["ROLDANILLO", "BUENAVENTURA", "SEVILLA", "CARTAGO", "LA UNION",
               "ZARZAL"]

TOT_RUR = int(len(RUR))
res = {
    "corte": CORTE, "sismo": SISMO,
    "censo": {"recibidos": int(N0), "dobles": int(DUPS), "unicos": int(len(R))},
    "turismo": resumen(T),
    "agro": resumen(AG),
    "rnt": {
        "vigentes": int(len(V)), "municipios": int(V.zmun.nunique()),
        "rural": TOT_RUR, "pct_rural": pct(TOT_RUR, len(V)),
        "municipios_rural": int(RUR.zmun.nunique()),
        "habitaciones": int(RUR.HABITACIONES.sum()),
        "camas": int(RUR.CAMAS.sum()),
        "empleos": int(RUR.NUM_EMP.sum()),
        "sub": {k: int(v) for k, v in RUR.SUB_CATEGORIA.value_counts().items()},
        "definicion_rural": SUB_RURAL,
    },
    "pesos": PESOS, "min_reportes_sev": MIN_REPORTES_SEV,
    "priorizados_gobernacion": PRIORIZADOS,
    "municipios": MU.to_dict("records"),
}


def limpio(o):
    if isinstance(o, dict):
        return {k: limpio(v) for k, v in o.items()}
    if isinstance(o, list):
        return [limpio(v) for v in o]
    if isinstance(o, float) and np.isnan(o):
        return None
    return o


json.dump(limpio(res), open("agroturismo.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1, default=str)
MU.to_csv("agroturismo_municipal.csv", index=False)

mil = lambda x: f"{x:,}".replace(",", ".")
c1 = lambda x: str(x).replace(".", ",")
TU, AGR = res["turismo"], res["agro"]
print("=" * 86)
print(f"LÍNEA BASE AGROTURISMO · corte {CORTE}")
print("=" * 86)
print(f"  oferta turística formal (RNT vigente)   {mil(res['rnt']['vigentes']):>8}")
print(f"  de ella, alojamiento/atractivo rural    {mil(TOT_RUR):>8}  "
      f"({c1(res['rnt']['pct_rural'])} %) en {res['rnt']['municipios_rural']} municipios")
print(f"    habitaciones {mil(res['rnt']['habitaciones'])} · camas "
      f"{mil(res['rnt']['camas'])} · empleos declarados {mil(res['rnt']['empleos'])}")
print()
print(f"  cadena de valor del turismo afectada    {mil(TU['n']):>8}  "
      f"{c1(TU['pct_sev'])} % crítico o grave · {c1(TU['pct_no_opera'])} % sin operar")
print(f"    empleo comprometido {mil(TU['empl_lo'])}–{mil(TU['empl_hi'])} en "
      f"{mil(TU['con_empleo'])} negocios · pérdidas piso ${mil(TU['perd_min'])} M")
print(f"  sector agropecuario afectado            {mil(AGR['n']):>8}  "
      f"{c1(AGR['pct_sev'])} % crítico o grave")
print(f"    empleo comprometido {mil(AGR['empl_lo'])}–{mil(AGR['empl_hi'])} · "
      f"pérdidas piso ${mil(AGR['perd_min'])} M")
print()
print("ÍNDICE DE PRIORIZACIÓN  (vocación rural + daño + severidad, pesos iguales)")
print(f"{'#':>2} {'municipio':16} {'índice':>7} {'rural':>6} {'turíst.':>8} "
      f"{'%sev':>6} {'empleo':>12} {'$ piso':>8} {'agro':>5}")
for r in res["municipios"][:18]:
    print(f"{r['rank']:>2} {r['municipio'].title():16} {c1(r['indice']):>7} "
          f"{r['rnt_rural']:>6} {r['tur_n']:>8} {c1(r['tur_pct_sev'] or 0):>6} "
          f"{str(r['tur_empl_lo']) + '–' + str(r['tur_empl_hi']):>12} "
          f"{mil(r['tur_perd_min']):>8} {r['agro_n']:>5}")
print()
d = {r["municipio"]: r for r in res["municipios"]}
print("Los seis ya priorizados por la Gobernación, en este índice:")
for m in PRIORIZADOS:
    r = d[m]
    print(f"   {m.title():16} puesto {r['rank']:>2} · índice {c1(r['indice'])} · "
          f"{r['rnt_rural']} prestadores rurales · {r['tur_n']} negocios afectados")
print("\nescrito: agroturismo.json · agroturismo_municipal.csv")
