"""Mapas coropleticos con TODOS los municipios rotulados."""
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPoly
from matplotlib.lines import Line2D
import matplotlib.patheffects as pe
import numpy as np, pandas as pd, json, unicodedata
plt.rcParams.update({"font.family":"DejaVu Sans","figure.dpi":210})

import sys as _sys; from pathlib import Path as _Path
_sys.path.insert(0, str(next(p for p in _Path(__file__).resolve().parents if (p / "rutas.py").is_file())))
from rutas import fuente, GEORIESGO  # rutas relativas del laboratorio (antes /sessions/.../mnt)
OBS = str(GEORIESGO)
M=pd.read_csv("indice_municipal.csv")
geo=json.load(open(f"{OBS}/fuentes/municipios_valle.geojson",encoding="utf-8"))
def norm(s):
    s=unicodedata.normalize("NFD",str(s or "").upper())
    return "".join(c for c in s if unicodedata.category(c)!="Mn").strip()
ALIAS={"SANTIAGO DE CALI":"CALI","CALIMA (EL DARIEN)":"CALIMA"}
def anillos(g): return [g["coordinates"][0]] if g["type"]=="Polygon" else [p[0] for p in g["coordinates"]]

def bonito(s):
    s=str(s).lower()
    s=" ".join(w.capitalize() for w in s.split())
    return s.replace(" De "," de ").replace(" Del "," del ")

# Municipios pequenos o alargados donde el centroide deja el rotulo encima del
# vecino o fuera del poligono. Desplazamiento manual en grados.
NUDGE = {"ULLOA":(0.055,0.030), "ALCALA":(0.010,-0.028),
         "VERSALLES":(0.0,0.012), "CAICEDONIA":(-0.030,0.0),
         "TULUA":(0.010,-0.010), "LA UNION":(0.0,0.008),
         "RESTREPO":(-0.012,0.010), "VIJES":(0.004,-0.006),
         "YUMBO":(-0.006,0.0), "LA CUMBRE":(-0.008,0.004)}

def centro(f):
    """Centroide del anillo mayor, que para estas formas cae dentro."""
    a=max(anillos(f["geometry"]), key=len)
    p=np.array(a)
    k=ALIAS.get(norm(f["properties"]["nombre"]),norm(f["properties"]["nombre"]))
    dx,dy=NUDGE.get(k,(0.0,0.0))
    return p[:,0].mean()+dx, p[:,1].mean()+dy

def mapa(col, titulo, subtitulo, etiqueta_barra, archivo, cmap="YlOrRd",
         fmt="{:.0f}", discreto=None):
    vals={}
    for f in geo["features"]:
        k=ALIAS.get(norm(f["properties"]["nombre"]),norm(f["properties"]["nombre"]))
        r=M[M.municipio.map(lambda x: ALIAS.get(norm(x),norm(x)))==k]
        vals[k]=float(r[col].iloc[0]) if len(r) else np.nan

    fig,ax=plt.subplots(figsize=(8.6,10.2))
    v=[x for x in vals.values() if not np.isnan(x)]
    vmin,vmax=min(v),max(v)
    cm=plt.get_cmap(cmap)
    for f in geo["features"]:
        k=ALIAS.get(norm(f["properties"]["nombre"]),norm(f["properties"]["nombre"]))
        x=vals[k]
        if discreto:
            col_f=discreto.get(k,"#e0e0e0")
        else:
            col_f=cm((x-vmin)/(vmax-vmin)*0.86+0.10) if not np.isnan(x) else "#e0e0e0"
        for a in anillos(f["geometry"]):
            ax.add_patch(MplPoly(np.array(a),closed=True,facecolor=col_f,
                                 edgecolor="white",linewidth=.7,zorder=2))
    # ── rotulos: TODOS los municipios, con su valor ──
    puntos=[]
    for f in geo["features"]:
        k=ALIAS.get(norm(f["properties"]["nombre"]),norm(f["properties"]["nombre"]))
        cx,cy=centro(f); puntos.append((cy,cx,k,vals[k]))
    puntos.sort(reverse=True)
    for cy,cx,k,x in puntos:
        et=bonito(k)
        txt=f"{et}\n{fmt.format(x)}" if not np.isnan(x) else et
        # color de letra segun lo oscuro del relleno
        oscuro = (not np.isnan(x)) and ((x-vmin)/(vmax-vmin) > 0.62)
        # Contorno fino del mismo color del fondo: el rotulo se lee sobre
        # cualquier relleno sin recuadro opaco, que taparia el poligono.
        ax.annotate(txt,(cx,cy),fontsize=5.6,ha="center",va="center",
                    color="white" if (oscuro and not discreto) else "#12100e",
                    linespacing=1.15,zorder=5,
                    path_effects=[pe.withStroke(
                        linewidth=1.5,
                        foreground="#3a0d0a" if (oscuro and not discreto) else "white")])
    ax.autoscale_view(); ax.set_aspect("equal"); ax.axis("off")
    if not discreto:
        sm=plt.cm.ScalarMappable(cmap=cm,norm=plt.Normalize(vmin,vmax))
        cb=fig.colorbar(sm,ax=ax,fraction=.028,pad=.01,shrink=.62)
        cb.set_label(etiqueta_barra,fontsize=8.5); cb.ax.tick_params(labelsize=7.5)
    else:
        leyenda=[Line2D([0],[0],marker="s",color="none",markerfacecolor=c,
                        markersize=11,label=l) for l,c in discreto["_leyenda"]]
        ax.legend(handles=leyenda,fontsize=8,frameon=False,loc="lower left",
                  title=etiqueta_barra,title_fontsize=8.5)
    ax.set_title(titulo,fontsize=12.5,fontweight="bold",loc="left",pad=14,color="#1F3864")
    ax.text(0,1.005,subtitulo,transform=ax.transAxes,fontsize=8.6,color="#4a4a4a",va="bottom")
    ax.text(0,-.012,"Cada municipio muestra su nombre y su valor. Geometría: Marco "
                    "Geoestadístico Nacional (DANE).",
            transform=ax.transAxes,fontsize=7,color="#5a5a5a",va="top")
    plt.tight_layout(); plt.savefig(archivo,bbox_inches="tight"); plt.close()
    print("  ",archivo)

mil=lambda x:f"{x:,}".replace(",",".")
SUB=f"42 municipios · {mil(int(M.n.sum()))} establecimientos únicos · corte 1 de septiembre de 2026"

print("mapas:")
mapa("IAE_aj","Índice de afectación económica",SUB,
     "IAE ajustado (0–100)","m1_iae.png")
mapa("pct_no_opera","Establecimientos que no pueden operar",
     "Porcentaje sobre los que informan continuidad operativa",
     "% no puede operar","m2_nopera.png",cmap="OrRd",fmt="{:.0f}%")
mapa("pct_severo","Afectación crítica o grave",
     "Porcentaje de establecimientos en los dos niveles más altos",
     "% crítico o grave","m3_severo.png",cmap="YlOrBr",fmt="{:.0f}%")
mapa("pct_perd_alta","Pérdidas superiores a $20 millones",
     "Porcentaje sobre los que informan pérdidas económicas",
     "% pérdidas altas","m4_perdidas.png",cmap="PuRd",fmt="{:.0f}%")
mapa("pct_empleo","Establecimientos con algún empleo en riesgo",
     "Porcentaje sobre los que informan empleos afectados o en riesgo",
     "% con empleo en riesgo","m5_empleo.png",cmap="Blues",fmt="{:.0f}%")
