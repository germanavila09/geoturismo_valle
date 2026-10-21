"""Histogramas, dispersiones y rankings por indicador."""
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

M = pd.read_csv("indice_municipal.csv")
R = json.load(open("descriptivo.json", encoding="utf-8"))
DUP = json.load(open("duplicados.json", encoding="utf-8"))
est = pd.read_pickle("dedup.pkl")

IND = [("pct_severo", "Afectación crítica o grave", ROJO),
       ("pct_no_opera", "No puede operar", NAR),
       ("pct_perd_alta", "Pérdidas > $20 millones", "#8b5cf6"),
       ("pct_empleo", "Con algún empleo en riesgo", AZU)]

# ── F1 · histogramas de los cuatro indicadores ────────────────────────────
fig, axes = plt.subplots(2, 2, figsize=(7.6, 4.6))
for ax, (c, et, col) in zip(axes.ravel(), IND):
    s = M[c].dropna()
    ax.hist(s, bins=9, color=col, alpha=.82, edgecolor="white", linewidth=.9)
    ax.axvline(s.median(), color="#1a1a1a", ls="--", lw=1.2)
    ax.text(s.median(), ax.get_ylim()[1] * .93, f" mediana {s.median():.0f} %",
            fontsize=7.4, color="#1a1a1a")
    ax.set_title(f"{et}\nrango {s.min():.0f}–{s.max():.0f} % · CV {s.std()/s.mean():.2f}",
                 fontsize=8.4, fontweight="bold", loc="left", color=AZULT)
    ax.set_xlabel("% de establecimientos del municipio", fontsize=7.6)
    ax.set_ylabel("municipios", fontsize=7.6)
fig.suptitle("Cómo se reparte cada indicador entre los 42 municipios",
             fontsize=10.5, fontweight="bold", color=AZULT, x=.008, ha="left", y=1.005)
plt.tight_layout()
plt.savefig("f1_histogramas.png", bbox_inches="tight")
plt.close()

# ── etiquetado sin solapes ───────────────────────────────────────────────
# Un municipio etiquetado encima de otro no informa: se prueban ocho
# posiciones alrededor del punto y se toma la primera que no choque con
# ninguna etiqueta ya colocada. Si las ocho chocan, se omite la etiqueta.
DIRS = [(6, 3), (6, -9), (-6, 3), (-6, -9), (6, 11), (-6, 11), (6, -17), (-6, -17),
        (0, 13), (0, -19), (14, 3), (-14, 3)]
OMITIDAS = []
# Nombres largos que no caben en el margen; se usa la forma de uso corriente.
CORTO = {"GUADALAJARA DE BUGA": "Buga", "SANTIAGO DE CALI": "Cali",
         "VIJES": "Vijes", "SAN PEDRO": "San Pedro"}
corto = lambda m: CORTO.get(m.upper(), m.title())


def etiquetar(ax, filas, cx, cy, fs=6.8, todos=None):
    ax.figure.canvas.draw()
    inv = ax.transData.transform
    # transData da pixeles; los desplazamientos de annotate van en puntos.
    # Sin este factor las cajas se comparan en unidades distintas y el test
    # de choque no detecta nada.
    k = ax.figure.dpi / 72.0
    bb = ax.get_window_extent()
    puestas = []
    if todos is not None:   # los propios puntos tambien ocupan espacio
        for _, r in todos.dropna(subset=[cx, cy]).iterrows():
            qx, qy = inv((r[cx], r[cy]))
            puestas.append((qx - 3 * k, qy - 3 * k, qx + 3 * k, qy + 3 * k))
    for _, r in filas.iterrows():
        txt = corto(r.municipio)
        px, py = inv((r[cx], r[cy]))
        an = (fs * .60 * len(txt) + 3) * k, fs * 1.5 * k
        for dx, dy in DIRS:
            x0 = px + dx * k if dx >= 0 else px + dx * k - an[0]
            caja = (x0, py + dy * k, x0 + an[0], py + dy * k + an[1])
            # A la izquierda esta el eje Y: invadirlo hace la etiqueta ilegible.
            # Hacia la derecha y arriba hay margen de figura, se tolera algo.
            if (caja[0] < bb.x0 or caja[2] > bb.x1 + 70 * k / 2.85
                    or caja[1] < bb.y0 or caja[3] > bb.y1 + 12):
                continue
            choca = any(not (caja[2] < c[0] or caja[0] > c[2] or
                             caja[3] < c[1] or caja[1] > c[3]) for c in puestas)
            if not choca:
                lejos = abs(dx) > 9 or abs(dy) > 13
                ax.annotate(txt, (r[cx], r[cy]), fontsize=fs, xytext=(dx, dy),
                            textcoords="offset points", color="#2a2a2a",
                            ha="left" if dx >= 0 else "right",
                            arrowprops=dict(arrowstyle="-", lw=.5, color="#9aa0a6",
                                            shrinkA=1, shrinkB=3) if lejos else None)
                puestas.append(caja)
                break
        else:
            OMITIDAS.append(txt)


# ── F2 · dispersiones clave, con nombre de municipio ─────────────────────
def disp(ax, cx, cy, ex, ey):
    d = M.dropna(subset=[cx, cy]).copy()
    tam = 16 + 58 * (d.n - d.n.min()) / (d.n.max() - d.n.min())
    ax.scatter(d[cx], d[cy], s=tam, c=d.IAE_aj, cmap="YlOrRd",
               edgecolors="white", linewidths=.7, zorder=3, vmin=0, vmax=100)
    ax.margins(x=.19, y=.13)
    mx, my = d[cx].median(), d[cy].median()
    ax.axvline(mx, color="#c8c8c8", lw=.9, zorder=1)
    ax.axhline(my, color="#c8c8c8", lw=.9, zorder=1)
    ax.set_xlabel(ex, fontsize=8)
    ax.set_ylabel(ey, fontsize=8)
    # Se nombran los extremos de cada eje y los municipios que rompen la
    # relacion (los que mas discrepan entre un rango y el otro).
    d["_disc"] = (d[cx].rank() - d[cy].rank()).abs()
    sel = pd.concat([d.nlargest(1, "n"), d.nlargest(4, cx), d.nlargest(4, cy),
                     d.nsmallest(2, cx), d.nsmallest(2, cy),
                     d.nlargest(4, "_disc")]).drop_duplicates("municipio")
    etiquetar(ax, sel.sort_values("n", ascending=False), cx, cy, todos=d)
    rho = d[[cx, cy]].corr(method="spearman").iloc[0, 1]
    ax.text(.98, .04, f"ρ de Spearman = {rho:.2f}".replace(".", ","),
            transform=ax.transAxes, ha="right", fontsize=7.6, color="#3a3a3a")

fig, axes = plt.subplots(1, 2, figsize=(7.8, 3.5))
disp(axes[0], "pct_severo", "pct_perd_alta",
     "% crítico o grave", "% con pérdidas > $20M")
axes[0].set_title("Severidad y pérdidas van juntas", fontsize=9.2,
                  fontweight="bold", loc="left", color=AZULT)
disp(axes[1], "pct_no_opera", "pct_perd_alta",
     "% que no puede operar", "% con pérdidas > $20M")
axes[1].set_title("Parálisis y pérdidas, en cambio, no", fontsize=9.2,
                  fontweight="bold", loc="left", color=AZULT)
plt.tight_layout()
plt.savefig("f2_dispersion.png", bbox_inches="tight")
plt.close()

# ── F3 · cobertura frente a intensidad ───────────────────────────────────
fig, ax = plt.subplots(figsize=(7.4, 4.0))
ax.scatter(M.n, M.pct_severo, s=42 + 78 * M.IAE_aj / 100, c=M.IAE_aj,
           cmap="YlOrRd", edgecolors="white", linewidths=.7, vmin=0, vmax=100, zorder=3)
ax.set_xscale("log")
ax.margins(x=.09, y=.10)
ax.axhline(M.pct_severo.median(), color="#c8c8c8", lw=1)
ax.set_xlabel("Establecimientos que reportaron en el municipio (escala logarítmica)")
ax.set_ylabel("% en afectación\ncrítica o grave")
etiquetar(ax, M[(M.n > 200) | (M.pct_severo > 62) | (M.pct_severo < 25)]
          .sort_values("n", ascending=False), "n", "pct_severo", fs=6.9, todos=M)
ax.text(.99, .03, f"ρ = {M[['n','pct_severo']].corr(method='spearman').iloc[0,1]:.2f}".replace(".", ","),
        transform=ax.transAxes, ha="right", fontsize=8, color="#3a3a3a")
ax.set_title("El volumen de reportes apenas anticipa la intensidad de la afectación",
             fontsize=10, fontweight="bold", loc="left", color=AZULT, pad=10)
plt.tight_layout()
plt.savefig("f3_cobertura.png", bbox_inches="tight")
plt.close()

# ── F4 · rankings por indicador ──────────────────────────────────────────
fig, axes = plt.subplots(1, 4, figsize=(9.8, 4.6))
for ax, (c, et, col) in zip(axes, IND):
    t = M.dropna(subset=[c]).nlargest(12, c).iloc[::-1]
    # Un porcentaje sobre 40 reportes no pesa lo mismo que sobre 6.000: las
    # barras con base menor de 60 van atenuadas y llevan su n al lado.
    # Cada indicador tiene su propia base: no todos los reportes respondieron
    # a todas las preguntas.
    base = t[{"pct_severo": "n", "pct_no_opera": "base_cont",
              "pct_perd_alta": "base_perd", "pct_empleo": "base_empl"}[c]]
    ax.barh(range(len(t)), t[c], height=.7,
            color=[col if b >= 60 else "#dedede" for b in base],
            edgecolor=[col] * len(t), linewidth=.9, alpha=.9)
    for i, (v, b) in enumerate(zip(t[c], base)):
        ax.text(v + max(t[c]) * .03, i, f"{v:.0f}  n={b}", va="center",
                fontsize=6.8, color="#3a3a3a")
    ax.set_yticks(range(len(t)))
    ax.set_yticklabels([corto(m) for m in t.municipio], fontsize=7.2)
    ax.set_xlim(0, max(t[c]) * 1.34)
    ax.set_xticks([])
    ax.spines["bottom"].set_visible(False)
    ax.set_title(et, fontsize=8.4, fontweight="bold", loc="left", color=AZULT)
fig.suptitle("Doce primeros municipios en cada indicador  ·  el orden cambia según lo que se mida",
             fontsize=10, fontweight="bold", color=AZULT, x=.008, ha="left", y=1.045)
fig.text(.008, .995, "barra gris: menos de 60 respuestas a esa pregunta en el municipio; "
         "el porcentaje es poco estable  ·  n = respuestas válidas",
         fontsize=7.4, color="#5a5a5a")
plt.tight_layout()
plt.savefig("f4_rankings.png", bbox_inches="tight")
plt.close()

# ── F5 · correlaciones ───────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(4.6, 3.9))
cols = [c for c, _, _ in IND]
et = ["Crítico o\ngrave", "No puede\noperar", "Pérdidas\n> $20M", "Empleo en\nriesgo"]
cor = M[cols].corr(method="spearman")
im = ax.imshow(cor, cmap="RdYlBu_r", vmin=0, vmax=1)
for i in range(len(cols)):
    for j in range(len(cols)):
        ax.text(j, i, f"{cor.iloc[i,j]:.2f}".replace(".", ","), ha="center", va="center",
                fontsize=9, fontweight="bold" if i != j else "normal",
                color="white" if cor.iloc[i, j] > .62 else "#1a1a1a")
ax.set_xticks(range(len(cols)))
ax.set_xticklabels(et, fontsize=7.4)
ax.set_yticks(range(len(cols)))
ax.set_yticklabels(et, fontsize=7.4)
ax.set_title("Correlación de Spearman entre indicadores",
             fontsize=9.4, fontweight="bold", loc="left", color=AZULT, pad=10)
plt.colorbar(im, ax=ax, fraction=.045, pad=.03).ax.tick_params(labelsize=7)
plt.tight_layout()
plt.savefig("f5_correlacion.png", bbox_inches="tight")
plt.close()

# ── F6 · duplicidad ──────────────────────────────────────────────────────
fig, (a1, a2, a3) = plt.subplots(1, 3, figsize=(9.6, 3.0))

# Las senales se solapan (un mismo par puede compartir telefono y correo), asi
# que la suma por senal excede el total depurado. Se dice explicitamente.
s = DUP["senales"]
k = list(s.keys())[::-1]
a1.barh(range(len(k)), [s[x]["registros_extra"] for x in k], color=AZU, height=.6)
for i, x in enumerate(k):
    v, d = s[x]["registros_extra"], s[x]["grupos_descartados"]
    a1.text(v + 12, i, f"{v}" + (f"   ({d} grupos de gestor descartados)" if d else ""),
            va="center", fontsize=6.8, color="#3a3a3a")
a1.set_yticks(range(len(k)))
a1.set_yticklabels(k, fontsize=7.6)
a1.set_xlim(0, 700)
a1.set_xticks([])
a1.spines["bottom"].set_visible(False)
a1.set_title(f"Detectados por cada señal\n(se solapan; únicos: {DUP['extras']})",
             fontsize=8.6, fontweight="bold", loc="left", color=AZULT)

t = DUP["tam_grupos"]
a2.bar([str(x) for x in t], list(t.values()), color=ROJO, width=.55)
for i, (x, v) in enumerate(t.items()):
    a2.text(i, v + max(t.values()) * .04, str(v), ha="center", fontsize=7.8)
a2.set_xlabel("reportes del mismo establecimiento", fontsize=7.8)
a2.set_ylabel("grupos", fontsize=7.8)
a2.set_ylim(0, max(t.values()) * 1.22)
a2.set_title(f"Tamaño de los grupos\n{DUP['n_grupos_dup']} grupos, ninguno mayor "
             f"de {DUP['max_grupo']}", fontsize=8.6, fontweight="bold",
             loc="left", color=AZULT)

MET = [("pct_severo", "crítico\no grave"), ("pct_no_opera", "no puede\noperar"),
       ("pct_no_normal", "no opera con\nnormalidad"), ("pct_perd_alta", "pérdidas\n> $20M")]
x = np.arange(len(MET))
a3.bar(x - .19, [DUP["antes"][c] for c, _ in MET], .36, color=GRIS, label="sin depurar")
a3.bar(x + .19, [DUP["despues"][c] for c, _ in MET], .36, color=ROJO, label="depurado")
for i, (c, _) in enumerate(MET):
    d = DUP["despues"][c] - DUP["antes"][c]
    a3.text(i, max(DUP["antes"][c], DUP["despues"][c]) + 2.5, f"{d:+.2f}".replace(".", ","),
            ha="center", fontsize=6.8, color="#b3261e", fontweight="bold")
a3.set_xticks(x)
a3.set_xticklabels([e for _, e in MET], fontsize=6.8)
a3.set_ylabel("% de establecimientos", fontsize=7.8)
a3.set_ylim(0, 88)
a3.legend(fontsize=6.8, frameon=False, loc="upper left")
a3.set_title("Efecto sobre los indicadores\ndepartamentales (puntos porcentuales)",
             fontsize=8.6, fontweight="bold", loc="left", color=AZULT)
plt.tight_layout()
plt.savefig("f6_duplicados.png", bbox_inches="tight")
plt.close()

print("figuras f1-f6 listas")
print(f"etiquetas omitidas por falta de espacio: {len(OMITIDAS)} {OMITIDAS}")
