"""Cruce de las tres fuentes: cuanto se necesita frente a cuanto ha llegado.

LA PREGUNTA
El observatorio dice que municipios tienen el tejido empresarial mas golpeado.
La matriz GRD dice cuales estan en criticidad humanitaria. La Ruta de la
Solidaridad dice a cuales ha llegado la ayuda. Ninguna de las tres responde
sola a «donde poner el proximo camion»; el cruce si.

COMO SE MIDE LA BRECHA
No se comparan toneladas contra toneladas porque los municipios son de tamano
muy distinto. Se comparan POSICIONES: el puesto que ocupa un municipio por
necesidad frente al puesto que ocupa por ayuda recibida. Si un municipio es el
tercero mas critico y el puesto 30 en ayuda, hay una brecha de 27 puestos, y
eso no depende de su tamano.

  brecha = puesto_por_ayuda − puesto_por_necesidad

  positiva  → recibe menos de lo que su necesidad indicaria (rezagado)
  negativa  → recibe mas (adelantado)

Se usa el rango (rank) y no el valor porque las tres fuentes miden en unidades
incomparables: un indice 0-100, un porcentaje de establecimientos y toneladas.
Lo unico comparable entre ellas es el orden.

ADVERTENCIA DE LECTURA
Una brecha positiva NO prueba mala asignacion. Puede reflejar que el municipio
recibio por otra ruta, que su acceso vial estaba cerrado, o que la ayuda
adecuada no era la que despacha esta ruta. Es una senal para revisar, no un
veredicto.
"""
import json
import re
import unicodedata

import numpy as np
import pandas as pd

from fuentes_oficiales import AYUDA, AYUDA_KPI, GRD, GRD_KPI, leer


def norm(s):
    s = unicodedata.normalize("NFD", str(s).upper())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", s).strip()


# Las tres fuentes nombran distinto a los mismos municipios.
ALIAS = {"GUADALAJARA DE BUGA": "BUGA", "CALIMA (EL DARIEN)": "CALIMA",
         "CALIMA - EL DARIEN": "CALIMA", "SANTIAGO DE CALI": "CALI"}
clave = lambda s: ALIAS.get(norm(s), norm(s))

G = leer(GRD).assign(k=lambda d: d.municipio.map(clave))
A = leer(AYUDA).assign(k=lambda d: d.municipio.map(clave))
E = pd.read_csv("indice_municipal.csv").assign(k=lambda d: d.municipio.map(clave))

D = (G.merge(A[["k", "entregas", "zona", "toneladas"]], on="k", how="outer")
      .merge(E[["k", "n", "IAE_aj", "pct_severo", "pct_no_opera",
                "pct_perd_alta", "pct_empleo"]], on="k", how="left"))

falt = D[D.icm.isna()].k.tolist()
print(f"municipios sin ICM (fuera de la matriz GRD): {falt}")
D = D[D.icm.notna()].copy()

# ── necesidad: dos miradas que no son la misma ───────────────────────────
# ICM  = criticidad humanitaria oficial (personas, vivienda, conectividad)
# IAE  = afectacion del tejido empresarial, de esta base
D["r_icm"] = D.icm.rank(ascending=False)
D["r_iae"] = D.IAE_aj.rank(ascending=False)
D["r_nec"] = ((D.r_icm + D.r_iae.fillna(D.r_icm)) / 2).rank()
D["r_ayuda"] = D.toneladas.rank(ascending=False)
D["brecha"] = D.r_ayuda - D.r_nec

# ── intensidad de la ayuda relativa a la poblacion afectada ──────────────
# Para leer volumen, no orden: kilos por persona afectada declarada.
D["kg_por_afectado"] = (1000 * D.toneladas /
                        D.poblacion_afectada.replace(0, np.nan)).round(1)

# Cuantos de los mas golpeados economicamente quedan fuera de los criticos
# del tablero oficial, y al reves. Se cuenta, no se afirma de memoria.
NC = int((D.icm_semaforo == "Crítico").sum())
top_iae = set(D.nsmallest(NC, "r_iae").municipio)
top_icm = set(D.nsmallest(NC, "r_icm").municipio)
FUERA_ECON = sorted(top_iae - top_icm)
FUERA_HUM = sorted(top_icm - top_iae)

# ── cuadrantes de decision ───────────────────────────────────────────────
mi, ma = D.r_nec.median(), D.r_ayuda.median()


def cuadrante(r):
    alta_nec = r.r_nec <= mi          # rank bajo = mas necesidad
    mucha_ayuda = r.r_ayuda <= ma
    if alta_nec and not mucha_ayuda:
        return "1 · Necesidad alta, ayuda baja"
    if alta_nec and mucha_ayuda:
        return "2 · Necesidad alta, ayuda alta"
    if not alta_nec and mucha_ayuda:
        return "3 · Necesidad baja, ayuda alta"
    return "4 · Necesidad baja, ayuda baja"


D["cuadrante"] = D.apply(cuadrante, axis=1)

# ── discrepancia entre las dos miradas de necesidad ──────────────────────
# Municipios donde la criticidad humanitaria y la economica no coinciden:
# son los que un solo tablero no ve.
D["disc"] = D.r_icm - D.r_iae

D = D.sort_values("r_nec").reset_index(drop=True)
COLS = ["municipio", "zona", "icm", "icm_semaforo", "semaforo_vuln", "IAE_aj",
        "n", "poblacion_afectada", "viv_destruidas", "fallecidos", "heridos",
        "entregas", "toneladas",
        "kg_por_afectado", "r_icm", "r_iae", "r_nec", "r_ayuda", "brecha",
        "cuadrante", "disc", "pct_no_opera", "pct_perd_alta", "emprendimientos"]
D[COLS].round(2).to_csv("brecha_municipal.csv", index=False)

mil = lambda x: f"{x:,.0f}".replace(",", ".")
print("\n" + "=" * 78)
print("REZAGADOS · alta necesidad, poca ayuda relativa")
print("=" * 78)
print(f"  {'municipio':16} {'ICM':>6} {'IAE':>6} {'ton':>5} {'kg/afec':>8} "
      f"{'p.nec':>6} {'p.ayu':>6} {'brecha':>7}")
for r in D.nlargest(10, "brecha").itertuples():
    print(f"  {r.municipio[:16]:16} {r.icm:6.1f} "
          f"{(r.IAE_aj if pd.notna(r.IAE_aj) else 0):6.1f} {r.toneladas:5.0f} "
          f"{(r.kg_por_afectado if pd.notna(r.kg_por_afectado) else 0):8.1f} "
          f"{r.r_nec:6.0f} {r.r_ayuda:6.0f} {r.brecha:+7.0f}")

print("\nADELANTADOS · menos necesidad relativa, mas ayuda")
for r in D.nsmallest(6, "brecha").itertuples():
    print(f"  {r.municipio[:16]:16} {r.icm:6.1f} "
          f"{(r.IAE_aj if pd.notna(r.IAE_aj) else 0):6.1f} {r.toneladas:5.0f} "
          f"{r.r_nec:6.0f} {r.r_ayuda:6.0f} {r.brecha:+7.0f}")

print("\n" + "=" * 78)
print("CUADRANTES")
print(D.cuadrante.value_counts().sort_index().to_string())
print("\nCuadrante 1 (prioridad):")
print("  " + ", ".join(D[D.cuadrante.str.startswith("1")].municipio))

print("\n" + "=" * 78)
print("LAS DOS MIRADAS NO COINCIDEN")
print("  criticidad humanitaria alta, afectación económica baja:")
for r in D.nsmallest(5, "disc").itertuples():
    print(f"    {r.municipio[:16]:16} ICM p.{r.r_icm:.0f}  ·  IAE p.{r.r_iae:.0f}")
print("  afectación económica alta, criticidad humanitaria baja:")
for r in D.nlargest(5, "disc").itertuples():
    print(f"    {r.municipio[:16]:16} ICM p.{r.r_icm:.0f}  ·  IAE p.{r.r_iae:.0f}")
corr = D[["icm", "IAE_aj"]].corr(method="spearman").iloc[0, 1]
print(f"\n  correlación de Spearman entre ICM e IAE: {corr:.3f}")

print("\n" + "=" * 78)
print("INTENSIDAD DE LA AYUDA")
print(f"  mediana kg por persona afectada: {D.kg_por_afectado.median():.1f}")
print("  menor intensidad:")
for r in D.nsmallest(6, "kg_por_afectado").itertuples():
    print(f"    {r.municipio[:16]:16} {r.kg_por_afectado:6.1f} kg/afectado · "
          f"{mil(r.poblacion_afectada)} afectados · {r.toneladas:.0f} t")

sin = D[D.toneladas == 0]
print(f"\n  municipios sin una sola entrega: {list(sin.municipio)}")

res = {
    "grd": GRD_KPI, "ayuda": AYUDA_KPI,
    "corr_icm_iae": round(float(corr), 3),
    "n_criticos": NC, "fuera_econ": FUERA_ECON, "fuera_hum": FUERA_HUM,
    "mediana_kg": round(float(D.kg_por_afectado.median()), 1),
    "cuadrantes": {k: int(v) for k, v in D.cuadrante.value_counts().items()},
    "prioridad": D[D.cuadrante.str.startswith("1")].municipio.tolist(),
    "rezagados": D.nlargest(10, "brecha")[
        ["municipio", "icm", "IAE_aj", "toneladas", "entregas", "kg_por_afectado",
         "r_nec", "r_ayuda", "brecha", "poblacion_afectada", "viv_destruidas",
         "semaforo_vuln"]].round(1).to_dict("records"),
    "adelantados": D.nsmallest(5, "brecha")[
        ["municipio", "icm", "IAE_aj", "toneladas", "r_nec", "r_ayuda", "brecha"]]
        .round(1).to_dict("records"),
    "solo_humanitario": D.nsmallest(5, "disc")[
        ["municipio", "icm", "IAE_aj", "r_icm", "r_iae"]].round(1).to_dict("records"),
    "solo_economico": D.nlargest(5, "disc")[
        ["municipio", "icm", "IAE_aj", "r_icm", "r_iae"]].round(1).to_dict("records"),
    "sin_entregas": sin.municipio.tolist(),
    "baja_intensidad": D.nsmallest(6, "kg_por_afectado")[
        ["municipio", "kg_por_afectado", "poblacion_afectada", "toneladas",
         "icm"]].round(1).to_dict("records"),
    "municipios": D[COLS].round(2).to_dict("records"),
}
def limpio(o):
    """NaN no es JSON valido y rompe el generador del informe en Node."""
    if isinstance(o, dict):
        return {k: limpio(v) for k, v in o.items()}
    if isinstance(o, list):
        return [limpio(v) for v in o]
    if isinstance(o, float) and np.isnan(o):
        return None
    return o


json.dump(limpio(res), open("brecha.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1, default=str)
print("\nbrecha.json y brecha_municipal.csv escritos")
