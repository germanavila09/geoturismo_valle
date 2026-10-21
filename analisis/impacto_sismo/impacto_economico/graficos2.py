"""Graficos generales sobre la base depurada. Sin el diagrama de Moran."""
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#8a8a8a", "figure.dpi": 205,
                     "ytick.color": "#1a1a1a", "xtick.color": "#4a4a4a"})
ROJO, NAR, AMA, VER, AZU, GRIS = "#b3261e", "#d97706", "#eab308", "#4a9c5d", "#1f6feb", "#9aa0a6"
AZULT = "#1F3864"

est = pd.read_pickle("dedup.pkl")
M = pd.read_csv("indice_municipal.csv")
D = json.load(open("datos3.json", encoding="utf-8"))
N = len(est)
mil = lambda x: f"{x:,}".replace(",", ".")

# ── G1 · las cuatro variables ordinales ──────────────────────────────────
fig, axes = plt.subplots(2, 2, figsize=(7.6, 5.0))


# matplotlib interpreta «$…$» como formula: hay que escapar el peso o los
# rangos de perdidas salen convertidos en cursivas sin sentido.
ET = {"Sí, pero parcialmente": "Sí, parcialmente", "Sí, normalmente": "Sí, normalmente",
      "no_afectado": "No afectado",
      "Más de $100 millones.": r"Más de \$100M",
      "Más de $20 y hasta $100 millones.": r"De \$20M a \$100M",
      "Entre $5 y $20 millones.": r"De \$5M a \$20M",
      "Menos de $5 millones.": r"Menos de \$5M"}


def barras(ax, col, orden, colores, titulo):
    s = est[col].dropna()
    v = [100 * (s == o).mean() for o in orden]
    et = [ET.get(o, o) for o in orden]
    b = ax.barh(range(len(orden))[::-1], v, color=colores, height=.62)
    for r, x, k in zip(b, v, [int((s == o).sum()) for o in orden]):
        ax.text(x + max(v) * .015, r.get_y() + r.get_height() / 2,
                f"{x:.1f} %  ({mil(k)})", va="center", fontsize=7.6, color="#3a3a3a")
    ax.set_yticks(range(len(orden))[::-1])
    ax.set_yticklabels(et, fontsize=7.8)
    ax.set_xlim(0, max(v) * 1.45)
    ax.set_xticks([])
    ax.spines["bottom"].set_visible(False)
    ax.set_title(f"{titulo}\nbase {mil(len(s))}", fontsize=8.6, fontweight="bold",
                 loc="left", color=AZULT)


barras(axes[0, 0], "Nivel de afectación",
       ["Crítica", "Grave", "Moderada", "Baja", "Sin clasificación", "no_afectado"],
       [ROJO, "#e2574c", NAR, VER, GRIS, "#cfcfcf"], "Nivel de afectación")
barras(axes[0, 1], "Continuidad operativa",
       ["No puede operar", "Sí, pero parcialmente", "Sí, normalmente"],
       [ROJO, NAR, VER], "Continuidad operativa")
barras(axes[1, 0], "Pérdidas económicas",
       ["Más de $100 millones.", "Más de $20 y hasta $100 millones.",
        "Entre $5 y $20 millones.", "Menos de $5 millones."],
       [ROJO, NAR, AMA, VER], "Pérdidas económicas")
barras(axes[1, 1], "Empleos afectados o en riesgo",
       ["Más de 50", "Entre 21 y 50", "Entre 6 y 20", "Entre 1 y 5", "Ninguno"],
       [ROJO, "#e2574c", NAR, AMA, VER], "Empleos afectados o en riesgo")
plt.tight_layout()
plt.savefig("g1_variables.png", bbox_inches="tight")
plt.close()

# ── G2 · necesidad y apoyo: departamento frente a los diez mas afectados ──
TOP10 = D["top10"]
sub = est[est.Municipio.isin(TOP10)]
n10 = len(sub)


def cat(serie, cats):
    import unicodedata
    def desnuda(s):
        s = unicodedata.normalize("NFD", str(s).lower())
        return "".join(c for c in s if unicodedata.category(c) != "Mn")
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

fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.8, 3.0))


def comp(ax, col, cats, tit, c1, c2):
    d1, d2 = cat(est[col], cats), cat(sub[col], cats)
    k = [x for x, _ in cats]
    y = np.arange(len(k))
    ax.barh(y + .19, [100 * d1[x] / N for x in k], height=.36, color=c1,
            label="Departamento")
    ax.barh(y - .19, [100 * d2[x] / n10 for x in k], height=.36, color=c2,
            label="10 más afectados")
    ax.set_yticks(y)
    import textwrap
    ax.set_yticklabels(["\n".join(textwrap.wrap(x, 22)) for x in k], fontsize=7.4)
    ax.invert_yaxis()
    ax.set_xlabel("% de establecimientos", fontsize=7.8)
    ax.legend(fontsize=7, frameon=False, loc="lower right")
    ax.set_title(tit, fontsize=8.8, fontweight="bold", loc="left", color=AZULT)


comp(a1, "Principal necesidad", CAT_NEC, "Principal necesidad", AZU, ROJO)
comp(a2, "Apoyo financiero", CAT_APO, "Apoyo financiero preferido", "#5b8def", NAR)
plt.tight_layout()
plt.savefig("g2_necesidades.png", bbox_inches="tight")
plt.close()

# ── G3 · ranking del indice ──────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(7.6, 4.6))
t = M.nlargest(15, "IAE_aj").iloc[::-1]
y = np.arange(len(t))
ax.barh(y, t.IAE_aj, height=.68,
        color=[ROJO if v >= 85 else NAR if v >= 70 else AMA for v in t.IAE_aj])
for i, r in enumerate(t.itertuples()):
    ax.text(r.IAE_aj + 1.2, i, f"{r.IAE_aj:.0f}   n={mil(r.n)}", va="center",
            fontsize=7.6, color="#3a3a3a")
ax.set_yticks(y)
ax.set_yticklabels([m.title() for m in t.municipio], fontsize=8.4)
ax.set_xlim(0, 122)
ax.set_xlabel("Índice de afectación económica ajustado (0–100)")
ax.set_title("Municipios con mayor afectación económica", fontsize=10,
             fontweight="bold", loc="left", color=AZULT, pad=10)
plt.tight_layout()
plt.savefig("g3_ranking.png", bbox_inches="tight")
plt.close()

# ── G5 · contraste con fuentes externas ──────────────────────────────────
fig, ax = plt.subplots(figsize=(7.6, 2.9))
cats = ["Crítica o grave\n(Cali)", "No puede operar\n(Cali)",
        "No opera con\nnormalidad (Valle)", "Empleo en riesgo\n(Valle)"]
nuestro = [D["cali"]["sev"], D["cali"]["noop"], D["noop_norm"], D["empleo"]["pct"]]
externo = [D["conf"]["cali_sev"], D["conf"]["cali_noop"], D["wwb"]["noop"], np.nan]
x = np.arange(len(cats))
ax.bar(x - .19, nuestro, .36, color=AZU, label=f"Esta base (1 sep · {mil(N)} únicos)")
ax.bar(x + .19, [0 if np.isnan(v) else v for v in externo], .36, color=NAR,
       label="Fuentes externas (ago)")
for i, (a, b_) in enumerate(zip(nuestro, externo)):
    ax.text(i - .19, a + 1.4, f"{a:.1f} %".replace(".", ","), ha="center", fontsize=7.8)
    if not np.isnan(b_):
        ax.text(i + .19, b_ + 1.4, f"{b_:.0f} %", ha="center", fontsize=7.8)
    else:
        ax.text(i + .19, 2, "sin dato\ncomparable", ha="center", fontsize=6.6, color=GRIS)
ax.set_xticks(x)
ax.set_xticklabels(cats, fontsize=7.8)
ax.set_ylim(0, 92)
ax.set_ylabel("%")
ax.legend(fontsize=7.4, frameon=False)
ax.set_title("Contraste con la Cámara de Comercio de Cali y la Fundación WWB",
             fontsize=9.6, fontweight="bold", loc="left", color=AZULT, pad=10)
plt.tight_layout()
plt.savefig("g5_contraste.png", bbox_inches="tight")
plt.close()
print("g1, g2, g3 y g5 regenerados sobre la base depurada")
