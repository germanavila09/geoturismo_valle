"""Geoestadistica descriptiva por municipio, sobre la base sin duplicados.

Se retiro el analisis de autocorrelacion espacial (I de Moran). En su lugar,
descripcion por indicador: distribucion, ranking y relacion entre variables.

Todo se calcula sobre `dedup.pkl`, que solo contiene columnas no sensibles.
"""
import json
import re
import unicodedata

import numpy as np
import pandas as pd

est = pd.read_pickle("dedup.pkl")
N = len(est)

SEV = {"Crítica": 1.0, "Grave": 0.75, "Moderada": 0.40, "Baja": 0.15, "no_afectado": 0.0}
CONT = {"No puede operar": 1.0, "Sí, pero parcialmente": 0.5, "Sí, normalmente": 0.0}
PERD = {"Más de $100 millones.": 1.0, "Más de $20 y hasta $100 millones.": 0.66,
        "Entre $5 y $20 millones.": 0.33, "Menos de $5 millones.": 0.10}
EMPL = {"Más de 50": 1.0, "Entre 21 y 50": 0.75, "Entre 6 y 20": 0.5,
        "Entre 1 y 5": 0.25, "Ninguno": 0.0}
ALTA = ["Más de $20 y hasta $100 millones.", "Más de $100 millones."]

est["_sev"] = est["Nivel de afectación"].map(SEV)
est["_cont"] = est["Continuidad operativa"].map(CONT)
est["_perd"] = est["Pérdidas económicas"].map(PERD)
est["_empl"] = est["Empleos afectados o en riesgo"].map(EMPL)

filas = []
for mun, g in est.groupby("Municipio"):
    cont = g["Continuidad operativa"].dropna()
    perd = g["Pérdidas económicas"].dropna()
    empl = g["Empleos afectados o en riesgo"].dropna()
    f = {"municipio": mun, "n": len(g),
         "pct_severo": round(100 * g["Nivel de afectación"].isin(["Crítica", "Grave"]).mean(), 1),
         "pct_critico": round(100 * (g["Nivel de afectación"] == "Crítica").mean(), 1),
         "pct_no_opera": round(100 * (cont == "No puede operar").mean(), 1) if len(cont) else np.nan,
         "pct_no_normal": round(100 * (cont != "Sí, normalmente").mean(), 1) if len(cont) else np.nan,
         "pct_perd_alta": round(100 * perd.isin(ALTA).mean(), 1) if len(perd) else np.nan,
         "pct_empleo": round(100 * (empl != "Ninguno").mean(), 1) if len(empl) else np.nan,
         "sin_clasif": round(100 * (g["Nivel de afectación"] == "Sin clasificación").mean(), 1),
         "base_cont": len(cont), "base_perd": len(perd), "base_empl": len(empl)}
    for c, et in [("_sev", "i_sev"), ("_cont", "i_cont"), ("_perd", "i_perd"), ("_empl", "i_empl")]:
        s = g[c].dropna()
        f[et] = round(float(s.mean()), 4) if len(s) else np.nan
    filas.append(f)
M = pd.DataFrame(filas)

# ── indice compuesto, con contraccion hacia la media departamental ────────
PESOS = {"i_sev": 0.30, "i_cont": 0.30, "i_perd": 0.25, "i_empl": 0.15}
bruto = sum(M[k].fillna(M[k].mean()) * w for k, w in PESOS.items())
comp = sum(est[c].fillna(est[c].mean()) * w for c, w in
           [("_sev", .30), ("_cont", .30), ("_perd", .25), ("_empl", .15)])
est["_b"] = comp
sigma2 = float(est.groupby("Municipio")._b.var().mean())
tau2 = float(est.groupby("Municipio")._b.mean().var())
mu = float(est._b.mean())
M["_bruto"] = M.municipio.map(est.groupby("Municipio")._b.mean())
M["w"] = (tau2 / (tau2 + sigma2 / M.n)).round(3)
aj = M.w * M._bruto + (1 - M.w) * mu
M["IAE"] = (100 * (bruto - bruto.min()) / (bruto.max() - bruto.min())).round(1)
M["IAE_aj"] = (100 * (aj - aj.min()) / (aj.max() - aj.min())).round(1)
M = M.drop(columns=["_bruto"]).sort_values("IAE_aj", ascending=False).reset_index(drop=True)

IND = [("pct_severo", "Afectación crítica o grave"),
       ("pct_no_opera", "No puede operar"),
       ("pct_perd_alta", "Pérdidas superiores a $20 millones"),
       ("pct_empleo", "Con algún empleo en riesgo")]

res = {"n": N, "nmun": len(M), "pesos": PESOS,
       "shrink": {"tau2": round(tau2, 5), "sigma2": round(sigma2, 5), "mu": round(mu, 4),
                  "w_min": float(M.w.min()), "w_max": float(M.w.max())},
       "municipios": M.to_dict("records"),
       "descriptivos": {}, "correlaciones": {}}

# ── descriptivos de cada indicador entre los 42 municipios ───────────────
for c, et in IND + [("IAE_aj", "Índice compuesto ajustado")]:
    s = M[c].dropna()
    res["descriptivos"][et] = {
        "min": round(float(s.min()), 1), "q1": round(float(s.quantile(.25)), 1),
        "mediana": round(float(s.median()), 1), "q3": round(float(s.quantile(.75)), 1),
        "max": round(float(s.max()), 1), "media": round(float(s.mean()), 1),
        "desv": round(float(s.std()), 1),
        "cv": round(float(s.std() / s.mean()), 3),
        "rango": round(float(s.max() - s.min()), 1),
        "min_mun": M.loc[s.idxmin(), "municipio"], "max_mun": M.loc[s.idxmax(), "municipio"],
        "top5": M.nlargest(5, c)[["municipio", c, "n"]].values.tolist()}

# ── correlaciones entre indicadores (Spearman: son ordinales) ────────────
cols = [c for c, _ in IND] + ["n"]
cor = M[cols].corr(method="spearman").round(3)
res["correlaciones"] = {a: {b: float(cor.loc[a, b]) for b in cols} for a in cols}

M.to_csv("indice_municipal.csv", index=False)
json.dump(res, open("descriptivo.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1, default=str)

mil = lambda x: f"{x:,}".replace(",", ".")
print(f"establecimientos únicos: {mil(N)} · municipios: {len(M)}")
print(f"contracción: w entre {M.w.min():.3f} y {M.w.max():.3f}")
print("\nDESCRIPTIVOS ENTRE LOS 42 MUNICIPIOS")
print(f"  {'indicador':36} {'mín':>6} {'Q1':>6} {'med':>6} {'Q3':>6} {'máx':>6} {'CV':>6}")
for et, d in res["descriptivos"].items():
    print(f"  {et:36} {d['min']:6} {d['q1']:6} {d['mediana']:6} {d['q3']:6} "
          f"{d['max']:6} {d['cv']:6}")
print("\nCORRELACIÓN DE SPEARMAN ENTRE INDICADORES")
print(cor.to_string())
print(f"\nTOP 10 POR ÍNDICE AJUSTADO")
for r in M.head(10).itertuples():
    print(f"  {r.municipio[:22]:24} {r.IAE_aj:6} · n={r.n:5} · sev={r.pct_severo:5} % · "
          f"noop={r.pct_no_opera:5} %")
