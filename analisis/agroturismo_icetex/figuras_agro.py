"""Figuras de la línea base de agroturismo.

Reutiliza el motor de coropléticos de mapas_turismo.py —misma proyección,
mismos rótulos por municipio, misma leyenda por clases— cambiando solo la
tabla de datos. Sin títulos dentro de la figura: el pie de figura va en el
informe.
"""
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Se ejecuta mapas_turismo.py hasta la definición de mapa(), sin dibujar nada.
_src = open("mapas_turismo.py", encoding="utf-8").read()
_g = {}
exec(_src.split('ROJOS = [')[0], _g)
mapa, clave, bonito, mil = _g["mapa"], _g["clave"], _g["bonito"], _g["mil"]

R = json.load(open("agroturismo.json", encoding="utf-8"))
MU = pd.DataFrame(R["municipios"])
MU["k"] = MU.municipio.map(clave)
_g["DAT"] = MU.set_index("k")          # el motor lee DAT de su propio ámbito

CREMA = "#FFF9E9"
AZUL, ROJO, NAR, VER, GRIS = "#1F3864", "#B3261E", "#C2410C", "#2D6A4F", "#8A8A8A"
VERDES = ["#eaf3e7", "#c6e0bf", "#93c391", "#5fa267", "#2f7d47", "#12522c"]
ROJOS = ["#fde8d5", "#fbc79b", "#f39a5c", "#dd6031", "#b3261e", "#7a1410"]

print("figuras de agroturismo:")

# ══ AG1 · oferta de alojamiento y atractivo rural ════════════════════════
mapa("rnt_rural", "", "", "Prestadores rurales\ncon RNT vigente",
     "ag1_oferta_rural.png", [2, 10, 25, 50, 100], VERDES,
     sin_dato="sin prestadores rurales inscritos")

# ══ AG2 · qué tan rural es la oferta de cada municipio ═══════════════════
mapa("pct_rural", "", "", "% de la oferta formal\nque es rural",
     "ag2_ruralidad.png", [10, 25, 40, 55, 70], VERDES,
     fmtf=lambda x: f"{x:.0f} %", sin_dato="sin prestadores inscritos")

plt.rcParams.update({"font.family": "DejaVu Sans", "axes.facecolor": CREMA,
                     "figure.facecolor": CREMA, "axes.edgecolor": "#CFC7B0",
                     "text.color": "#2A2A2A", "xtick.color": "#4A4A4A",
                     "ytick.color": "#4A4A4A"})
c1 = lambda x: f"{x:.1f}".replace(".", ",")

# ══ AG3 · vocación rural frente a daño turístico ═════════════════════════
# El cuadrante superior derecho es el que interesa al proyecto: hay con qué
# trabajar (oferta rural inscrita) y hay por qué hacerlo (daño declarado).
fig, ax = plt.subplots(figsize=(8.6, 5.6))
d = MU[(MU.rnt_rural > 0) | (MU.tur_n > 0)].copy()
d = d[d.municipio != "CALI"]          # Cali aplasta las dos escalas; va aparte
mx, my = d.rnt_rural.median(), d.tur_n.median()
ax.axvline(mx, color=GRIS, lw=1, ls="--", zorder=1)
ax.axhline(my, color=GRIS, lw=1, ls="--", zorder=1)
col = np.where((d.rnt_rural >= mx) & (d.tur_n >= my), ROJO, AZUL)
ax.scatter(d.rnt_rural, d.tur_n, s=26 + d.tur_perd_min / 12, c=col,
           alpha=.82, edgecolor="white", linewidth=.8, zorder=3)

DIRS = [(6, 4), (6, -10), (-6, 4), (-6, -10), (0, 12), (0, -16),
        (12, 4), (-12, 4), (10, -14), (-10, -14), (6, 16), (-6, 16),
        (6, -22), (-6, -22), (0, 24), (0, -28)]


def etiquetar(ax, filas, cx, cy, fs=7.6):
    """Coloca cada rótulo en el primer desplazamiento libre. Los
    desplazamientos van en PUNTOS y transData devuelve PÍXELES: sin el factor
    dpi/72 las cajas de colisión quedan mal y los rótulos se montan."""
    k = ax.figure.dpi / 72.0
    cajas = []
    for _, r in filas.iterrows():
        x0, y0 = ax.transData.transform((r[cx], r[cy]))
        txt = bonito(r.municipio)
        w, h = 6.6 * k * len(txt), 12 * k
        for dx, dy in DIRS:
            bx = x0 + dx * k - (w if dx < 0 else 0) - (w / 2 if dx == 0 else 0)
            by = y0 + dy * k - h / 2
            caja = (bx, by, bx + w, by + h)
            if all(not (caja[0] < c[2] and c[0] < caja[2]
                        and caja[1] < c[3] and c[1] < caja[3]) for c in cajas):
                cajas.append(caja)
                ax.annotate(txt, (r[cx], r[cy]), textcoords="offset points",
                            xytext=(dx, dy), fontsize=fs, color="#2a2a2a",
                            ha="right" if dx < 0 else ("center" if dx == 0 else "left"),
                            va="center", zorder=5,
                            path_effects=[pe.withStroke(linewidth=2,
                                                        foreground=CREMA)])
                break


# Rotular todo lo que pase la mediana satura la esquina baja izquierda, donde
# hay veinte municipios pequeños pegados. Se rotula lo que el proyecto va a
# mirar: lo que supera un umbral en cualquiera de los dos ejes, más los seis
# que la Gobernación ya priorizó.
PRIO = R["priorizados_gobernacion"]
marca = (d.rnt_rural >= 14) | (d.tur_n >= 30) | d.municipio.isin(PRIO)
# Los ejes y el lienzo deben estar resueltos antes de medir colisiones: sin
# esto transData devuelve una escala provisional y las cajas no corresponden a
# los píxeles finales, que fue exactamente lo que montó «Palmira» sobre «Dagua».
ax.set_xlabel("Prestadores rurales con RNT vigente  ·  vocación agroturística", fontsize=10)
ax.set_ylabel("Negocios turísticos que reportaron daño", fontsize=10)
plt.tight_layout()
fig.canvas.draw()
etiquetar(ax, d[marca], "rnt_rural", "tur_n")
cali = MU[MU.municipio == "CALI"].iloc[0]
ax.text(.985, .035, f"Cali queda fuera de la escala: {cali.rnt_rural} prestadores "
        f"rurales y {mil(int(cali.tur_n))} negocios afectados",
        transform=ax.transAxes, ha="right", fontsize=8, color="#6a6a6a", style="italic")
ax.text(.985, .965, "hay oferta rural\ny hay daño", transform=ax.transAxes,
        ha="right", va="top", fontsize=9, color=ROJO, fontweight="bold")
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
plt.tight_layout()
plt.savefig("ag3_cuadrantes.png", bbox_inches="tight", facecolor=CREMA, dpi=200)
plt.close()
print("   ag3_cuadrantes.png")

# ══ AG4 · índice de priorización, abierto en sus tres componentes ════════
fig, ax = plt.subplots(figsize=(8.6, 5.4))
t = MU.nlargest(15, "indice").iloc[::-1]
y = np.arange(len(t))
capas = [("i_vocacion", "Vocación rural", VER),
         ("i_dano", "Daño declarado", ROJO),
         ("i_severidad", "Severidad", NAR)]
izq = np.zeros(len(t))
P = R["pesos"]
for c, lab, color in capas:
    v = t[c].values * P[c.split("_")[1]]
    ax.barh(y, v, left=izq, color=color, height=.7, label=lab)
    izq = izq + v
for i, v in enumerate(izq):
    ax.text(v + 1.1, i, c1(v), va="center", fontsize=8.6, fontweight="bold",
            color="#2a2a2a")
ax.set_yticks(y)
ax.set_yticklabels([bonito(m) for m in t.municipio], fontsize=9)
ax.set_xlim(0, izq.max() * 1.14)
ax.set_xlabel("Índice de priorización (0 a 100) · los tres componentes pesan igual",
              fontsize=9.5)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.legend(fontsize=8.6, frameon=False, ncol=3, loc="lower right")
plt.tight_layout()
plt.savefig("ag4_indice.png", bbox_inches="tight", facecolor=CREMA, dpi=200)
plt.close()
print("   ag4_indice.png")

print(f"\nmediana de corte en el cuadrante: {mx:.0f} prestadores rurales · "
      f"{my:.0f} negocios afectados")
