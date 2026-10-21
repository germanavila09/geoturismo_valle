import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np, pandas as pd, json
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":9,
    "axes.spines.top":False,"axes.spines.right":False,"axes.edgecolor":"#8a8a8a",
    "figure.dpi":205,"ytick.color":"#1a1a1a","xtick.color":"#4a4a4a"})
ROJO,NAR,AMA,VER,AZU,GRIS="#b3261e","#d97706","#eab308","#4a9c5d","#1f6feb","#9aa0a6"
est=pd.read_pickle("est.pkl"); M=pd.read_csv("indice_municipal.csv")
R=json.load(open("geo_resultados.json",encoding="utf-8"))
N=len(est)

# ── G1 · las cuatro variables ordinales, en un solo panel ──
fig,axes=plt.subplots(2,2,figsize=(7.6,5.0))
def barras(ax,col,orden,colores,titulo,fmt="{:.0f}%"):
    s=est[col].dropna(); v=[100*(s==o).mean() for o in orden]
    et=[o.replace("Sí, ","").replace(".","").replace(" millones","M")[:22] for o in orden]
    b=ax.barh(range(len(orden))[::-1],v,color=colores,height=.62)
    for r,x,n in zip(b,v,[int((s==o).sum()) for o in orden]):
        ax.text(x+1,r.get_y()+r.get_height()/2,f"{x:.1f}%  ({n:,})".replace(",","."),
                va="center",fontsize=7.6,color="#3a3a3a")
    ax.set_yticks(range(len(orden))[::-1]); ax.set_yticklabels(et,fontsize=7.8)
    ax.set_xlim(0,max(v)*1.42); ax.set_xticks([])
    ax.spines["bottom"].set_visible(False)
    ax.set_title(f"{titulo}\nbase {len(s):,}".replace(",","."),fontsize=8.6,
                 fontweight="bold",loc="left",color="#1F3864")
barras(axes[0,0],"Nivel de afectación",["Crítica","Grave","Moderada","Baja","Sin clasificación","no_afectado"],
       [ROJO,"#e2574c",NAR,VER,GRIS,"#cfcfcf"],"Nivel de afectación")
barras(axes[0,1],"Continuidad operativa",["No puede operar","Sí, pero parcialmente","Sí, normalmente"],
       [ROJO,NAR,VER],"Continuidad operativa")
barras(axes[1,0],"Pérdidas económicas",["Más de $100 millones.","Más de $20 y hasta $100 millones.",
       "Entre $5 y $20 millones.","Menos de $5 millones."],[ROJO,NAR,AMA,VER],"Pérdidas económicas")
barras(axes[1,1],"Empleos afectados o en riesgo",["Más de 50","Entre 21 y 50","Entre 6 y 20","Entre 1 y 5","Ninguno"],
       [ROJO,"#e2574c",NAR,AMA,VER],"Empleos afectados o en riesgo")
plt.tight_layout(); plt.savefig("g1_variables.png",bbox_inches="tight"); plt.close()

# ── G2 · necesidades y apoyo, departamento vs 10 mas afectados ──
fig,(a1,a2)=plt.subplots(1,2,figsize=(7.6,3.0))
def comp(ax,d1,d2,tit,color1,color2):
    k=list(d1.keys()); y=np.arange(len(k))
    v1=[100*d1[x]/N for x in k]
    n10=int(M[M.municipio.isin(R["top10"])].n.sum())
    v2=[100*d2.get(x,0)/n10 for x in k]
    ax.barh(y+.19,v1,height=.36,color=color1,label="Departamento")
    ax.barh(y-.19,v2,height=.36,color=color2,label="10 más afectados")
    ax.set_yticks(y); ax.set_yticklabels([x[:30] for x in k],fontsize=7.6)
    ax.invert_yaxis(); ax.set_xlabel("% de establecimientos",fontsize=7.8)
    ax.legend(fontsize=7,frameon=False,loc="lower right")
    ax.set_title(tit,fontsize=8.8,fontweight="bold",loc="left",color="#1F3864")
comp(a1,R["nec_dpto"],R["nec_top10"],"Principal necesidad",AZU,ROJO)
comp(a2,R["apo_dpto"],R["apo_top10"],"Apoyo financiero preferido","#5b8def",NAR)
plt.tight_layout(); plt.savefig("g2_necesidades.png",bbox_inches="tight"); plt.close()

# ── G3 · ranking con componentes ──
fig,ax=plt.subplots(figsize=(7.6,4.6))
t=M.nlargest(15,"IAE_aj").iloc[::-1]
y=np.arange(len(t))
ax.barh(y,t.IAE_aj,color=[ROJO if v>=85 else NAR if v>=70 else AMA for v in t.IAE_aj],height=.68)
for i,r in enumerate(t.itertuples()):
    ax.text(r.IAE_aj+1.2,i,f"{r.IAE_aj:.0f}   n={r.n:,}".replace(",","."),
            va="center",fontsize=7.6,color="#3a3a3a")
ax.set_yticks(y); ax.set_yticklabels([m.title() for m in t.municipio],fontsize=8.4)
ax.set_xlim(0,122); ax.set_xlabel("Índice de afectación económica ajustado (0–100)")
ax.set_title("Municipios con mayor afectación económica",fontsize=10,
             fontweight="bold",loc="left",color="#1F3864",pad=10)
plt.tight_layout(); plt.savefig("g3_ranking.png",bbox_inches="tight"); plt.close()

# ── G4 · diagrama de dispersion de Moran ──
fig,ax=plt.subplots(figsize=(5.6,4.4))
ax.axhline(0,color="#bbb",lw=.8); ax.axvline(0,color="#bbb",lw=.8)
COL={"Alto-Alto":ROJO,"Bajo-Bajo":AZU,"Alto-Bajo":NAR,"Bajo-Alto":VER}
for _,r in M.iterrows():
    sig=r.p_local<=0.05
    ax.scatter(r.z,r.rezago,s=52 if sig else 26,
               c=COL.get(r.cluster,GRIS) if sig else "#d5d5d5",
               edgecolors="white",linewidths=.6,zorder=3)
    if sig or abs(r.z)>1.6:
        ax.annotate(r.municipio.title(),(r.z,r.rezago),fontsize=6.6,
                    xytext=(4,3),textcoords="offset points",color="#3a3a3a")
b=np.polyfit(M.z,M.rezago,1)
xs=np.linspace(M.z.min(),M.z.max(),10)
ax.plot(xs,np.polyval(b,xs),color=ROJO,lw=1.4,ls="--",
        label=f"pendiente = I de Moran = {R['moran_ajustado']['I']:.3f}")
ax.set_xlabel("Índice del municipio (estandarizado)")
ax.set_ylabel("Promedio de sus vecinos")
ax.legend(fontsize=7.6,frameon=False,loc="upper left")
ax.set_title("Diagrama de Moran: el índice no se agrupa en el territorio",
             fontsize=9.4,fontweight="bold",loc="left",color="#1F3864",pad=10)
plt.tight_layout(); plt.savefig("g4_moran.png",bbox_inches="tight"); plt.close()

# ── G5 · contraste con fuentes externas ──
fig,ax=plt.subplots(figsize=(7.6,2.9))
cats=["Crítica o grave\n(Cali)","No puede operar\n(Cali)","No opera con\nnormalidad (Valle)",
      "Empleo en riesgo\n(Valle)"]
nuestro=[61.2,28.7,70.8,74.3]
externo=[63.0,39.0,76.2,np.nan]
x=np.arange(len(cats))
ax.bar(x-.19,nuestro,.36,color=AZU,label="Esta base (1 sep · 14.241)")
ax.bar(x+.19,[0 if np.isnan(v) else v for v in externo],.36,color=NAR,
       label="Fuentes externas (ago)")
for i,(a,b_) in enumerate(zip(nuestro,externo)):
    ax.text(i-.19,a+1.4,f"{a:.1f}%",ha="center",fontsize=7.8)
    if not np.isnan(b_): ax.text(i+.19,b_+1.4,f"{b_:.0f}%",ha="center",fontsize=7.8)
    else: ax.text(i+.19,2,"sin dato\ncomparable",ha="center",fontsize=6.6,color=GRIS)
ax.set_xticks(x); ax.set_xticklabels(cats,fontsize=7.8)
ax.set_ylim(0,92); ax.set_ylabel("%"); ax.legend(fontsize=7.4,frameon=False)
ax.set_title("Contraste con la Cámara de Comercio de Cali y la Fundación WWB",
             fontsize=9.6,fontweight="bold",loc="left",color="#1F3864",pad=10)
plt.tight_layout(); plt.savefig("g5_contraste.png",bbox_inches="tight"); plt.close()
print("graficos g1-g5 listos")
