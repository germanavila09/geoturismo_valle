"""Listado nominal de negocios turísticos afectados en los municipios priorizados.

AUTOSUFICIENTE: solo necesita los dos Excel. Rehace por dentro la depuración
de doble notificación, así que no depende de ningún archivo intermedio.

USO
    python listado_priorizados.py [reportes.xlsx] [rnt.xlsx] [salida.xlsx]

Requiere pandas y openpyxl:
    pip install pandas openpyxl

QUE ENTREGA
Un .xlsx de USO INTERNO con:
  · «Método y advertencias» · cómo leer cada columna
  · «Resumen»               · conteos por municipio y por marca de RNT
  · una hoja por municipio  · el listado de establecimientos

QUE COLUMNAS SALEN Y POR QUE
Solo datos del establecimiento: razón social, sector, tamaño, nivel de
afectación, continuidad operativa, pérdidas, empleo comprometido, necesidad
principal, apoyo preferido y la marca de RNT.

NO salen nombre de la persona, documento, teléfono, correo, NIT, dirección ni
barrio. En la auditoría de esta base se encontraron 1.576 registros con datos
personales sin autorización verificable bajo la Ley 1581 de 2012, y este
listado no debe propagarlos. Esos campos se leen únicamente para detectar
duplicados y para nada más.

LA MARCA DE RNT DICE «APARECE», NO «TIENE»
El RNT no trae NIT, de modo que la única llave posible entre las dos bases es
la razón social normalizada más el municipio. «No se encontró» significa
VERIFICAR, no que el negocio sea informal: en todo el departamento el cruce
por nombre solo empareja 174 de 1.703 reportes, y más de la mitad del RNT son
viviendas turísticas registradas con nombres que no son un nombre comercial.
"""
import os
import re
import sys
import unicodedata
import warnings
from collections import defaultdict

import pandas as pd

warnings.filterwarnings("ignore")

# ── rutas ────────────────────────────────────────────────────────────────
import sys as _sys; from pathlib import Path as _Path
_sys.path.insert(0, str(next(p for p in _Path(__file__).resolve().parents if (p / "rutas.py").is_file())))
from rutas import fuente, GEORIESGO  # rutas relativas del laboratorio (antes /sessions/.../mnt)
DEF_REP = fuente("reportes_emergencia_2026-09-01.xlsx")
DEF_RNT = fuente("rnt valle.xlsx")
DEF_OUT = "Turismo_priorizados_listado.xlsx"

REP = sys.argv[1] if len(sys.argv) > 1 else DEF_REP
RNT = sys.argv[2] if len(sys.argv) > 2 else DEF_RNT
OUT = sys.argv[3] if len(sys.argv) > 3 else DEF_OUT

ANO_VIGENTE = 2026
SEC_TURISMO = ["Alojamiento y servicios de comida", "Transporte y almacenamiento"]
PRIORIZADOS = ["ROLDANILLO", "BUENAVENTURA", "SEVILLA", "CARTAGO",
               "LA UNION", "ZARZAL"]
BONITO = {"ROLDANILLO": "Roldanillo", "BUENAVENTURA": "Buenaventura",
          "SEVILLA": "Sevilla", "CARTAGO": "Cartago", "LA UNION": "La Unión",
          "ZARZAL": "Zarzal"}

# ── normalización ────────────────────────────────────────────────────────
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
             "CALIMA DARIEN": "CALIMA", "SANTIAGO DE CALI": "CALI"}
nmun = lambda s: ALIAS_MUN.get(desnuda(s), desnuda(s))

GENERICOS = {"", "NINGUNO", "NA", "N A", "NO APLICA", "NO", "PARTICULAR",
             "INDEPENDIENTE", "COMERCIANTE", "VENDEDOR AMBULANTE",
             "AGROPECUARIA", "PROPIO", "NO TENGO", "SIN NOMBRE", "CASA", "HOGAR"}
util = lambda nom: len(nom) >= 6 and nom not in GENERICOS

# ═════════════════════════════════════════════════════════════════════════
# 1 · DEPURACIÓN DE DOBLE NOTIFICACIÓN
# ═════════════════════════════════════════════════════════════════════════
# Se agrupa solo por identificadores fuertes —teléfono, correo, NIT y
# documento— y nunca por parecido de nombre: emparejar por similitud de razón
# social produjo un grupo de 200 reportes con 199 teléfonos distintos en 13
# municipios, porque el encadenamiento «A se parece a B, B a C» une negocios
# que no tienen relación.
#
# Compartir un teléfono tampoco basta. Aparece un patrón de GESTOR: alguien que
# diligenció el formulario para muchos negocios y puso sus propios datos de
# contacto (un correo en 35 reportes de 13 municipios con 35 razones sociales).
# Colapsar eso borraría establecimientos reales. Por eso un grupo se acepta
# solo si además puede ser una sola unidad económica.
MAX_DOCS = 1        # documentos distintos tolerados dentro de un grupo
MAX_NOMBRES = 2     # razones sociales distintas toleradas

raw = pd.read_excel(REP, sheet_name="Reportes").reset_index(drop=True)
N0 = len(raw)

raw["_tel"] = raw["Teléfono de contacto"].map(digitos)
raw["_mail"] = raw["Correo electrónico de contacto"].map(
    lambda x: str(x).strip().lower() if pd.notna(x) else "")
raw["_nit"] = raw["NIT"].map(digitos)
raw["_doc"] = raw["Documento de identificación"].map(digitos)
raw["_emp"] = raw.Empresa.map(norm_emp)

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
    noms = sub["_emp"][sub["_emp"].str.len() >= 4].nunique()
    return docs <= MAX_DOCS and noms <= MAX_NOMBRES


SENALES = [("_tel", 7), ("_mail", 5), ("_nit", 7), ("_doc", 6)]
gestores = 0
for col, minlen in SENALES:
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

# Al colapsar se conserva el reporte con la severidad más alta: entre dos
# notificaciones del mismo negocio se asume el peor estado declarado.
ORDEN_SEV = {"Crítica": 0, "Grave": 1, "Moderada": 2, "Baja": 3,
             "Sin clasificación": 4, "no_afectado": 5}
raw["_grupo"] = [raiz(i) for i in range(N0)]
raw["_o"] = raw["Nivel de afectación"].map(ORDEN_SEV).fillna(9)
R = raw.sort_values("_o").drop_duplicates("_grupo", keep="first").copy()
DUPS = N0 - len(R)

R["_mun"] = R.Municipio.map(nmun)
T = R[R["Actividad económica/sector"].isin(SEC_TURISMO)].copy()
P = T[T._mun.isin(PRIORIZADOS)].copy()

# ═════════════════════════════════════════════════════════════════════════
# 2 · MARCA DE RNT
# ═════════════════════════════════════════════════════════════════════════
rnt = pd.read_excel(RNT, sheet_name="Data")
V = rnt[rnt.ANO == ANO_VIGENTE].drop_duplicates("CODIGO_RNT").copy()
V["_mun"] = V.MUNICIPIO.map(nmun)
V["_emp"] = V.RAZON_SOCIAL_ESTABLECIMIENTO.map(norm_emp)

exacto = defaultdict(dict)     # municipio -> nombre -> (categoría, código)
tokens = defaultdict(list)     # municipio -> [(conjunto, categoría, código)]
for r in V.itertuples():
    if not util(r._emp):
        continue
    exacto[r._mun][r._emp] = (r.CATEGORIA, r.CODIGO_RNT)
    tokens[r._mun].append((set(r._emp.split()), r.CATEGORIA, r.CODIGO_RNT))


def marcar(nombre, municipio):
    """(marca, categoría RNT, código RNT). Dos pasadas: exacta y por palabras."""
    if not util(nombre):
        return "Nombre no utilizable", "", ""
    hit = exacto[municipio].get(nombre)
    if hit:
        return "Sí (exacta)", hit[0], hit[1]
    t = set(nombre.split())
    mejor, cat, cod = 0.0, "", ""
    for s, c, k in tokens[municipio]:
        u = len(t | s)
        if not u:
            continue
        j = len(t & s) / u
        if j > mejor:
            mejor, cat, cod = j, c, k
    if mejor >= 0.75:
        return "Sí (probable)", cat, cod
    return "No se encontró", "", ""


marcas = [marcar(r._emp, r._mun) for r in P.itertuples()]
P["RNT"] = [m[0] for m in marcas]
P["Categoría RNT"] = [m[1] for m in marcas]
P["Código RNT"] = [m[2] for m in marcas]

# ═════════════════════════════════════════════════════════════════════════
# 3 · MARCA DE PERSONA NATURAL
# ═════════════════════════════════════════════════════════════════════════
# Muchos reportes vienen de personas naturales y escriben su propio nombre en
# el campo «Empresa». Esas filas requieren tratamiento aparte bajo la Ley 1581
# antes de circular el listado. Es un tamiz, no un veredicto: conviene
# revisarlas a mano.
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
    "COMERCIALIZADORA",
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


def parece_persona(nombre):
    p = [w for w in nombre.split() if len(w) > 2]
    if len(p) < 2 or any(w in COMERCIAL for w in p):
        return False
    return any(w in PERSONALES for w in p)


P["Revisar Ley 1581"] = ["Sí" if parece_persona(e) else "" for e in P._emp]

# ═════════════════════════════════════════════════════════════════════════
# 4 · SALIDA
# ═════════════════════════════════════════════════════════════════════════
COLS = {
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

resumen, hojas = [], {}
for k in PRIORIZADOS:
    g = P[P._mun == k].sort_values(["_o", "Empresa"])
    h = g[list(COLS)].rename(columns=COLS)
    h.insert(0, "#", range(1, len(g) + 1))
    for c in ["RNT", "Categoría RNT", "Código RNT", "Revisar Ley 1581"]:
        h[c] = g[c].values
    hojas[BONITO[k]] = h
    c = g.RNT.value_counts()
    resumen.append({
        "Municipio": BONITO[k],
        "Negocios turísticos afectados": len(g),
        "Prestadores con RNT vigente en el municipio": int((V._mun == k).sum()),
        "Aparece en RNT (exacta)": int(c.get("Sí (exacta)", 0)),
        "Aparece en RNT (probable)": int(c.get("Sí (probable)", 0)),
        "No se encontró en RNT": int(c.get("No se encontró", 0)),
        "Nombre no utilizable": int(c.get("Nombre no utilizable", 0)),
        "Crítica o grave": int(g["Nivel de afectación"].isin(["Crítica", "Grave"]).sum()),
        "No puede operar": int((g["Continuidad operativa"] == "No puede operar").sum()),
        "Revisar Ley 1581": int((g["Revisar Ley 1581"] == "Sí").sum()),
    })

RES = pd.DataFrame(resumen)
RES.loc[len(RES)] = ["TOTAL"] + [RES[c].sum() for c in RES.columns[1:]]

NOTAS = pd.DataFrame({"Nota": [
    "USO INTERNO. Contiene razón social de establecimientos afectados.",
    "",
    "Corte del censo: 1 de septiembre de 2026.",
    f"Base: {N0:,} reportes recibidos → {len(R):,} establecimientos únicos "
    f"({DUPS:,} dobles notificaciones retiradas).".replace(",", "."),
    f"Grupos con patrón de gestor detectados y NO fusionados: {gestores}.",
    f"RNT vigente: corte {ANO_VIGENTE}, {len(V):,} prestadores.".replace(",", "."),
    "Cadena de valor del turismo: sectores «Alojamiento y servicios de comida» y "
    "«Transporte y almacenamiento» del censo.",
    "",
    "COLUMNA RNT — dice si el nombre APARECE en el registro, no si el negocio lo tiene:",
    "  Sí (exacta)            el nombre normalizado coincide carácter por carácter",
    "  Sí (probable)          coinciden tres cuartas partes o más de las palabras; verificar",
    "  No se encontró         sin coincidencia. VERIFICAR: no prueba que sea informal",
    "  Nombre no utilizable   la razón social es genérica o demasiado corta",
    "",
    "El RNT no trae NIT, así que la única llave posible es la razón social más el "
    "municipio. En todo el departamento el cruce empareja 174 de 1.703 reportes.",
    "Más de la mitad del RNT son viviendas turísticas, registradas con nombres que no "
    "corresponden a un nombre comercial.",
    "",
    "COLUMNA REVISAR LEY 1581 — la razón social parece ser el nombre de una persona "
    "natural. Requiere tratamiento aparte antes de circular el listado.",
    "",
    "NO se incluyen nombre de la persona, documento, teléfono, correo, NIT, dirección "
    "ni barrio. Esos campos se leen solo para detectar duplicados.",
]})

with pd.ExcelWriter(OUT, engine="openpyxl") as w:
    NOTAS.to_excel(w, sheet_name="Método y advertencias", index=False)
    RES.to_excel(w, sheet_name="Resumen", index=False)
    for nombre, h in hojas.items():
        h.to_excel(w, sheet_name=nombre[:31], index=False)
    for ws in w.book.worksheets:
        for col in ws.columns:
            ancho = max((len(str(c.value)) for c in col if c.value), default=10)
            ws.column_dimensions[col[0].column_letter].width = min(max(ancho + 2, 11), 58)
        ws.freeze_panes = "A2"

mil = lambda x: f"{x:,}".replace(",", ".")
print(f"reportes {mil(N0)} → únicos {mil(len(R))} ({mil(DUPS)} duplicados, "
      f"{gestores} grupos de gestor no fusionados)")
print(f"turismo en el departamento: {mil(len(T))}")
print(f"escrito: {OUT}\n")
print(RES.to_string(index=False))
