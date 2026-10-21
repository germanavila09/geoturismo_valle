"""Gráficas del deck de turismo, sobre el universo definido por sector.

Sin título ni bajada dentro de la figura: los pone la lámina, y repetirlos
roba área útil y se lee como duplicado.
"""
import json
import textwrap
from decimal import ROUND_HALF_UP, Decimal

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

CREMA = "#FFF9E9"          # el color exacto de la plantilla de la Gobernación
AZULT = "#1F3864"
ROJO, NAR, AMA, VER, AZU, GRIS = "#b3261e", "#d97706", "#eab308", "#4a9c5d", "#1f6feb", "#9aa0a6"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#8a8a8a", "figure.dpi": 200,
                     "figure.facecolor": CREMA, "axes.facecolor": CREMA,
                     "savefig.facecolor": CREMA,
                     "ytick.color": "#1a1a1a", "xtick.color": "#4a4a4a"})

R = json.load(open("turismo_mun_0903.json", encoding="utf-8"))
MU = pd.DataFrame(R["municipios"])
TUR, TOD = R["turismo"], R["todos"]
mil = lambda x: f"{x:,}".replace(",", ".")


def com(x, d=1):
    """Python redondea 16,25 a 16,2 (al par) y JavaScript a 16,3. Con la misma
    cifra en el gráfico y en el texto de la lámina, la discrepancia se ve."""
    q = Decimal(str(x)).quantize(Decimal("1." + "0" * d), rounding=ROUND_HALF_UP)
    return str(q).replace(".", ",")


def guardar(f):
    plt.savefig(f, bbox_inches="tight", facecolor=CREMA)
    plt.close()
    print("  ", f)


NOMBRE = {"ALCALA": "Alcalá", "ANDALUCIA": "Andalucía", "BOLIVAR": "Bolívar",
          "CAICEDONIA": "Caicedonia", "EL AGUILA": "El Águila", "GUACARI": "Guacarí",
          "JAMUNDI": "Jamundí", "LA UNION": "La Unión", "RIOFRIO": "Riofrío",
          "TULUA": "Tuluá", "BUGA": "Buga", "CALI": "Cali"}
bonito = lambda m: NOMBRE.get(m, m.title().replace(" De ", " de "))
MU["et"] = MU.municipio.map(bonito)

print("gráficas del turismo:")

# ══ T1 · severidad por municipio ═════════════════════════════════════════
fig, ax = plt.subplots(figsize=(8.4, 4.9))
# Cali sale del gráfico: con 667 de 1.703 aplasta la escala y deja ilegibles
# a los quince siguientes. Se declara aparte, no se esconde.
cali = MU[MU.municipio == "CALI"].iloc[0]
t = MU[MU.municipio != "CALI"].nlargest(15, "n").iloc[::-1]
capas = [("critica", "Crítica", ROJO), ("grave", "Grave", "#e2574c"),
         ("moderada", "Moderada", NAR), ("baja", "Baja", VER),
         ("sin_clasif", "Sin clasificación", GRIS),
         ("no_afectado", "Declara no afectación", "#c9c2b0")]
izq = np.zeros(len(t))
for c, et, col in capas:
    ax.barh(range(len(t)), t[c], left=izq, color=col, height=.72, label=et)
    izq = izq + t[c].values
for i, v in enumerate(izq):
    ax.text(v + max(izq) * .012, i, mil(int(v)), va="center", fontsize=8,
            fontweight="bold", color="#2a2a2a")
ax.set_yticks(range(len(t)))
ax.set_yticklabels(t.et, fontsize=9)
ax.set_xlim(0, max(izq) * 1.13)
ax.set_xlabel("Negocios turísticos que reportaron daño", fontsize=9)
ax.legend(fontsize=7.4, frameon=False, ncol=6, loc="lower right",
          bbox_to_anchor=(1.02, -0.16))
guardar("t1_severidad.png")

# ══ T3 · empleo por tramos y pérdidas ═══════════════════════════════════
# Se cuentan ESTABLECIMIENTOS por tramo de empleo, no empleos acotados entre
# dos cotas. La encuesta pregunta por rangos, así que el número de negocios en
# cada tramo es un dato exacto; el número de empleos nunca lo es.
fig, (a1, a2) = plt.subplots(1, 2, figsize=(8.4, 4.4))
MU["empl_con"] = MU.empl_t1 + MU.empl_t2 + MU.empl_t3
t = MU.nlargest(12, "empl_con").iloc[::-1]
TRAMOS = [("empl_t1", "De 1 a 5 empleos", "#8fb8f0"),
          ("empl_t2", "De 6 a 20", AZU),
          ("empl_t3", "Más de 20", "#0b3d91")]
izq = np.zeros(len(t))
for c, et, col in TRAMOS:
    a1.barh(range(len(t)), t[c], left=izq, color=col, height=.68, label=et)
    izq = izq + t[c].values
for i, v in enumerate(izq):
    a1.text(v + max(izq) * .02, i, mil(int(v)), va="center", fontsize=7.6,
            fontweight="bold", color="#2a2a2a")
a1.set_yticks(range(len(t)))
a1.set_yticklabels(t.et, fontsize=8.2)
a1.set_xlim(0, max(izq) * 1.16)
a1.set_xlabel("Establecimientos con al menos un empleo comprometido", fontsize=8)
a1.legend(fontsize=7.4, frameon=False, loc="lower right", ncol=1)
a1.set_title("Negocios con empleo comprometido", fontsize=9.6, fontweight="bold",
             loc="left", color=AZULT)

t = MU.nlargest(12, "perd_min").iloc[::-1]
a2.barh(range(len(t)), t.perd_min, color=ROJO, height=.68)
for i, r in enumerate(t.itertuples()):
    a2.text(r.perd_min + max(t.perd_min) * .02, i, "$" + mil(int(r.perd_min)) + " M",
            va="center", fontsize=7.4, color="#3a3a3a")
a2.set_yticks(range(len(t)))
a2.set_yticklabels(t.et, fontsize=8.2)
a2.set_xlim(0, max(t.perd_min) * 1.34)
a2.set_xticks([])
a2.spines["bottom"].set_visible(False)
a2.set_title("Pérdidas declaradas · cota inferior", fontsize=9.6, fontweight="bold",
             loc="left", color=AZULT)
plt.tight_layout()
guardar("t3_empleo_perdidas.png")

# ══ T4 · alivios solicitados ═════════════════════════════════════════════
fig, (a1, a2) = plt.subplots(1, 2, figsize=(8.4, 3.7))


def panel(ax, dic, base, titulo, paleta):
    d = dict(sorted(dic.items(), key=lambda kv: -kv[1]))
    k = list(d)[::-1]
    v = [100 * d[x] / base for x in k]
    ax.barh(range(len(k)), v, color=[paleta(x) for x in v], height=.62)
    for i, x in enumerate(v):
        ax.text(x + 1.2, i, com(x) + " %", va="center", fontsize=8,
                fontweight="bold", color="#2a2a2a")
    ax.set_yticks(range(len(k)))
    ax.set_yticklabels(["\n".join(textwrap.wrap(x, 22)) for x in k], fontsize=7.8)
    ax.set_xlim(0, max(v) * 1.3)
    ax.set_xticks([])
    ax.spines["bottom"].set_visible(False)
    ax.set_title(titulo, fontsize=9.4, fontweight="bold", loc="left", color=AZULT)


panel(a1, TUR["nec"], TUR["base_nec"],
      f"Qué necesitan\n{mil(TUR['base_nec'])} responden",
      lambda x: ROJO if x > 30 else NAR if x > 15 else GRIS)
panel(a2, TUR["apo"], TUR["base_apo"],
      f"Qué instrumento prefieren\n{mil(TUR['base_apo'])} opinan",
      lambda x: VER if x > 40 else AZU if x > 15 else GRIS)
plt.tight_layout()
guardar("t4_alivios.png")

# ══ T5 · turismo frente al resto de la economía ══════════════════════════
fig, ax = plt.subplots(figsize=(8.0, 3.9))
IND = [("pct_sev", "Crítica o grave"), ("pct_no_opera", "No puede operar"),
       ("pct_perd_alta", "Pérdidas > $20M"), ("pct_empl", "Con empleo en riesgo")]
x = np.arange(len(IND))
tur = [TUR[c] for c, _ in IND]
tod = [TOD[c] for c, _ in IND]
ax.bar(x - .2, tod, .4, color=GRIS, label=f"Toda la economía ({mil(TOD['n'])})")
ax.bar(x + .2, tur, .4, color=ROJO, label=f"Cadena turística ({mil(TUR['n'])})")
for i, (a, b_) in enumerate(zip(tod, tur)):
    ax.text(i - .2, a + 1.4, com(a) + " %", ha="center", fontsize=8, color="#3a3a3a")
    ax.text(i + .2, b_ + 1.4, com(b_) + " %", ha="center", fontsize=8,
            fontweight="bold", color=ROJO)
ax.set_xticks(x)
ax.set_xticklabels([e for _, e in IND], fontsize=8.6)
ax.set_ylim(0, 100)
ax.set_ylabel("% de establecimientos", fontsize=8.6)
ax.legend(fontsize=8, frameon=False, loc="upper left")
guardar("t5_contraste.png")

print(f"\nturismo {mil(TUR['n'])} · crítico o grave {com(TUR['pct_sev'])} % · "
      f"empleos {mil(TUR['empl_lo'])}–{mil(TUR['empl_hi'])} · "
      f"pérdidas ${mil(TUR['perd_min'])} M")
