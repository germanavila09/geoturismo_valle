"""Ranking de pérdidas declaradas por municipio, para la columna de la lámina.

Formato estrecho y alto (3,3 × 5,3 pulgadas) porque va al lado del mapa.
Cali sale del ranking y se declara aparte: con $7.770 M frente a $1.825 M del
segundo, dejaría las otras barras en un hilo.

La cifra es la COTA INFERIOR: la encuesta pregunta por rangos, así que se suma
el piso de cada rango declarado más $100 millones por cada reporte del tramo
abierto («más de $100 millones»). El daño real es mayor y no puede estimarse
sin pedir el monto exacto.
"""
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

CREMA = "#FFF9E9"
AZULT = "#1F3864"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "axes.spines.bottom": False, "axes.edgecolor": "#8a8a8a",
                     "figure.dpi": 205, "figure.facecolor": CREMA,
                     "axes.facecolor": CREMA, "savefig.facecolor": CREMA,
                     "ytick.color": "#1a1a1a"})

R = json.load(open("turismo_mun_0903.json", encoding="utf-8"))
MU = pd.DataFrame(R["municipios"])
TUR = R["turismo"]
mil = lambda x: f"{x:,}".replace(",", ".")

NOMBRE = {"ALCALA": "Alcalá", "CAICEDONIA": "Caicedonia", "JAMUNDI": "Jamundí",
          "LA UNION": "La Unión", "RIOFRIO": "Riofrío", "TULUA": "Tuluá",
          "CALI": "Cali", "BUGA": "Buga"}
MU["et"] = MU.municipio.map(lambda m: NOMBRE.get(m, m.title().replace(" De ", " de ")))

cali = MU[MU.municipio == "CALI"].iloc[0]
t = MU[MU.municipio != "CALI"].nlargest(12, "perd_min").iloc[::-1]

fig, ax = plt.subplots(figsize=(3.3, 4.5))
col = ["#7a1410" if v >= 600 else "#ad2f1e" if v >= 250 else "#d45c43"
       for v in t.perd_min]
ax.barh(range(len(t)), t.perd_min, color=col, height=.70)
for i, r in enumerate(t.itertuples()):
    ax.text(r.perd_min + max(t.perd_min) * .035, i, "$" + mil(int(r.perd_min)),
            va="center", fontsize=8.2, color="#2a2a2a", fontweight="bold")
ax.set_yticks(range(len(t)))
ax.set_yticklabels(t.et, fontsize=8.8)
ax.set_xlim(0, max(t.perd_min) * 1.34)
ax.set_xticks([])
# La unidad va en el título: un xlabel debajo choca con el texto de la lámina.
ax.set_title(f"Los {len(t)} siguientes, en millones de pesos\n"
             f"Cali aparte con ${mil(int(cali.perd_min))} M",
             fontsize=9.4, fontweight="bold", loc="left", color=AZULT, pad=10)
plt.tight_layout()
plt.savefig("mt5_ranking.png", bbox_inches="tight", facecolor=CREMA)
plt.close()

print("mt5_ranking.png")
tot = MU.perd_min.sum()
print(f"  departamento ${mil(TUR['perd_min'])} M · Cali {100 * cali.perd_min / tot:.0f} %"
      f" · los 5 primeros {100 * MU.nlargest(5, 'perd_min').perd_min.sum() / tot:.0f} %")
print(MU.nlargest(8, "perd_min")[["municipio", "perd_min", "perd_ab", "base_perd",
                                  "pct_perd_alta"]].to_string(index=False))
