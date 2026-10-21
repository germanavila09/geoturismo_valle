"""Insumos del informe, recalculados sobre la base sin doble notificacion.

Cambios respecto de datos2.json:
  · universo = 13.652 establecimientos unicos (antes 14.241 con duplicados)
  · se retira todo lo relativo a la I de Moran
  · se anaden los descriptivos por indicador y el analisis de duplicidad

Las cifras de fuentes externas (DANE, WWB, Confecamaras, Camara de Comercio)
se conservan tal cual: son de terceros y no dependen de esta depuracion.
"""
import json

import numpy as np
import pandas as pd

est = pd.read_pickle("dedup.pkl")
M = pd.read_csv("indice_municipal.csv")
DUP = json.load(open("duplicados.json", encoding="utf-8"))
R = json.load(open("descriptivo.json", encoding="utf-8"))
N = len(est)

V = ["Nivel de afectación", "Principal necesidad", "Pérdidas económicas",
     "Continuidad operativa", "Empleos afectados o en riesgo", "Apoyo financiero"]
bases = {v: int(est[v].notna().sum()) for v in V}


def conteo(col):
    s = est[col].dropna()
    return {"base": int(len(s)), "c": {k: int(v) for k, v in s.value_counts().items()}}


sev, cont, perd, empl = (conteo(c) for c in
                         ["Nivel de afectación", "Continuidad operativa",
                          "Pérdidas económicas", "Empleos afectados o en riesgo"])


# Los dos campos de seleccion multiple admiten texto libre en «Otro», y el
# archivo trae la codificacion rota (mojibake) en parte de esas respuestas.
# Se reduce cada mencion a su categoria por palabras clave; lo que no encaja
# queda en «Otro», sin inventar categorias.
CAT_NEC = [("Capital de trabajo o insumos", ["capital de trabajo", "inventario", "insumo",
                                             "capital semilla"]),
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
    import unicodedata
    s = unicodedata.normalize("NFD", str(s).lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def multiple(col, cats):
    c = {k: 0 for k, _ in cats}
    c["Otro"] = 0
    for x in est[col].dropna():
        vistos = set()
        for p in str(x).split(";"):
            t = desnuda(p)
            if not t.strip():
                continue
            for k, claves in cats:
                if any(cl in t for cl in claves) and k not in vistos:
                    c[k] += 1
                    vistos.add(k)
                    break
            else:
                if "Otro" not in vistos:
                    c["Otro"] += 1
                    vistos.add("Otro")
    return dict(sorted(c.items(), key=lambda kv: -kv[1]))


nec = multiple("Principal necesidad", CAT_NEC)
apo = multiple("Apoyo financiero", CAT_APO)

# ── cotas de perdidas y empleo (los rangos solo permiten intervalos) ─────
# El rango abierto no entra en `lo`; se suma aparte para dejar explicito que
# la cota inferior depende de un supuesto sobre el tramo sin techo.
PLO = {"Menos de $5 millones.": 0, "Entre $5 y $20 millones.": 5,
       "Más de $20 y hasta $100 millones.": 20, "Más de $100 millones.": 0}
PHI = {"Menos de $5 millones.": 5, "Entre $5 y $20 millones.": 20,
       "Más de $20 y hasta $100 millones.": 100}
ELO = {"Ninguno": 0, "Entre 1 y 5": 1, "Entre 6 y 20": 6,
       "Entre 21 y 50": 21, "Más de 50": 51}
EHI = {"Ninguno": 0, "Entre 1 y 5": 5, "Entre 6 y 20": 20, "Entre 21 y 50": 50}

p = est["Pérdidas económicas"].dropna()
e = est["Empleos afectados o en riesgo"].dropna()
econ = {"lo": int(sum(PLO[x] for x in p)),
        "hi": int(sum(PHI.get(x, 0) for x in p)),
        "ab": int((p == "Más de $100 millones.").sum()),
        "base": int(len(p))}
econ["min"] = econ["lo"] + 100 * econ["ab"]
empleo = {"lo": int(sum(ELO[x] for x in e)), "hi": int(sum(EHI.get(x, 0) for x in e)),
          "ab": int((e == "Más de 50").sum()),
          "pct": round(100 * (e != "Ninguno").mean(), 1), "base": int(len(e))}

cc = est[est.Municipio.str.upper().str.contains("CALI", na=False) &
         ~est.Municipio.str.upper().str.contains("CALIMA", na=False)]
cali = {"n": int(len(cc)),
        "sev": round(100 * cc["Nivel de afectación"].isin(["Crítica", "Grave"]).mean(), 1),
        "noop": round(100 * (cc["Continuidad operativa"].dropna() == "No puede operar").mean(), 1)}

noop_norm = round(100 * (cont["base"] - cont["c"]["Sí, normalmente"]) / cont["base"], 1)

MUN = M.copy()
MUN["peso_w"] = MUN.w
D = {
    "n": N, "nmun": int(len(M)), "bases": bases,
    "sev": sev, "cont": cont, "perd": perd, "empl": empl,
    "nec": nec, "apo": apo,
    "econ": econ, "empleo": empleo, "cali": cali, "noop_norm": noop_norm,
    "shrink": R["shrink"], "pesos": R["pesos"],
    "descriptivos": R["descriptivos"], "correlaciones": R["correlaciones"],
    "dup": DUP,
    "mun": MUN.to_dict("records"),
    "top10": M.head(10).municipio.tolist(),
    # Cifras de terceros: no dependen de esta base.
    "dane": {"unidades": 193974, "cali": 99208, "ulloa": 199, "micro": 69, "dens": 41,
             "pobreza": 21.8, "pobreza_nac": 28.0, "pobreza_ext": 7.7, "pobreza_cali": 19.7},
    "wwb": {"n": 4000, "mun": 147, "noop": 76.2, "inutil": 11, "detuvo": 47.1,
            "vivienda": 71.6, "hogares": 60.4, "no_alcanza": 27.7, "con_dificultad": 32.7,
            "alimento": 11.7, "comedor": 8.3, "emocional": 81.4, "capital": 34.9,
            "psico": 22.5, "viv": 21.7, "ventas": 48.7},
    "conf": {"empresas": 30000, "cali_sev": 63, "cali_noop": 39},
    "macro": {"empresas": 270000, "empleos": 1400000, "micro": 93,
              "pib_min": 0.2, "pib_max": 0.4, "usd_min": 990, "usd_max": 1980},
}
D["dane"]["cobertura"] = round(100 * N / D["dane"]["unidades"], 1)
D["dane"]["cob_cali"] = round(100 * cali["n"] / D["dane"]["cali"], 1)

json.dump(D, open("datos3.json", "w", encoding="utf-8"), ensure_ascii=False,
          indent=1, default=str)

mil = lambda x: f"{x:,}".replace(",", ".")
print(f"universo depurado      {mil(N)}")
print(f"bases                  {bases}")
print(f"crítico o grave        {sev['c'].get('Crítica',0)+sev['c'].get('Grave',0)} "
      f"({100*(sev['c'].get('Crítica',0)+sev['c'].get('Grave',0))/sev['base']:.1f} %)")
print(f"no opera con normal.   {noop_norm} %")
print(f"pérdidas (piso)        {mil(econ['min'])} millones · abiertos {econ['ab']}")
print(f"empleo                 {mil(empleo['lo'])}–{mil(empleo['hi'])} · {empleo['pct']} %")
print(f"Cali                   n={mil(cali['n'])} sev={cali['sev']} noop={cali['noop']}")
print(f"cobertura DANE         {D['dane']['cobertura']} % · Cali {D['dane']['cob_cali']} %")
print("necesidades            ", nec)
print("apoyo                  ", apo)
