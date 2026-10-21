"""Mapas coropléticos del turismo, apaisados para el deck.

Cada municipio lleva su nombre y su valor sobre el polígono, y el mapa lleva
leyenda por clases —no una barra de color continua— porque en una proyección
la lectura es «a qué grupo pertenece», no «qué tono exacto es».

Fondo crema para integrarse con la plantilla de la Gobernación.
"""
import json
import unicodedata

import matplotlib
matplotlib.use("Agg")
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Polygon as MplPoly

CREMA = "#FFF9E9"
AZULT = "#1F3864"
plt.rcParams.update({"font.family": "DejaVu Sans", "figure.dpi": 210,
                     "figure.facecolor": CREMA, "savefig.facecolor": CREMA})

import sys as _sys; from pathlib import Path as _Path
_sys.path.insert(0, str(next(p for p in _Path(__file__).resolve().parents if (p / "rutas.py").is_file())))
from rutas import fuente, GEORIESGO  # rutas relativas del laboratorio (antes /sessions/.../mnt)
OBS = str(GEORIESGO)
geo = json.load(open(f"{OBS}/fuentes/municipios_valle.geojson", encoding="utf-8"))
R = json.load(open("turismo_mun_0903.json", encoding="utf-8"))
MU = pd.DataFrame(R["municipios"])


def norm(s):
    s = unicodedata.normalize("NFD", str(s or "").upper())
    return "".join(c for c in s if unicodedata.category(c) != "Mn").strip()


ALIAS = {"SANTIAGO DE CALI": "CALI", "CALIMA (EL DARIEN)": "CALIMA",
         "GUADALAJARA DE BUGA": "BUGA"}
clave = lambda s: ALIAS.get(norm(s), norm(s))
MU["k"] = MU.municipio.map(clave)
DAT = MU.set_index("k")

mil = lambda x: f"{x:,}".replace(",", ".")
# La figura va dentro del deck, que ya pone título y bajada en la lámina.
TITULOS = False

anillos = lambda g: ([g["coordinates"][0]] if g["type"] == "Polygon"
                     else [p[0] for p in g["coordinates"]])

NOMBRE = {"ALCALA": "Alcalá", "ANDALUCIA": "Andalucía", "BOLIVAR": "Bolívar",
          "CAICEDONIA": "Caicedonia", "EL AGUILA": "El Águila",
          "GUACARI": "Guacarí", "JAMUNDI": "Jamundí", "LA UNION": "La Unión",
          "RIOFRIO": "Riofrío", "TULUA": "Tuluá", "BUGA": "Buga"}


def bonito(k):
    return NOMBRE.get(k, k.title().replace(" De ", " de ").replace(" El ", " el "))


# Municipios pequeños o alargados donde el centroide deja el rótulo encima del
# vecino. Desplazamiento manual, en grados.
NUDGE = {"ULLOA": (0.055, 0.030), "ALCALA": (0.012, -0.030),
         "VERSALLES": (-0.016, 0.024), "CAICEDONIA": (-0.026, 0.016),
         "TULUA": (0.012, -0.012), "TORO": (0.012, 0.006),
         "ANSERMANUEVO": (0.006, 0.012), "LA UNION": (0.004, 0.010),
         "RESTREPO": (-0.016, 0.016), "VIJES": (0.019, 0.004),
         "YUMBO": (-0.006, 0.0), "LA CUMBRE": (-0.036, -0.012),
         "ARGELIA": (0.014, -0.012), "EL CAIRO": (-0.012, 0.010),
         "EL DOVIO": (-0.014, -0.002), "SEVILLA": (0.012, -0.018),
         "ANDALUCIA": (-0.010, -0.004), "BUGALAGRANDE": (0.006, 0.010)}


def centro(f):
    a = max(anillos(f["geometry"]), key=len)
    p = np.array(a)
    k = clave(f["properties"]["nombre"])
    dx, dy = NUDGE.get(k, (0.0, 0.0))
    return p[:, 0].mean() + dx, p[:, 1].mean() + dy


def mapa(col, titulo, bajada, etiqueta, archivo, cortes, colores, fmt="{:.0f}",
         nota="", sin_dato="sin dato", fmtf=None):
    """cortes: límites superiores de cada clase; el último es +inf."""
    fnum = fmtf or (lambda x: fmt.format(x))
    vals = {}
    for f in geo["features"]:
        k = clave(f["properties"]["nombre"])
        vals[k] = float(DAT[col].get(k, np.nan)) if k in DAT.index else np.nan

    def clase(x):
        if x is None or (isinstance(x, float) and np.isnan(x)):
            return None
        for i, c in enumerate(cortes):
            if x <= c:
                return i
        return len(cortes)

    fig, ax = plt.subplots(figsize=(9.6, 6.4))
    for f in geo["features"]:
        k = clave(f["properties"]["nombre"])
        i = clase(vals[k])
        col_f = colores[i] if i is not None else "#e0e0e0"
        for a in anillos(f["geometry"]):
            ax.add_patch(MplPoly(np.array(a), closed=True, facecolor=col_f,
                                 edgecolor="white", linewidth=.75, zorder=2))
    # ── rótulos: los 42 municipios, con su nombre y su valor ──
    for f in geo["features"]:
        k = clave(f["properties"]["nombre"])
        cx, cy = centro(f)
        x = vals[k]
        i = clase(x)
        et = bonito(k)
        txt = f"{et}\n{fnum(x)}" if i is not None else f"{et}\n—"
        # El texto va blanco sobre los tonos oscuros y oscuro sobre los claros,
        # con un contorno del color contrario para que se lea sobre la frontera.
        oscuro = i is not None and i >= len(colores) - 2
        ax.annotate(txt, (cx, cy), fontsize=7.4, ha="center", va="center",
                    color="white" if oscuro else "#12100e", linespacing=1.15,
                    zorder=5, path_effects=[pe.withStroke(
                        linewidth=1.9,
                        foreground="#3a0d0a" if oscuro else "white")])
    ax.autoscale_view()
    ax.set_aspect("equal")
    ax.axis("off")

    ets = ["hasta " + fnum(cortes[0])]
    for i in range(1, len(cortes)):
        ets.append(fnum(cortes[i - 1]) + " – " + fnum(cortes[i]))
    ets.append("más de " + fnum(cortes[-1]))
    marcas = [Line2D([0], [0], marker="s", color="none", markerfacecolor=colores[i],
                     markeredgecolor="white", markersize=13, label=ets[i])
              for i in range(len(colores))]
    # Si algún municipio quedó gris hay que decir por qué, o el gris se lee
    # como «cero» y no como «no se puede calcular».
    if any(clase(v) is None for v in vals.values()):
        marcas.append(Line2D([0], [0], marker="s", color="none",
                             markerfacecolor="#e0e0e0", markeredgecolor="white",
                             markersize=13, label=sin_dato))
    leg = ax.legend(handles=marcas, title=etiqueta, loc="upper left",
                    bbox_to_anchor=(-0.02, 0.99), fontsize=11, title_fontsize=11.6,
                    frameon=True, facecolor="white", edgecolor="#d8d0b8",
                    borderpad=.7, labelspacing=.55)
    leg.get_title().set_color(AZULT)
    leg.get_title().set_fontweight("bold")
    leg.get_frame().set_alpha(.94)

    if TITULOS:
        ax.set_title(titulo + "\n", fontsize=13, fontweight="bold", loc="left",
                     color=AZULT, pad=20)
        ax.text(0, 1.022, bajada, transform=ax.transAxes, fontsize=9.2,
                color="#5a5a5a", va="bottom")
        if nota:
            ax.text(0, -0.008, nota, transform=ax.transAxes, fontsize=7.8,
                    color="#6a6a6a", va="top")
    plt.tight_layout()
    plt.savefig(archivo, bbox_inches="tight", facecolor=CREMA)
    plt.close()
    print("  ", archivo)


ROJOS = ["#fde8d5", "#fbc79b", "#f39a5c", "#dd6031", "#b3261e", "#7a1410"]
MORAS = ["#f2e9f7", "#dcc4ec", "#bf95dc", "#9b64c7", "#7439a8", "#4c1d75"]
NARAN = ["#fff3d6", "#fbdc9a", "#f4bb5c", "#e0902c", "#b96b12", "#8a4a06"]

print("mapas del turismo:")
mapa("n", "Negocios turísticos afectados por municipio",
     f"{len(MU)} municipios · {mil(R['turismo']['n'])} establecimientos de "
     f"alojamiento, comida y transporte",
     "Establecimientos\nque reportaron daño", "mt1_afectados.png",
     [5, 15, 30, 60, 120], ROJOS,
     nota="Cada municipio muestra su nombre y su número de reportes. "
          "Geometría: Marco Geoestadístico Nacional (DANE).")

mapa("reportes_x100_rnt",
     "Peso del daño turístico frente al tamaño de la oferta formal",
     "Reportes turísticos por cada 100 prestadores con RNT vigente",
     "Reportes por cada\n100 inscritos en el RNT", "mt2_intensidad.png",
     [15, 30, 50, 80, 120], MORAS, sin_dato="sin prestadores inscritos",
     nota="No es el porcentaje del RNT afectado: el censo incluye negocios sin RNT y "
          "el registro incluye viviendas turísticas que casi nunca reportan. "
          "Sirve para comparar municipios entre sí.")

mapa("pct_sev", "Severidad declarada por el sector turístico",
     "Porcentaje de los negocios turísticos del municipio en nivel crítico o grave",
     "% crítico o grave", "mt3_severidad.png",
     [30, 45, 60, 70, 80], NARAN, fmt="{:.0f}",
     nota="Calculado sobre los reportes turísticos de cada municipio. "
          "En municipios con pocos reportes el porcentaje es poco estable.")

mapa("rnt_vigentes", "Dónde está la oferta turística formal del Valle",
     f"{mil(R['rnt']['vigentes'])} prestadores con RNT vigente 2026",
     "Prestadores con\nRNT vigente", "mt4_oferta.png",
     [25, 50, 100, 200, 400], ROJOS,
     nota="Registro Nacional de Turismo, corte 2026. El RNT se renueva cada año.")

VERDES = ["#e8f1e6", "#c3ddbd", "#93c391", "#5fa267", "#2f7d47", "#12522c"]
PESOS = ["#fbe9e7", "#f6c4b8", "#ea9077", "#d45c43", "#ad2f1e", "#7a1410"]
mapa("perd_min", "Pérdidas estimadas por municipio",
     f"Cota inferior declarada por la cadena turística · ${mil(R['turismo']['perd_min'])} "
     f"millones en el departamento",
     "Pérdidas declaradas\n(millones de pesos)", "mt5_perdidas.png",
     [25, 100, 250, 600, 1500], PESOS,
     fmtf=lambda x: "$" + mil(int(round(x))),
     sin_dato="sin reportes con dato de pérdidas",
     nota="Cota inferior: suma del piso de cada rango declarado más $100 millones por "
          "cada reporte del tramo abierto. El daño real es mayor.")
