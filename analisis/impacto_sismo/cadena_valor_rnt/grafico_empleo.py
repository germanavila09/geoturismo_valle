"""Gráfico de «Empleos afectados o en riesgo» por municipio, en tramos.

QUE SE CUENTA Y POR QUE
La encuesta no pregunta cuántos empleos: ofrece rangos (Ninguno, 1 a 5, 6 a 20,
21 a 50, más de 50). Por eso NO se grafica el número de empleos —que solo puede
acotarse en un intervalo y confunde— sino el número de ESTABLECIMIENTOS en cada
tramo, que es un conteo exacto.

«Ninguno» queda fuera de las barras: son negocios sin empleo comprometido.
Los tramos «21 a 50» y «más de 50» se agrupan en «más de 20» porque juntos son
34 casos en todo el departamento: separarlos deja dos series invisibles.

Cali va en un eje propio arriba: con 406 de 1.077 aplasta la escala de los
otros 39 municipios. Comparten el mismo eje horizontal, así que las barras
siguen siendo comparables entre los dos paneles.
"""
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

CREMA = "#FFF9E9"
AZULT = "#1F3864"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#8a8a8a", "figure.dpi": 205,
                     "figure.facecolor": CREMA, "axes.facecolor": CREMA,
                     "savefig.facecolor": CREMA,
                     "ytick.color": "#1a1a1a", "xtick.color": "#4a4a4a"})

R = json.load(open("turismo_mun_0903.json", encoding="utf-8"))
MU = pd.DataFrame(R["municipios"])
TUR = R["turismo"]
mil = lambda x: f"{x:,}".replace(",", ".")
ent = lambda x: f"{x:.0f}"
com = lambda x: f"{x:.1f}".replace(".", ",")

NOMBRE = {"ALCALA": "Alcalá", "ANDALUCIA": "Andalucía", "BOLIVAR": "Bolívar",
          "CAICEDONIA": "Caicedonia", "EL AGUILA": "El Águila", "GUACARI": "Guacarí",
          "JAMUNDI": "Jamundí", "LA UNION": "La Unión", "RIOFRIO": "Riofrío",
          "TULUA": "Tuluá", "BUGA": "Buga", "CALI": "Cali"}
MU["et"] = MU.municipio.map(lambda m: NOMBRE.get(m, m.title().replace(" De ", " de ")))
MU["con"] = MU.empl_t1 + MU.empl_t2 + MU.empl_t3

TRAMOS = [("empl_t1", "De 1 a 5 empleos", "#9fc2f2"),
          ("empl_t2", "De 6 a 20 empleos", "#1f6feb"),
          ("empl_t3", "Más de 20 empleos", "#0b3d91")]

cali = MU[MU.municipio == "CALI"].iloc[0]
t = MU[(MU.municipio != "CALI") & (MU.con > 0)].sort_values("con").reset_index(drop=True)

# Cada panel lleva su propia escala. Compartirla dejaba el panel de abajo
# comprimido en la quinta parte del ancho: ilegible para 39 municipios.
XMAX_C = cali.con * 1.42
XMAX = t.con.max() * 1.60

# Posiciones explícitas: con gridspec el panel de Cali quedaba con un hueco
# enorme y el título se montaba sobre la bajada.
fig = plt.figure(figsize=(8.6, 9.9))
axC = fig.add_axes([0.170, 0.876, 0.795, 0.026])
ax = fig.add_axes([0.170, 0.112, 0.795, 0.728])


def pintar(eje, filas, altura, xmax, etiquetar_leyenda):
    izq = np.zeros(len(filas))
    for c, et, col in TRAMOS:
        v = np.array([getattr(r, c) for r in filas], dtype=float)
        eje.barh(range(len(filas)), v, left=izq, color=col, height=altura,
                 label=et if etiquetar_leyenda else None)
        izq = izq + v
    for i, r in enumerate(filas):
        eje.text(izq[i] + xmax * .012, i,
                 f"{mil(int(izq[i]))} de {mil(r.base_empl)}   ·   "
                 f"{ent(100 * izq[i] / r.base_empl)} %",
                 va="center", fontsize=7.6, color="#3a3a3a")
    eje.set_yticks(range(len(filas)))
    eje.set_yticklabels([r.et for r in filas], fontsize=8.6)
    eje.set_xlim(0, xmax)


pintar(axC, [cali], .60, XMAX_C, False)
pintar(ax, list(t.itertuples()), .74, XMAX, True)

axC.set_ylim(-.62, .62)
axC.tick_params(axis="x", labelsize=7.6)
axC.set_xticks([0, 100, 200, 300, 400])
axC.text(1.0, 1.9, "Cali, en escala propia", transform=axC.transAxes, ha="right",
         fontsize=8.2, color="#8a8a8a", va="bottom")
ax.set_xlabel("Establecimientos turísticos con al menos un empleo comprometido",
              fontsize=9.2, labelpad=7)
# La leyenda va abajo a la derecha: arriba choca con la etiqueta de
# Buenaventura, que es la barra más larga del panel.
ax.legend(fontsize=8.8, frameon=False, loc="lower right",
          bbox_to_anchor=(1.0, 0.045))

fig.text(.012, .980, "Empleos afectados o en riesgo en la cadena turística",
         fontsize=15, fontweight="bold", color=AZULT, va="top")
fig.text(.012, .950,
         f"{mil(TUR['empl_t1'] + TUR['empl_t2'] + TUR['empl_t3'])} negocios con al menos un empleo comprometido  ·  "
         f"{com(100 * (TUR['empl_t1'] + TUR['empl_t2'] + TUR['empl_t3']) / TUR['base_empl'])} % de los {mil(TUR['base_empl'])} que "
         f"responden la pregunta  ·  {com(100 * (TUR['empl_t1'] + TUR['empl_t2'] + TUR['empl_t3']) / TUR['n'])} % de los "
         f"{mil(TUR['n'])} negocios turísticos afectados",
         fontsize=9.4, color="#5a5a5a", va="top")
fig.text(.012, .928,
         "Cada barra muestra cuántos negocios de los que respondieron en ese municipio "
         "tienen empleo comprometido",
         fontsize=8.6, color="#8a8a8a", va="top")
# El pie se parte a mano: una sola línea larga se sale del ancho de la figura.
fig.text(.012, .012,
         "Se cuentan establecimientos, no empleos. La encuesta pregunta por rangos, así "
         "que el número de negocios en cada\ntramo es exacto y el de empleos no. Los "
         f"tramos «21 a 50» y «más de 50» se agrupan porque suman {TUR['empl_t3']} casos "
         f"en todo\nel departamento. Quedan fuera los {mil(TUR['empl_ninguno'])} negocios "
         f"que declaran «Ninguno» y los {mil(TUR['n'] - TUR['base_empl'])} que dejaron la "
         "pregunta en blanco.",
         fontsize=8, color="#6a6a6a", va="bottom", linespacing=1.5)

plt.savefig("empleos_por_municipio.png", facecolor=CREMA)
plt.close()

print("empleos_por_municipio.png")
print(f"  {len(t) + 1} municipios · "
      f"{mil(TUR['empl_t1'] + TUR['empl_t2'] + TUR['empl_t3'])} negocios con empleo "
      f"comprometido de {mil(TUR['base_empl'])} que responden")
print(f"  1 a 5: {mil(TUR['empl_t1'])} · 6 a 20: {mil(TUR['empl_t2'])} · "
      f"más de 20: {TUR['empl_t3']}")
