"""Base cruzada: censo de afectación (corte 3 sep) × RNT vigente del Valle.

Entrega un Excel con TODOS los establecimientos de la cadena de valor del
turismo que reportaron daño, marcados según aparezcan o no en el Registro
Nacional de Turismo.

CADENA DE VALOR DEL TURISMO
Sectores «Alojamiento y servicios de comida» y «Transporte y almacenamiento»
del censo: el mismo criterio con el que se construyó la cifra ya socializada.

LA MARCA DE RNT DICE «APARECE», NO «TIENE»
El RNT no trae NIT, así que la única llave entre las dos bases es la razón
social normalizada más el municipio. «No se encontró» significa VERIFICAR, no
que el negocio sea informal: más de la mitad del RNT son viviendas turísticas
registradas con nombres que no son un nombre comercial.

DATOS SENSIBLES
Los campos de contacto se leen solo para detectar doble notificación. No salen
en el archivo entregado.
"""
import json
import os
import re
import unicodedata
import warnings
from collections import defaultdict

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

import sys as _sys; from pathlib import Path as _Path
_sys.path.insert(0, str(next(p for p in _Path(__file__).resolve().parents if (p / "rutas.py").is_file())))
from rutas import fuente, GEORIESGO  # rutas relativas del laboratorio (antes /sessions/.../mnt)
REP = fuente("reportes_emergencia_2026-09-03.xlsx")
REP_ANT = fuente("reportes_emergencia_2026-09-01.xlsx")
RNT = fuente("rnt valle.xlsx")
OUT = "Turismo_cruce_RNT_2026-09-03.xlsx"
CORTE = "3 de septiembre de 2026"

ANO_VIGENTE = 2026
SEC_TURISMO = ["Alojamiento y servicios de comida", "Transporte y almacenamiento"]
SUFIJOS = r"\b(S\.?A\.?S|SAS|LTDA|LIMITADA|S\.?A|E\.?U|EU|SCA|S\.?C\.?A|" \
          r"CIA|COMPANIA|Y CIA|EN LIQUIDACION|ZOMAC|BIC|ESAL|SOCIEDAD)\b"


def desnuda(s):
    if pd.isna(s):
        return ""
    s = unicodedata.normalize("NFD", str(s).replace("�", "N").upper())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9 ]", " ", s)).strip()


def norm_emp(s):
    return re.sub(r"\s+", " ", re.sub(SUFIJOS, " ", desnuda(s))).strip()


def digitos(s):
    if pd.isna(s):
        return ""
    d = re.sub(r"\D", "", str(s))
    return d[-10:] if len(d) >= 10 else d


ALIAS_MUN = {"GUADALAJARA DE BUGA": "BUGA", "CALIMA EL DARIEN": "CALIMA",
             "CALIMA DARIEN": "CALIMA", "CALIMA EL DARIEN ": "CALIMA",
             "SANTIAGO DE CALI": "CALI"}
nmun = lambda s: ALIAS_MUN.get(desnuda(s), desnuda(s))

GENERICOS = {"", "NINGUNO", "NA", "N A", "NO APLICA", "NO", "PARTICULAR",
             "INDEPENDIENTE", "COMERCIANTE", "VENDEDOR AMBULANTE",
             "AGROPECUARIA", "PROPIO", "NO TENGO", "SIN NOMBRE", "CASA", "HOGAR"}
util = lambda nom: len(nom) >= 6 and nom not in GENERICOS

# ── 1 · depuración de doble notificación ─────────────────────────────────
# Solo identificadores fuertes, con guarda de coherencia para no colapsar el
# patrón de gestor (una persona que diligenció por muchos negocios).
MAX_DOCS, MAX_NOMBRES = 1, 2
raw = pd.read_excel(REP, sheet_name="Reportes").reset_index(drop=True)
N0 = len(raw)
raw["_tel"] = raw["Teléfono de contacto"].map(digitos)
raw["_mail"] = raw["Correo electrónico de contacto"].map(
    lambda x: str(x).strip().lower() if pd.notna(x) else "")
raw["_nit"] = raw["NIT"].map(digitos)
raw["_doc"] = raw["Documento de identificación"].map(digitos)
raw["zemp"] = raw.Empresa.map(norm_emp)

padre = list(range(N0))


def raiz(a):
    while padre[a] != a:
        padre[a] = padre[padre[a]]
        a = padre[a]
    return a


def unir(a, b):
    ra, rb = raiz(a), raiz(b)
    if ra != rb:
        padre[max(ra, rb)] = min(ra, rb)


def coherente(sub):
    docs = sub["_doc"][sub["_doc"].str.len() >= 6].nunique()
    noms = sub["zemp"][sub["zemp"].str.len() >= 4].nunique()
    return docs <= MAX_DOCS and noms <= MAX_NOMBRES


gestores = 0
for col, minlen in [("_tel", 7), ("_mail", 5), ("_nit", 7), ("_doc", 6)]:
    base = raw[raw[col].str.len() >= minlen]
    if col == "_mail":
        base = base[base._mail.str.contains("@", na=False)]
    for _, idxs in base.groupby(col).indices.items():
        if len(idxs) < 2:
            continue
        if not coherente(raw.loc[idxs]):
            gestores += 1
            continue
        for i in range(1, len(idxs)):
            unir(int(idxs[0]), int(idxs[i]))

ORDEN_SEV = {"Crítica": 0, "Grave": 1, "Moderada": 2, "Baja": 3,
             "Sin clasificación": 4, "no_afectado": 5}
raw["_grupo"] = [raiz(i) for i in range(N0)]
raw["_o"] = raw["Nivel de afectación"].map(ORDEN_SEV).fillna(9)
R = raw.sort_values("_o").drop_duplicates("_grupo", keep="first").copy()
DUPS = N0 - len(R)
R["zmun"] = R.Municipio.map(nmun)
T = R[R["Actividad económica/sector"].isin(SEC_TURISMO)].copy()

# ── 2 · RNT vigente ──────────────────────────────────────────────────────
rnt = pd.read_excel(RNT, sheet_name="Data")
V = rnt[rnt.ANO == ANO_VIGENTE].drop_duplicates("CODIGO_RNT").copy()
V["zmun"] = V.MUNICIPIO.map(nmun)
V["zemp"] = V.RAZON_SOCIAL_ESTABLECIMIENTO.map(norm_emp)

exacto, tokens = defaultdict(dict), defaultdict(list)
for r in V.itertuples():
    if util(r.zemp):
        exacto[r.zmun][r.zemp] = (r.CATEGORIA, r.SUB_CATEGORIA, r.CODIGO_RNT)
        tokens[r.zmun].append((set(r.zemp.split()), r.CATEGORIA, r.SUB_CATEGORIA,
                               r.CODIGO_RNT))


def marcar(nombre, municipio):
    if not nombre:
        return "Sin razón social declarada", "", "", "", ""
    if not util(nombre):
        return "Nombre genérico, no cruzable", "", "", "", ""
    h = exacto[municipio].get(nombre)
    if h:
        return "Sí (exacta)", h[0], h[1], h[2], "1,00"
    t = set(nombre.split())
    mejor, cat, sub, cod = 0.0, "", "", ""
    for s, c, sc, k in tokens[municipio]:
        u = len(t | s)
        if u:
            j = len(t & s) / u
            if j > mejor:
                mejor, cat, sub, cod = j, c, sc, k
    if mejor >= 0.75:
        return "Sí (probable)", cat, sub, cod, f"{mejor:.2f}".replace(".", ",")
    return "No se encontró", "", "", "", ""


m = [marcar(r.zemp, r.zmun) for r in T.itertuples()]
T["RNT"] = [x[0] for x in m]
T["Categoría RNT"] = [x[1] for x in m]
T["Subcategoría RNT"] = [x[2] for x in m]
T["Código RNT"] = [x[3] for x in m]
T["Similitud"] = [x[4] for x in m]

# ── 3 · marca de persona natural (Ley 1581) ──────────────────────────────
COMERCIAL = {
    "HOTEL", "HOSTAL", "HOSPEDAJE", "POSADA", "CABANA", "CABANAS", "FINCA",
    "MOTEL", "APARTAHOTEL", "RESIDENCIA", "RESIDENCIAS", "ALOJAMIENTO",
    "RESTAURANTE", "ASADERO", "CAFETERIA", "CAFE", "PANADERIA", "PIZZERIA",
    "COMIDAS", "COMIDA", "CEVICHERIA", "PARRILLA", "FONDA", "BAR", "TABERNA",
    "DISCOTECA", "HELADERIA", "FRUTERIA", "PESCADERIA", "EMPANADAS",
    "PIQUETEADERO", "TRANSPORTES", "TRANSPORTE", "TAXI", "TAXIS", "BUSES",
    "COOPERATIVA", "AGENCIA", "VIAJES", "TURISMO", "TOURS", "OPERADOR",
    "ECOTURISMO", "CENTRO", "CLUB", "PARQUE", "BALNEARIO", "PISCINA", "SALON",
    "EVENTOS", "EL", "LA", "LOS", "LAS", "DEL", "SAN", "SANTA", "DON", "DONA",
    "SAZON", "RINCON", "MIRADOR", "PARAISO", "ESQUINA", "PUNTO", "SABOR",
    "DELICIAS", "TIENDA", "MERCADO", "SUPERMERCADO", "ALMACEN", "VARIEDADES",
    "SERVICIOS", "EMPRESA", "GRUPO", "INVERSIONES", "DISTRIBUIDORA",
    "COMERCIALIZADORA", "PANADERIA", "REPOSTERIA", "GRANERO",
}
PERSONALES = {
    "JOSE", "JUAN", "LUIS", "CARLOS", "JORGE", "MARIA", "ANA", "LUZ", "MARTHA",
    "SANDRA", "DIEGO", "ANDRES", "JAVIER", "FERNANDO", "RICARDO", "OSCAR",
    "WILLIAM", "JHON", "JOHN", "JAIRO", "HERNAN", "GERMAN", "ALEXANDER",
    "CLAUDIA", "PATRICIA", "LILIANA", "MONICA", "GLORIA", "NANCY", "ROSA",
    "CARMEN", "ELENA", "BEATRIZ", "ESPERANZA", "YENNY", "YULI", "LEIDY",
    "GOMEZ", "RODRIGUEZ", "MARTINEZ", "LOPEZ", "GARCIA", "PEREZ", "SANCHEZ",
    "RAMIREZ", "TORRES", "FLOREZ", "VARGAS", "CASTRO", "RUIZ", "DIAZ",
    "MORENO", "MUNOZ", "ROJAS", "MORALES", "JIMENEZ", "GUTIERREZ", "ALVAREZ",
    "MEJIA", "OSORIO", "SALAZAR", "CARDONA", "ARIAS", "GIRALDO", "OCAMPO",
    "ZAPATA", "VALENCIA", "MONTOYA", "RESTREPO", "HURTADO", "MOSQUERA",
    "CAICEDO", "VELASQUEZ", "BEDOYA", "AGUDELO", "QUINTERO", "HENAO",
}


def parece_persona(nom):
    p = [w for w in nom.split() if len(w) > 2]
    if len(p) < 2 or any(w in COMERCIAL for w in p):
        return False
    return any(w in PERSONALES for w in p)


T["Revisar Ley 1581"] = ["Sí" if parece_persona(e) else "" for e in T.zemp]

# ── 4 · métricas municipales ─────────────────────────────────────────────
PLO = {"Menos de $5 millones.": 0, "Entre $5 y $20 millones.": 5,
       "Más de $20 y hasta $100 millones.": 20, "Más de $100 millones.": 0}
SEV = ["Crítica", "Grave"]
rnt_mun = V.groupby("zmun").size()
filas = []
for k in sorted(set(T.zmun) | set(rnt_mun.index)):
    g = T[T.zmun == k]
    p = g["Pérdidas económicas"].dropna()
    e = g["Empleos afectados o en riesgo"].dropna()
    c = g.RNT.value_counts() if len(g) else {}
    ab = int((p == "Más de $100 millones.").sum())
    filas.append({
        "Municipio": k.title().replace(" De ", " de "),
        "Negocios turísticos afectados": len(g),
        "Prestadores con RNT vigente": int(rnt_mun.get(k, 0)),
        "Aparece en RNT (exacta)": int(c.get("Sí (exacta)", 0)) if len(g) else 0,
        "Aparece en RNT (probable)": int(c.get("Sí (probable)", 0)) if len(g) else 0,
        "No se encontró en RNT": int(c.get("No se encontró", 0)) if len(g) else 0,
        "Sin razón social": int(c.get("Sin razón social declarada", 0)) if len(g) else 0,
        "Nombre genérico": int(c.get("Nombre genérico, no cruzable", 0)) if len(g) else 0,
        "Crítica o grave": int(g["Nivel de afectación"].isin(SEV).sum()),
        "No puede operar": int((g["Continuidad operativa"] == "No puede operar").sum()),
        "Con empleo comprometido": int((e != "Ninguno").sum()),
        "Pérdidas piso (millones)": int(sum(PLO[x] for x in p) + 100 * ab),
        "Revisar Ley 1581": int((g["Revisar Ley 1581"] == "Sí").sum()),
    })
MU = pd.DataFrame(filas).sort_values("Negocios turísticos afectados", ascending=False)
MU = MU.reset_index(drop=True)
TOT = ["TOTAL"] + [MU[c].sum() for c in MU.columns[1:]]
MU.loc[len(MU)] = TOT

# ── 5 · salida ───────────────────────────────────────────────────────────
COLS = {
    "Número de reporte": "N.º de reporte",
    "Municipio": "Municipio",
    "Empresa": "Razón social declarada",
    "Actividad económica/sector": "Sector",
    "Tamaño de empresa": "Tamaño",
    "Nivel de afectación": "Nivel de afectación",
    "Continuidad operativa": "Continuidad operativa",
    "Pérdidas económicas": "Pérdidas declaradas",
    "Empleos afectados o en riesgo": "Empleo comprometido",
    "Principal necesidad": "Necesidad principal",
    "Apoyo financiero": "Apoyo preferido",
}
B = T.sort_values(["zmun", "_o", "Empresa"])
CR = B[list(COLS)].rename(columns=COLS)
for c in ["RNT", "Categoría RNT", "Subcategoría RNT", "Código RNT", "Similitud",
          "Revisar Ley 1581"]:
    CR[c] = B[c].values

cc = T.RNT.value_counts()
APAR = int(cc.get("Sí (exacta)", 0) + cc.get("Sí (probable)", 0))
NOTAS = pd.DataFrame({"Nota": [
    "BASE CRUZADA · USO INTERNO. Contiene razón social de establecimientos afectados.",
    "",
    f"Censo de afectación, corte {CORTE}.",
    f"  {N0:,} reportes recibidos → {len(R):,} establecimientos únicos "
    f"({DUPS:,} dobles notificaciones retiradas).".replace(",", "."),
    f"  {gestores} grupos con patrón de gestor detectados y NO fusionados.",
    f"  Cadena de valor del turismo: {len(T):,} establecimientos.".replace(",", "."),
    "",
    f"Registro Nacional de Turismo, corte {ANO_VIGENTE}: {len(V):,} prestadores "
    f"vigentes.".replace(",", "."),
    f"  Cruzan con el censo: {APAR} ({100 * APAR / len(T):.1f} % de los turísticos "
    f"afectados, {100 * APAR / len(V):.1f} % del registro).".replace(".", ","),
    "",
    "COLUMNA RNT — dice si el nombre APARECE en el registro, no si el negocio lo tiene:",
    "  Sí (exacta)            el nombre normalizado coincide carácter por carácter",
    "  Sí (probable)          coinciden 75 % o más de las palabras; la columna "
    "Similitud trae el índice. VERIFICAR antes de usar",
    "  No se encontró         sin coincidencia. VERIFICAR: no prueba que sea informal",
    "  Sin razón social declarada   el reporte no trae nombre del establecimiento",
    "  Nombre genérico, no cruzable el nombre declarado es genérico o demasiado corto",
    "",
    "El RNT no trae NIT, así que la única llave posible es la razón social más el "
    "municipio. Más de la mitad del RNT son viviendas turísticas, registradas con "
    "nombres que no corresponden a un nombre comercial y que por eso nunca cruzan.",
    "",
    "COLUMNA REVISAR LEY 1581 — la razón social parece ser el nombre de una persona "
    "natural. Requiere tratamiento aparte antes de circular el listado.",
    "",
    "NO se incluyen nombre de la persona, documento, teléfono, correo, NIT, dirección "
    "ni barrio. Esos campos se leen solo para detectar doble notificación.",
]})

with pd.ExcelWriter(OUT, engine="openpyxl") as w:
    NOTAS.to_excel(w, sheet_name="Método y advertencias", index=False)
    MU.to_excel(w, sheet_name="Resumen municipal", index=False)
    CR.to_excel(w, sheet_name="Base cruzada turismo", index=False)
    CR[CR.RNT.str.startswith("Sí")].to_excel(w, sheet_name="Solo los que cruzan",
                                             index=False)
    for ws in w.book.worksheets:
        for col in ws.columns:
            a = max((len(str(c.value)) for c in col if c.value), default=10)
            ws.column_dimensions[col[0].column_letter].width = min(max(a + 2, 11), 56)
        ws.freeze_panes = "A2"

# ── comparación con el corte anterior ────────────────────────────────────
ant = pd.read_excel(REP_ANT, sheet_name="Reportes")
res = {"corte": "2026-09-03", "n0": N0, "unicos": len(R), "dups": DUPS,
       "gestores": gestores, "turismo": len(T), "rnt_vigentes": len(V),
       "cruzan": APAR, "exacta": int(cc.get("Sí (exacta)", 0)),
       "probable": int(cc.get("Sí (probable)", 0)),
       "no_encontrado": int(cc.get("No se encontró", 0)),
       "sin_razon": int(cc.get("Sin razón social declarada", 0)),
       "generico": int(cc.get("Nombre genérico, no cruzable", 0)),
       "ley1581": int((T["Revisar Ley 1581"] == "Sí").sum()),
       "anterior_n0": len(ant)}
json.dump(res, open("cruce_0903.json", "w", encoding="utf-8"), ensure_ascii=False,
          indent=1)
MU.to_csv("turismo_municipal_0903.csv", index=False)

mil = lambda x: f"{x:,}".replace(",", ".")
print("=" * 72)
print(f"CORTE {CORTE}")
print("=" * 72)
print(f"  reportes recibidos          {mil(N0):>8}   (antes {mil(len(ant))})")
print(f"  doble notificación          {mil(DUPS):>8}   ({100*DUPS/N0:.1f} %)")
print(f"  establecimientos únicos     {mil(len(R)):>8}")
print(f"  cadena de valor del turismo {mil(len(T)):>8}")
print("-" * 72)
print(f"  RNT vigente {ANO_VIGENTE}            {mil(len(V)):>8}")
print(f"  cruzan con el censo         {APAR:>8}   "
      f"({100*APAR/len(T):.1f} % del turismo afectado)")
print(f"    exacta                    {cc.get('Sí (exacta)',0):>8}")
print(f"    probable                  {cc.get('Sí (probable)',0):>8}")
print(f"    no se encontró            {cc.get('No se encontró',0):>8}")
print(f"    sin razón social          {cc.get('Sin razón social declarada',0):>8}")
print(f"    nombre genérico           {cc.get('Nombre genérico, no cruzable',0):>8}")
print(f"  filas a revisar Ley 1581    {res['ley1581']:>8}")
print("=" * 72)
print(f"\nescrito: {OUT}\n")
print(MU.head(16).to_string(index=False))
