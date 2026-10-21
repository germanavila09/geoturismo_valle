#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mapa coropletico + graficos de barras para el informe PAER (PCC + Buenaventura).

Reusa el patron ya validado en observatorios/geoturismo/analisis/impacto_sismo/
cadena_valor_rnt/mapas_turismo.py (geometria DANE, rotulo nombre+valor, leyenda
por clases) pero resalta los 11 municipios del alcance sobre el contexto de
los 42 del departamento, en vez de mostrar los 42 con el mismo peso visual.
"""
import json
import unicodedata
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Polygon as MplPoly

HERE = Path(__file__).resolve().parent
LAB_ROOT = next(p for p in HERE.parents if (p / "georiesgo").is_dir() and (p / "geoturismo").is_dir())
GEORIESGO = str(LAB_ROOT / "georiesgo")
RNT_DIR = str(LAB_ROOT / "geoturismo" / "analisis" / "impacto_sismo" / "cadena_valor_rnt")
OUT = str(HERE / "figuras")

AZULT = "#1F3864"
CREMA = "#FFFDF7"
plt.rcParams.update({"font.family": "DejaVu Sans", "figure.dpi": 210,
                      "figure.facecolor": CREMA, "savefig.facecolor": CREMA})

geo = json.load(open(f"{GEORIESGO}/fuentes/municipios_valle.geojson", encoding="utf-8"))
R = json.load(open(f"{RNT_DIR}/turismo_mun_0903.json", encoding="utf-8"))
MU = pd.DataFrame(R["municipios"])


def norm(s):
    s = unicodedata.normalize("NFD", str(s or "").upper())
    return "".join(c for c in s if unicodedata.category(c) != "Mn").strip()


ALIAS = {"SANTIAGO DE CALI": "CALI", "CALIMA (EL DARIEN)": "CALIMA",
         "GUADALAJARA DE BUGA": "BUGA"}
clave = lambda s: ALIAS.get(norm(s), norm(s))
MU["k"] = MU.municipio.map(clave)
DAT = MU.set_index("k")

PCC_BUGA = ["EL CAIRO", "ANSERMANUEVO", "ARGELIA", "EL AGUILA", "ALCALA",
            "ULLOA", "SEVILLA", "CAICEDONIA", "TRUJILLO", "RIOFRIO",
            "BUENAVENTURA"]

NOMBRE = {"ALCALA": "Alcalá", "EL AGUILA": "El Águila", "RIOFRIO": "Riofrío",
          "EL CAIRO": "El Cairo"}


def bonito(k):
    return NOMBRE.get(k, k.title())


NUDGE = {"ULLOA": (0.055, 0.030), "ALCALA": (0.012, -0.030),
         "CAICEDONIA": (-0.026, 0.016), "ANSERMANUEVO": (0.006, 0.012),
         "ARGELIA": (0.014, -0.012), "EL CAIRO": (-0.012, 0.010),
         "SEVILLA": (0.012, -0.018)}

anillos = lambda g: ([g["coordinates"][0]] if g["type"] == "Polygon"
                      else [p[0] for p in g["coordinates"]])


def centro(f):
    a = max(anillos(f["geometry"]), key=len)
    p = np.array(a)
    k = clave(f["properties"]["nombre"])
    dx, dy = NUDGE.get(k, (0.0, 0.0))
    return p[:, 0].mean() + dx, p[:, 1].mean() + dy


mil = lambda x: f"{x:,}".replace(",", ".")

# ── Figura 1: mapa coropletico, 11 municipios resaltados sobre el Valle ────
COLORES = ["#fff3d6", "#fbdc9a", "#f4a35c", "#dd6031", "#9a1f16"]
CORTES = [45, 55, 65, 75]  # % critico o grave


def clase(x):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return None
    for i, c in enumerate(CORTES):
        if x <= c:
            return i
    return len(CORTES)


fig, ax = plt.subplots(figsize=(9.6, 7.2))
for f in geo["features"]:
    k = clave(f["properties"]["nombre"])
    en_alcance = k in PCC_BUGA
    val = float(DAT["pct_sev"].get(k, np.nan)) if k in DAT.index else np.nan
    i = clase(val) if en_alcance else None
    fill = COLORES[i] if i is not None else ("#e9e6df" if not en_alcance else "#e0e0e0")
    edge = AZULT if en_alcance else "#ffffff"
    lw = 2.1 if en_alcance else 0.6
    for a in anillos(f["geometry"]):
        ax.add_patch(MplPoly(np.array(a), closed=True, facecolor=fill,
                              edgecolor=edge, linewidth=lw,
                              zorder=3 if en_alcance else 1))

for f in geo["features"]:
    k = clave(f["properties"]["nombre"])
    if k not in PCC_BUGA:
        continue
    cx, cy = centro(f)
    val = float(DAT["pct_sev"].get(k, np.nan)) if k in DAT.index else np.nan
    i = clase(val)
    oscuro = i is not None and i >= len(COLORES) - 2
    txt = f"{bonito(k)}\n{val:.0f} %"
    ax.annotate(txt, (cx, cy), fontsize=8.6, ha="center", va="center",
                color="white" if oscuro else "#15110a", fontweight="bold",
                linespacing=1.2, zorder=6,
                path_effects=[pe.withStroke(linewidth=2.2,
                              foreground="#3a0d0a" if oscuro else "white")])

ax.autoscale_view()
ax.set_aspect("equal")
ax.axis("off")
ax.set_title("Afectación turística declarada — % de negocios en estado crítico o grave",
             fontsize=13.5, fontweight="bold", loc="left", color=AZULT, pad=16)
ax.text(0, 1.01, "Municipios del Paisaje Cultural Cafetero y Buenaventura, resaltados sobre el Valle del Cauca",
        transform=ax.transAxes, fontsize=10, color="#5a5a5a", va="bottom")

ets = ["hasta " + str(CORTES[0]) + " %"]
for j in range(1, len(CORTES)):
    ets.append(f"{CORTES[j-1]}–{CORTES[j]} %")
ets.append("más de " + str(CORTES[-1]) + " %")
marcas = [Line2D([0], [0], marker="s", color="none", markerfacecolor=COLORES[j],
                 markeredgecolor=AZULT, markersize=13, label=ets[j])
          for j in range(len(COLORES))]
marcas.append(Line2D([0], [0], marker="s", color="none", markerfacecolor="#e9e6df",
                      markeredgecolor="white", markersize=13, label="Fuera del alcance de este informe"))
leg = ax.legend(handles=marcas, title="% crítico o grave", loc="upper left",
                bbox_to_anchor=(-0.02, 0.97), fontsize=9.6, title_fontsize=10.4,
                frameon=True, facecolor="white", edgecolor="#d8d0b8", borderpad=.7, labelspacing=.5)
leg.get_title().set_color(AZULT)
leg.get_title().set_fontweight("bold")
leg.get_frame().set_alpha(.95)

ax.text(0, -0.01, "Cada municipio del alcance muestra su nombre y su valor. Geometría: Marco Geoestadístico "
                  "Nacional (DANE). Fuente: cruce turismo–RNT, corte 2026-09-03.",
        transform=ax.transAxes, fontsize=7.6, color="#6a6a6a", va="top")
plt.tight_layout()
plt.savefig(f"{OUT}/fig1_mapa_pcc.png", bbox_inches="tight", facecolor=CREMA)
plt.close()
print("fig1_mapa_pcc.png OK")

# ── Figura 2: ranking de severidad, barras horizontales ────────────────────
rows = []
for k in PCC_BUGA:
    d = DAT.loc[k]
    rows.append((bonito(k), d["pct_sev"], d["n"], d["rnt_vigentes"]))
rows.sort(key=lambda r: r[1])

fig, ax = plt.subplots(figsize=(8.6, 5.6))
names = [r[0] for r in rows]
vals = [r[1] for r in rows]


def color_for(v):
    if v <= 45:
        return "#2f7d47"
    if v <= 55:
        return "#e0902c"
    if v <= 65:
        return "#dd6031"
    if v <= 75:
        return "#b3261e"
    return "#7a1410"


bars = ax.barh(names, vals, color=[color_for(v) for v in vals], zorder=3)
for b, r in zip(bars, rows):
    ax.text(b.get_width() + 1.3, b.get_y() + b.get_height() / 2,
            f"{r[1]:.0f} %  (n={r[2]}, RNT={r[3]})",
            va="center", fontsize=9, color="#15110a")
ax.set_xlim(0, 100)
ax.set_xlabel("% de negocios turísticos en estado crítico o grave")
ax.set_title("Severidad declarada por municipio — PCC y Buenaventura",
              fontsize=13, fontweight="bold", loc="left", color=AZULT, pad=28)
ax.text(0, 1.065, "n = negocios turísticos con daño reportado · RNT = prestadores con registro vigente",
        transform=ax.transAxes, fontsize=9.2, color="#5a5a5a")
ax.spines[["top", "right"]].set_visible(False)
ax.grid(axis="x", color="#e4e4e4", zorder=0)
plt.tight_layout(rect=[0, 0, 1, 0.90])
plt.savefig(f"{OUT}/fig2_severidad.png", bbox_inches="tight", facecolor=CREMA)
plt.close()
print("fig2_severidad.png OK")

# ── Figura 3: empleos comprometidos, rango bajo-alto ───────────────────────
rows2 = []
for k in PCC_BUGA:
    d = DAT.loc[k]
    rows2.append((bonito(k), float(d["empl_lo"]), float(d["empl_hi"])))
rows2.sort(key=lambda r: r[2])

fig, ax = plt.subplots(figsize=(8.6, 5.6))
names2 = [r[0] for r in rows2]
los = [r[1] for r in rows2]
his = [r[2] for r in rows2]
y = np.arange(len(names2))
ax.barh(y, [h - l for l, h in zip(los, his)], left=los, color="#2a78d6", zorder=3, height=0.6)
for yi, (lo, hi) in zip(y, zip(los, his)):
    ax.text(hi + 15, yi, f"{int(lo)}–{int(hi)}", va="center", fontsize=9, color="#15110a")
ax.set_yticks(y)
ax.set_yticklabels(names2)
ax.set_xlabel("Empleos comprometidos (rango bajo–alto)")
ax.set_title("Empleos turísticos comprometidos por municipio — PCC y Buenaventura",
              fontsize=13, fontweight="bold", loc="left", color=AZULT, pad=14)
ax.spines[["top", "right"]].set_visible(False)
ax.grid(axis="x", color="#e4e4e4", zorder=0)
plt.tight_layout()
plt.savefig(f"{OUT}/fig3_empleo.png", bbox_inches="tight", facecolor=CREMA)
plt.close()
print("fig3_empleo.png OK")
