"""Analisis geoestadistico de la afectacion empresarial · base completa.

SEIS VARIABLES, NINGUN DATO SENSIBLE
Se usan solo: continuidad operativa, perdidas economicas, empleos en riesgo,
principal necesidad, apoyo financiero y nivel de afectacion. No se toca ni una
columna con nombre, documento, telefono, correo, NIT o direccion.

QUE SE CALCULA
  1. Perfil municipal de las seis variables sobre los 14.241 establecimientos.
  2. Un indice de afectacion economica (IAE) que combina las seis.
  3. Autocorrelacion espacial: I de Moran global y local, con vecindad de
     contiguidad tipo reina sobre los poligonos municipales del DANE.

POR QUE MORAN Y NO SOLO UN RANKING
Un ranking dice quien esta peor; la autocorrelacion dice si lo que esta peor
forma conglomerados en el territorio o esta disperso. Si el dano se agrupa, la
respuesta puede organizarse por corredores; si esta disperso, hay que ir
municipio por municipio. Es una pregunta operativa, no estadistica.
"""
import json, re, unicodedata, warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")

import sys as _sys; from pathlib import Path as _Path
_sys.path.insert(0, str(next(p for p in _Path(__file__).resolve().parents if (p / "rutas.py").is_file())))
from rutas import fuente, GEORIESGO  # rutas relativas del laboratorio (antes /sessions/.../mnt)
OBS = str(GEORIESGO)
est = pd.read_pickle("est.pkl")           # 14.241 establecimientos deduplicados

SENSIBLES = ["Nombre completo","Documento de identificación","Teléfono de contacto",
             "Correo electrónico de contacto","Empresa","NIT","Dirección","Barrio"]
VARS = ["Continuidad operativa","Pérdidas económicas","Empleos afectados o en riesgo",
        "Principal necesidad","Apoyo financiero","Nivel de afectación"]

# ── escalas ordinales: cada respuesta vale entre 0 y 1 ─────────────────────
SEV  = {"Crítica":1.0,"Grave":0.75,"Moderada":0.40,"Baja":0.15,"no_afectado":0.0}
CONT = {"No puede operar":1.0,"Sí, pero parcialmente":0.5,"Sí, normalmente":0.0}
PERD = {"Más de $100 millones.":1.0,"Más de $20 y hasta $100 millones.":0.66,
        "Entre $5 y $20 millones.":0.33,"Menos de $5 millones.":0.10}
EMPL = {"Más de 50":1.0,"Entre 21 y 50":0.75,"Entre 6 y 20":0.5,
        "Entre 1 y 5":0.25,"Ninguno":0.0}

def norm(s):
    s = unicodedata.normalize("NFD", str(s or "").upper())
    return "".join(c for c in s if unicodedata.category(c) != "Mn").strip()

def multi(serie, canon):
    """Cuenta opciones de seleccion multiple, consolidando las «Otra» que
    repiten una opcion del formulario."""
    c = {}
    for v in serie.dropna():
        for p in re.split(r"[;\n]", str(v)):
            p = p.strip(" .")
            if not p: continue
            b = str(p).replace("�","n")
            b = unicodedata.normalize("NFD", b)
            b = "".join(x for x in b if unicodedata.category(x)!="Mn").lower().strip(" .")
            if b.startswith(("otra","otro")):
                b = re.sub(r"^otr[ao],?\s*.cu[aá]l.?:?\s*","",p,flags=re.I)
                b = unicodedata.normalize("NFD", b.replace("�","n"))
                b = "".join(x for x in b if unicodedata.category(x)!="Mn").lower().strip(" .")
            if b in canon: c[canon[b]] = c.get(canon[b],0)+1
    return dict(sorted(c.items(), key=lambda x:-x[1]))

NEC = {"reparar instalaciones, maquinaria o equipos":"Reparar instalaciones o equipos",
       "contar con capital de trabajo, inventarios o insumos":"Capital de trabajo o insumos",
       "recuperar clientes y ventas":"Recuperar clientes y ventas",
       "facilitar tramites":"Facilitar trámites",
       "restablecer servicios publicos o logistica":"Restablecer servicios o logística"}
APO = {"capital semilla o recursos no reembolsables":"Capital semilla (no reembolsable)",
       "alivio de las obligaciones actuales":"Alivio de obligaciones",
       "nuevo credito o financiacion":"Nuevo crédito",
       "no requiere apoyo financiero":"No requiere apoyo"}

est["_sev"]  = est["Nivel de afectación"].map(SEV)
est["_cont"] = est["Continuidad operativa"].map(CONT)
est["_perd"] = est["Pérdidas económicas"].map(PERD)
est["_empl"] = est["Empleos afectados o en riesgo"].map(EMPL)

filas = []
for mun, g in est.groupby("Municipio"):
    n = len(g)
    f = {"municipio": mun, "n": n}
    # cada componente sobre su propia base de respuesta
    for col, et in [("_sev","sev"),("_cont","cont"),("_perd","perd"),("_empl","empl")]:
        s = g[col].dropna()
        f[et] = round(float(s.mean()), 4) if len(s) else np.nan
        f[et+"_base"] = int(len(s))
    f["pct_severo"]   = round(100*g["Nivel de afectación"].isin(["Crítica","Grave"]).mean(),1)
    f["pct_no_opera"] = round(100*(g["Continuidad operativa"]=="No puede operar").mean(),1) if g["Continuidad operativa"].notna().any() else np.nan
    b = g["Continuidad operativa"].dropna()
    f["pct_no_opera"] = round(100*(b=="No puede operar").mean(),1) if len(b) else np.nan
    p = g["Pérdidas económicas"].dropna()
    f["pct_perd_alta"] = round(100*p.isin(["Más de $20 y hasta $100 millones.","Más de $100 millones."]).mean(),1) if len(p) else np.nan
    e = g["Empleos afectados o en riesgo"].dropna()
    f["pct_empleo"] = round(100*(e!="Ninguno").mean(),1) if len(e) else np.nan
    f["sin_clasif"] = round(100*(g["Nivel de afectación"]=="Sin clasificación").mean(),1)
    filas.append(f)
M = pd.DataFrame(filas)

# ── indice de afectacion economica ─────────────────────────────────────────
# Media de los cuatro componentes ordinales, ponderada por la severidad de lo
# que mide cada uno. Se normaliza 0-100. Los pesos son una decision de diseno y
# se declaran en el informe.
PESOS = {"sev":0.30, "cont":0.30, "perd":0.25, "empl":0.15}
M["IAE"] = sum(M[k].fillna(M[k].mean())*w for k,w in PESOS.items())
M["IAE"] = (100*(M.IAE - M.IAE.min())/(M.IAE.max()-M.IAE.min())).round(1)

# ── vecindad y I de Moran ──────────────────────────────────────────────────
geo = json.load(open(f"{OBS}/fuentes/municipios_valle.geojson", encoding="utf-8"))
ALIAS = {"SANTIAGO DE CALI":"CALI","CALIMA (EL DARIEN)":"CALIMA"}
def anillos(g):
    return [g["coordinates"][0]] if g["type"]=="Polygon" else [p[0] for p in g["coordinates"]]
pol = {}
for f in geo["features"]:
    nm = ALIAS.get(norm(f["properties"]["nombre"]), norm(f["properties"]["nombre"]))
    pol[nm] = [ {tuple(np.round(c,4)) for c in a} for a in anillos(f["geometry"]) ]

M["_k"] = M.municipio.map(lambda x: ALIAS.get(norm(x), norm(x)))
M = M[M._k.isin(pol)].reset_index(drop=True)
idx = {k:i for i,k in enumerate(M._k)}
nn = len(M)
W = np.zeros((nn,nn))
for a in M._k:
    va = set().union(*pol[a])
    for b in M._k:
        if a==b: continue
        vb = set().union(*pol[b])
        if len(va & vb) >= 1:          # comparten al menos un vertice: reina
            W[idx[a], idx[b]] = 1
grados = W.sum(1)
Wn = np.divide(W, grados[:,None], out=np.zeros_like(W), where=grados[:,None]>0)

def moran(x, Wn):
    x = np.asarray(x, float); z = x - x.mean()
    n = len(x); S0 = Wn.sum()
    I = (n/S0) * (z @ (Wn @ z)) / (z @ z)
    # significancia por permutaciones: no se asume normalidad
    rng = np.random.default_rng(42); sim = []
    for _ in range(999):
        zp = rng.permutation(z)
        sim.append((n/S0) * (zp @ (Wn @ zp)) / (zp @ zp))
    sim = np.array(sim)
    p = (np.sum(np.abs(sim) >= abs(I)) + 1) / 1000
    return I, p, sim.mean()

I, p, esp = moran(M.IAE.values, Wn)
zi = (M.IAE - M.IAE.mean())/M.IAE.std()
lag = Wn @ zi.values
Ii = zi.values * lag
M["z"] = zi.values.round(3); M["rezago"] = lag.round(3); M["Ii"] = Ii.round(3)
def cuad(z, l):
    if z > 0 and l > 0: return "Alto-Alto"
    if z < 0 and l < 0: return "Bajo-Bajo"
    if z > 0 and l < 0: return "Alto-Bajo"
    if z < 0 and l > 0: return "Bajo-Alto"
    return "—"
M["cluster"] = [cuad(a,b) for a,b in zip(M.z, M.rezago)]
# significancia local por permutacion condicional
rng = np.random.default_rng(7)
sig = []
for i in range(nn):
    vec = np.where(W[i]>0)[0]
    if len(vec)==0: sig.append(1.0); continue
    obs = Ii[i]; cnt = 0
    otros = np.delete(zi.values, i)
    for _ in range(999):
        m = rng.choice(otros, len(vec), replace=False).mean()
        if abs(zi.values[i]*m) >= abs(obs): cnt += 1
    sig.append((cnt+1)/1000)
M["p_local"] = np.round(sig,3)
M["cluster_sig"] = np.where(M.p_local<=0.05, M.cluster, "no significativo")

# ── multirespuesta a nivel departamental y de los 10 mas afectados ────────
top10 = M.nlargest(10,"IAE").municipio.tolist()
res = {
  "n_est": int(len(est)), "n_mun": int(len(M)),
  "moran_I": round(float(I),4), "moran_p": float(p), "moran_esperado": round(float(esp),4),
  "vecinos_prom": round(float(grados.mean()),2),
  "municipios": M.drop(columns=["_k"]).to_dict("records"),
  "top10": top10,
  "nec_dpto": multi(est["Principal necesidad"], NEC),
  "apo_dpto": multi(est["Apoyo financiero"], APO),
  "nec_top10": multi(est[est.Municipio.isin(top10)]["Principal necesidad"], NEC),
  "apo_top10": multi(est[est.Municipio.isin(top10)]["Apoyo financiero"], APO),
  "bases": {v: int(est[v].notna().sum()) for v in VARS},
  "pesos": PESOS,
  "sensibles_excluidas": SENSIBLES,
}
json.dump(res, open("geo_resultados.json","w",encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
M.to_csv("indice_municipal.csv", index=False)

print(f"establecimientos: {len(est):,}  ·  municipios: {nn}")
print(f"vecinos promedio por municipio: {grados.mean():.2f}")
print(f"\nI de Moran del IAE = {I:.4f}   (esperado bajo azar {esp:+.4f})   p = {p:.3f}")
print("  ->", "hay conglomeracion espacial" if p<=0.05 else "NO se detecta patron espacial: la afectacion esta dispersa")
print(f"\n{'municipio':22} {'n':>5} {'IAE':>6} {'%sev':>6} {'%noOp':>6} {'cluster':>16}")
for r in M.nlargest(15,"IAE").itertuples():
    print(f"{r.municipio[:22]:22} {r.n:5} {r.IAE:6} {r.pct_severo:6} {r.pct_no_opera:6} {r.cluster_sig:>16}")

# ═══════════════ CONTRACCION HACIA LA MEDIA DEPARTAMENTAL ═══════════════
#
# El indice crudo premia al municipio con pocos reportes. Trujillo encabezaba
# con 49 establecimientos: basta que unos pocos declaren lo peor para que su
# promedio se dispare, mientras Cali con 6.251 no puede moverse tanto. La
# correlacion entre el indice y el numero de reportes era 0,19 y la desviacion
# de los municipios pequenos (31,4) duplicaba la de los grandes (23,3).
#
# La correccion estandar en estimacion de areas pequenas es contraer cada
# estimacion hacia la media del conjunto, con un peso proporcional a cuanta
# informacion aporta el municipio:
#
#     w_i = tau2 / (tau2 + sigma2/n_i)
#     IAE_ajustado = w_i * IAE_i + (1 - w_i) * media_departamental
#
# tau2 es la varianza real entre municipios; sigma2/n_i, el ruido de muestreo
# de cada uno. Un municipio con muchos reportes conserva su valor; uno con
# pocos se acerca al promedio, que es la mejor apuesta cuando su propia
# evidencia es debil. No se borra el dato crudo: se publican los dos.
est_ind = est[["Municipio","_sev","_cont","_perd","_empl"]].copy()
comp = est_ind.assign(bruto=sum(est_ind[c].fillna(est_ind[c].mean())*w
                                for c,w in [("_sev",0.30),("_cont",0.30),
                                            ("_perd",0.25),("_empl",0.15)]))
sigma2 = float(comp.groupby("Municipio").bruto.var().mean())
medias = comp.groupby("Municipio").bruto.mean()
tau2 = float(medias.var())
mu = float(comp.bruto.mean())

M["_bruto"] = M.municipio.map(medias)
M["_w"] = tau2 / (tau2 + sigma2/M.n)
M["_ajust"] = M._w*M._bruto + (1-M._w)*mu
lo, hi = M._ajust.min(), M._ajust.max()
M["IAE_aj"] = (100*(M._ajust-lo)/(hi-lo)).round(1)
M["peso_w"] = M._w.round(3)

I2, p2, esp2 = moran(M.IAE_aj.values, Wn)
res["moran_ajustado"] = {"I": round(float(I2),4), "p": float(p2)}
res["shrinkage"] = {"tau2": round(tau2,5), "sigma2": round(sigma2,5),
                    "mu": round(mu,4),
                    "corr_bruto_n": round(float(M.IAE.corr(M.n)),3),
                    "corr_ajust_n": round(float(M.IAE_aj.corr(M.n)),3)}
res["municipios"] = M.drop(columns=["_k","_bruto","_w","_ajust"]).to_dict("records")
res["top10"] = M.nlargest(10,"IAE_aj").municipio.tolist()
top10 = res["top10"]
res["nec_top10"] = multi(est[est.Municipio.isin(top10)]["Principal necesidad"], NEC)
res["apo_top10"] = multi(est[est.Municipio.isin(top10)]["Apoyo financiero"], APO)
json.dump(res, open("geo_resultados.json","w",encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
M.to_csv("indice_municipal.csv", index=False)

print("\n" + "═"*66)
print(f"CONTRACCION:  tau2={tau2:.5f}  sigma2={sigma2:.5f}  media={mu:.4f}")
print(f"  correlacion con n:  bruto {M.IAE.corr(M.n):+.3f}  ->  ajustado {M.IAE_aj.corr(M.n):+.3f}")
print(f"  I de Moran ajustado = {I2:.4f}  p = {p2:.3f}")
print(f"\n{'municipio':22} {'n':>5} {'peso':>6} {'IAE':>6} {'IAEaj':>6}  cambio")
for r in M.nlargest(15,"IAE_aj").itertuples():
    print(f"{r.municipio[:22]:22} {r.n:5} {r.peso_w:6} {r.IAE:6} {r.IAE_aj:6}  {r.IAE_aj-r.IAE:+.1f}")
