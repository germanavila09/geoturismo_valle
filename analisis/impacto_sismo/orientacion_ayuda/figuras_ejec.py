"""Tres figuras para el informe ejecutivo. Ni una mas: el limite son 10 paginas."""
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from fuentes_oficiales import AYUDA_KPI

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#8a8a8a", "figure.dpi": 205,
                     "ytick.color": "#1a1a1a", "xtick.color": "#4a4a4a"})
ROJO, NAR, AMA, VER, AZU, GRIS = "#b3261e", "#d97706", "#eab308", "#4a9c5d", "#1f6feb", "#9aa0a6"
AZULT = "#1F3864"
D = pd.read_csv("brecha_municipal.csv")
B = json.load(open("brecha.json", encoding="utf-8"))

# etiquetado sin solapes (misma tecnica del informe extenso)
DIRS = [(6, 3), (6, -9), (-6, 3), (-6, -9), (6, 11), (-6, 11), (6, -17), (-6, -17),
        (0, 13), (0, -19), (14, 3), (-14, 3)]


def etiquetar(ax, filas, cx, cy, fs=6.9, todos=None, col="#2a2a2a"):
    ax.figure.canvas.draw()
    inv, k = ax.transData.transform, ax.figure.dpi / 72.0
    bb, puestas = ax.get_window_extent(), []
    if todos is not None:
        for _, r in todos.dropna(subset=[cx, cy]).iterrows():
            qx, qy = inv((r[cx], r[cy]))
            puestas.append((qx - 3 * k, qy - 3 * k, qx + 3 * k, qy + 3 * k))
    for _, r in filas.iterrows():
        t = r.municipio
        px, py = inv((r[cx], r[cy]))
        an = (fs * .60 * len(t) + 3) * k, fs * 1.5 * k
        for dx, dy in DIRS:
            x0 = px + dx * k if dx >= 0 else px + dx * k - an[0]
            c = (x0, py + dy * k, x0 + an[0], py + dy * k + an[1])
            if c[0] < bb.x0 or c[2] > bb.x1 + 24 or c[1] < bb.y0 or c[3] > bb.y1 + 12:
                continue
            if any(not (c[2] < p[0] or c[0] > p[2] or c[3] < p[1] or c[1] > p[3])
                   for p in puestas):
                continue
            ax.annotate(t, (r[cx], r[cy]), fontsize=fs, xytext=(dx, dy),
                        textcoords="offset points", color=col,
                        ha="left" if dx >= 0 else "right",
                        arrowprops=dict(arrowstyle="-", lw=.5, color="#9aa0a6",
                                        shrinkA=1, shrinkB=3)
                        if (abs(dx) > 9 or abs(dy) > 13) else None)
            puestas.append(c)
            break


# ══ E1 · matriz necesidad / ayuda ════════════════════════════════════════
fig, ax = plt.subplots(figsize=(7.9, 5.2))
mi, ma = D.r_nec.median(), D.r_ayuda.median()
# Solo se sombrea el cuadrante que exige decision.
ax.add_patch(plt.Rectangle((0, ma), mi, 43 - ma, color="#fdeeec", zorder=0))
col = np.where(D.cuadrante.str.startswith("1"), ROJO,
               np.where(D.cuadrante.str.startswith("2"), NAR, GRIS))
tam = 30 + 190 * D.poblacion_afectada / D.poblacion_afectada.max()
ax.scatter(D.r_nec, D.r_ayuda, s=tam, c=col, alpha=.85, edgecolors="white",
           linewidths=.8, zorder=3)
ax.axvline(mi, color="#b0b0b0", lw=1, ls="--", zorder=1)
ax.axhline(ma, color="#b0b0b0", lw=1, ls="--", zorder=1)
ax.plot([0, 42], [0, 42], color="#c8c8c8", lw=1, zorder=1)
ax.set_xlim(0, 44)
ax.set_ylim(45, -1)
# Se rotulan solo los municipios sobre los que hay algo que decidir.
sel = D[D.cuadrante.str.startswith("1") | (D.brecha.abs() >= 10) |
        (D.r_nec <= 4) | (D.poblacion_afectada > 8000)]
etiquetar(ax, sel.sort_values("poblacion_afectada", ascending=False),
          "r_nec", "r_ayuda", todos=D)
ax.set_xlabel("Puesto por necesidad (criticidad GRD + afectación económica)  →  menos necesidad",
              fontsize=8.2)
ax.set_ylabel("Puesto por ayuda recibida\n↓ menos toneladas", fontsize=8.2)
ax.text(1.2, 44, "1 · NECESIDAD ALTA, AYUDA BAJA", fontsize=7.8, color=ROJO,
        fontweight="bold", va="bottom")
ax.text(1.2, -.4, "2 · necesidad alta, ayuda alta", fontsize=7.6, color="#8a6a2a", va="top")
ax.text(43, -.4, "3 · necesidad baja, ayuda alta", fontsize=7.6, color=GRIS,
        va="top", ha="right")
ax.text(43, 44, "4 · necesidad baja, ayuda baja", fontsize=7.6, color=GRIS,
        va="bottom", ha="right")
ax.set_title("Dónde no coinciden la necesidad y la ayuda entregada\n",
             fontsize=10.6, fontweight="bold", loc="left", color=AZULT, pad=16)
ax.text(0, 1.028, "El tamaño del punto es la población afectada. Sobre la diagonal, "
        "cada municipio recibe según su necesidad.",
        transform=ax.transAxes, fontsize=7.7, color="#5a5a5a", va="bottom")
plt.tight_layout()
plt.savefig("e1_matriz.png", bbox_inches="tight")
plt.close()

# ══ E2 · intensidad: kilos por persona afectada ══════════════════════════
fig, ax = plt.subplots(figsize=(7.6, 3.5))
t = D.dropna(subset=["kg_por_afectado"]).nsmallest(13, "kg_por_afectado").iloc[::-1]
c = [ROJO if v < 2 else NAR if v < 3.5 else AZU for v in t.kg_por_afectado]
ax.barh(range(len(t)), t.kg_por_afectado, color=c, height=.68)
for i, r in enumerate(t.itertuples()):
    # El punto de miles y la coma decimal se arman por separado: aplicar un
    # replace global sobre la cadena completa deshace el decimal.
    kg = f"{r.kg_por_afectado:.1f}".replace(".", ",")
    afe = f"{r.poblacion_afectada:,.0f}".replace(",", ".")
    ax.text(r.kg_por_afectado + .15, i,
            f"{kg} kg   ·   {r.toneladas:.0f} t para {afe} afectados",
            va="center", fontsize=6.9, color="#3a3a3a")
ax.axvline(D.kg_por_afectado.median(), color="#1a1a1a", ls="--", lw=1.1)
ax.text(D.kg_por_afectado.median() + .12, -.75,
        f"mediana departamental {D.kg_por_afectado.median():.1f} kg".replace(".", ","),
        fontsize=7.4, color="#1a1a1a", va="center")
ax.set_yticks(range(len(t)))
ax.set_yticklabels(t.municipio, fontsize=7.6)
ax.set_xlim(0, 9.6)
ax.set_ylim(-1.4, len(t) - .3)
ax.set_xlabel("Kilogramos de ayuda por persona afectada declarada", fontsize=8.2)
ax.set_title("Los trece municipios con menos ayuda por persona afectada\n",
             fontsize=10.6, fontweight="bold", loc="left", color=AZULT, pad=14)
ax.text(0, 1.035, "Corte de ayuda: 27 de agosto. Población afectada: matriz GRD "
        "al 2 de septiembre. En rojo, por debajo de 2 kg.",
        transform=ax.transAxes, fontsize=7.6, color="#5a5a5a", va="bottom")
plt.tight_layout()
plt.savefig("e2_intensidad.png", bbox_inches="tight")
plt.close()

# ══ E3 · lo que se entrega frente a lo que se pide ═══════════════════════
fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.8, 3.4))

comp = AYUDA_KPI["composicion"]
GRUPO = {"Aseo personal": "Subsistencia inmediata", "Alimentos": "Subsistencia inmediata",
         "Líquidos e hidratación": "Subsistencia inmediata", "Bebé": "Subsistencia inmediata",
         "Aseo del hogar": "Subsistencia inmediata", "Salud": "Subsistencia inmediata",
         "Protección y seguridad": "Habitabilidad", "Descanso y abrigo": "Habitabilidad",
         "Menaje y utensilios": "Habitabilidad", "Ropa y calzado": "Habitabilidad",
         "Herramientas y materiales": "Recuperación productiva"}
g = {}
for k, v in comp.items():
    g[GRUPO.get(k, "Otros / sin desagregar")] = g.get(GRUPO.get(k, "Otros / sin desagregar"), 0) + v
orden = ["Subsistencia inmediata", "Habitabilidad", "Otros / sin desagregar",
         "Recuperación productiva"]
vals = [g[k] for k in orden]
cols = [AZU, "#5b8def", GRIS, ROJO]
a1.barh(range(len(orden))[::-1], vals, color=cols, height=.6)
for i, (k, v) in enumerate(zip(orden, vals)):
    # int(v + .5) y no format: Python redondea 70,5 a 70 (banquero) y el
    # informe cita 71 en el texto.
    a1.text(v + 1.4, len(orden) - 1 - i, "< 1 %" if v < 1 else f"{int(v + .5)} %",
            va="center", fontsize=8, color="#2a2a2a", fontweight="bold")
a1.set_yticks(range(len(orden))[::-1])
a1.set_yticklabels([k.replace(" ", "\n", 1) for k in orden], fontsize=7.6)
a1.set_xlim(0, 88)
a1.set_xticks([])
a1.spines["bottom"].set_visible(False)
a1.set_title("Lo que se ha entregado\n434 despachos · 561 toneladas · corte 27 ago",
             fontsize=8.8, fontweight="bold", loc="left", color=AZULT)

NEC = [("Capital de trabajo\no insumos", 45.4, ROJO),
       ("Reparar instalaciones\no equipos", 43.5, ROJO),
       ("Recuperar clientes\ny ventas", 22.5, NAR),
       ("Facilitar trámites", 7.2, GRIS),
       ("Restablecer servicios\no logística", 4.2, GRIS)]
a2.barh(range(len(NEC))[::-1], [v for _, v, _ in NEC],
        color=[c for _, _, c in NEC], height=.6)
for i, (k, v, _) in enumerate(NEC):
    a2.text(v + .9, len(NEC) - 1 - i, f"{v:.1f} %".replace(".", ","), va="center",
            fontsize=8, color="#2a2a2a", fontweight="bold")
a2.set_yticks(range(len(NEC))[::-1])
a2.set_yticklabels([k for k, _, _ in NEC], fontsize=7.6)
a2.set_xlim(0, 58)
a2.set_xticks([])
a2.spines["bottom"].set_visible(False)
a2.set_title("Lo que piden los establecimientos\n12.942 responden · corte 1 sep",
             fontsize=8.8, fontweight="bold", loc="left", color=AZULT)
fig.suptitle("La ayuda que sale y la necesidad que se declara no se cruzan",
             fontsize=10.6, fontweight="bold", color=AZULT, x=.006, ha="left", y=1.11)
fig.text(.006, 1.035, "Menos del 1 % de lo despachado son herramientas y materiales, "
         "mientras el 75,7 % de los establecimientos pide capital, reparación o ambos.",
         fontsize=7.6, color="#5a5a5a")
plt.tight_layout()
plt.savefig("e3_brecha_tipo.png", bbox_inches="tight")
plt.close()

print("e1, e2 y e3 listas")
