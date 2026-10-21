"""Gráficas del perfil del sector con la estructura del informe de la
Secretaría de Desarrollo Económico: continuidad del negocio, qué se dañó y
tipos de negocio.

Sin títulos dentro de la figura: el título va en la lámina.
"""
import json
from decimal import Decimal, ROUND_HALF_UP

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

CREMA = "#FFF9E9"
AZUL, ROJO, NAR, VER, GRIS = "#1F3864", "#B3261E", "#C2410C", "#2D6A4F", "#9A9A9A"
plt.rcParams.update({"font.family": "DejaVu Sans", "axes.facecolor": CREMA,
                     "figure.facecolor": CREMA, "axes.edgecolor": "#CFC7B0",
                     "axes.labelcolor": "#2A2A2A", "text.color": "#2A2A2A",
                     "xtick.color": "#4A4A4A", "ytick.color": "#4A4A4A"})

R = json.load(open("perfil_turismo.json", encoding="utf-8"))
TU, TD, SE = R["turismo"], R["todos"], R["secretaria"]


def com(x, d=1):
    q = Decimal(str(x)).quantize(Decimal("1." + "0" * d), rounding=ROUND_HALF_UP)
    return str(q).replace(".", ",")


mil = lambda x: f"{x:,}".replace(",", ".")


def guardar(f):
    plt.savefig(f, bbox_inches="tight", facecolor=CREMA, dpi=200)
    plt.close()
    print("  ", f)


print("gráficas del perfil:")

# ══ P1 · continuidad del negocio ═════════════════════════════════════════
# Barra apilada al 100 %, turismo arriba y departamento abajo, para que se vea
# que el turismo tiene más cierre y menos operación normal con la misma escala.
fig, ax = plt.subplots(figsize=(8.6, 2.5))
filas = [(f"Cadena turística\n{mil(TU['base_cont'])} informan", TU),
         (f"Toda la economía\n{mil(TD['base_cont'])} informan", TD)]
capas = [("pct_normal", "Opera normalmente", VER),
         ("pct_parcial", "Opera parcialmente", NAR),
         ("pct_no_opera", "No puede operar", ROJO)]
for i, (et, d) in enumerate(filas):
    izq = 0
    for k, lab, col in capas:
        v = d[k]
        ax.barh(i, v, left=izq, color=col, height=.5,
                label=lab if i == 0 else None)
        if v >= 6:
            ax.text(izq + v / 2, i, f"{com(v)} %", ha="center", va="center",
                    color="white", fontsize=10.5, fontweight="bold")
        izq += v
ax.set_yticks(range(len(filas)))
ax.set_yticklabels([f[0] for f in filas], fontsize=9.5)
ax.invert_yaxis()
ax.set_xlim(0, 100)
ax.set_xticks([])
for s in ("top", "right", "bottom", "left"):
    ax.spines[s].set_visible(False)
ax.legend(fontsize=9, frameon=False, ncol=3, loc="lower center",
          bbox_to_anchor=(0.5, -0.30))
guardar("p1_continuidad.png")

# ══ P2 · qué se dañó ═════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(8.6, 3.5))
CAT = ["Infraestructura, maquinaria o equipos",
       "Reducción de clientes, pedidos o ventas",
       "Inventarios o mercancías",
       "Proveedores, logística o servicios públicos"]
CORTO = ["Infraestructura,\nmaquinaria o equipos", "Reducción de clientes,\npedidos o ventas",
         "Inventarios o\nmercancías", "Proveedores, logística\no servicios públicos"]
t = [100 * TU["dano"].get(c, 0) / TU["base_dano"] for c in CAT]
g = [100 * TD["dano"].get(c, 0) / TD["base_dano"] for c in CAT]
y = np.arange(len(CAT))
ax.barh(y + .19, g, height=.36, color=GRIS, label=f"Toda la economía ({mil(TD['base_dano'])})")
ax.barh(y - .19, t, height=.36, color=ROJO, label=f"Cadena turística ({mil(TU['base_dano'])})")
for i, (a, b) in enumerate(zip(t, g)):
    ax.text(a + 1.2, i - .19, f"{com(a)} %", va="center", fontsize=9,
            fontweight="bold", color=ROJO)
    ax.text(b + 1.2, i + .19, f"{com(b)} %", va="center", fontsize=9, color="#5A5A5A")
ax.set_yticks(y)
ax.set_yticklabels(CORTO, fontsize=9)
ax.invert_yaxis()
ax.set_xlim(0, max(t + g) * 1.22)
ax.set_xlabel("% de establecimientos que marcan la opción", fontsize=9)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.legend(fontsize=8.5, frameon=False, loc="lower right")
guardar("p2_dano.png")

# ══ P3 · tipos de negocio ════════════════════════════════════════════════
# Dos paneles: cuántos son y qué tan golpeado está cada tipo. El segundo panel
# es el que decide a quién priorizar; el primero solo da el tamaño.
TI = R["tipificables"]
nom = [t["tipo"].replace("Cafes, panaderias y heladerias", "Cafés, panaderías\ny heladerías")
       .replace("Bares y entretenimiento nocturno", "Bares y\nentretenimiento")
       .replace("Agencias y operadores turisticos", "Agencias y\noperadores")
       .replace("Atractivos y recreacion", "Atractivos y\nrecreación")
       .replace("Restaurantes y comidas", "Restaurantes\ny comidas")
       .replace("Transporte de pasajeros", "Transporte\nde pasajeros")
       .replace("Eventos y banquetes", "Eventos y\nbanquetes") for t in TI]
fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.2, 4.0))
y = np.arange(len(TI))[::-1]

a1.barh(y, [t["n"] for t in TI], color=AZUL, height=.66)
for i, t in enumerate(TI):
    a1.text(t["n"] + max(x["n"] for x in TI) * .02, y[i],
            f"{mil(t['n'])} · {com(t['pct_tipificables'])} %", va="center",
            fontsize=8.6, fontweight="bold", color="#2a2a2a")
a1.set_yticks(y)
a1.set_yticklabels(nom, fontsize=8.6)
a1.set_xlim(0, max(x["n"] for x in TI) * 1.36)
a1.set_xlabel("Establecimientos afectados", fontsize=9)
a1.set_title("Cuántos son", fontsize=10, fontweight="bold", color=AZUL, loc="left")

a2.barh(y, [t["pct_sev"] for t in TI], color=ROJO, height=.66)
for i, t in enumerate(TI):
    a2.text(t["pct_sev"] + 1.6, y[i], f"{com(t['pct_sev'])} %", va="center",
            fontsize=8.6, fontweight="bold", color=ROJO)
a2.axvline(TU["pct_sev"], color=AZUL, lw=1.3, ls="--")
a2.text(TU["pct_sev"], len(TI) - .3, f"  sector {com(TU['pct_sev'])} %",
        fontsize=8.2, color=AZUL, va="bottom")
a2.set_yticks(y)
a2.set_yticklabels([])
a2.set_xlim(0, 100)
a2.set_xlabel("% en nivel crítico o grave", fontsize=9)
a2.set_title("Qué tan golpeados están", fontsize=10, fontweight="bold",
             color=AZUL, loc="left")
for ax in (a1, a2):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
plt.tight_layout()
guardar("p3_tipos.png")

print(f"\ncontinuidad turismo: {com(TU['pct_normal'])} / {com(TU['pct_parcial'])} / "
      f"{com(TU['pct_no_opera'])}  ·  departamento {com(TD['pct_normal'])} / "
      f"{com(TD['pct_parcial'])} / {com(TD['pct_no_opera'])}")
print(f"tipificables: {R['base_tipo']} de {TU['n']}")
