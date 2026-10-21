"""Perfil del sector turismo con la misma estructura del informe de la
Secretaría de Desarrollo Económico, Competitividad y Fomento del Empleo
(Consejo de Gobierno, 15 de septiembre de 2026).

QUÉ REPLICA
El informe departamental organiza la lectura en severidad · continuidad del
negocio · pérdidas · qué se dañó · qué se necesita · formalización. Aquí se
calculan esos mismos seis bloques, pero solo sobre la cadena de valor del
turismo y con la base depurada de doble notificación.

QUÉ AÑADE
El informe departamental llega hasta «Alojamiento, gastronomía y turismo» como
un solo renglón del 16 %. Este script abre ese renglón en tipos de negocio
—hoteles, restaurantes, cafeterías, transporte, agencias— leyendo la razón
social declarada.

LA TIPOLOGÍA ES UNA HEURÍSTICA, NO UN DATO
El formulario no pregunta qué tipo de negocio es. El tipo se infiere de
palabras clave en el nombre comercial: «Hotel Los Andes» → alojamiento. Los
nombres que no traen ninguna palabra reconocible quedan en «Sin clasificar»,
que se reporta siempre para que se vea cuánto del universo no se pudo tipificar.
"""
import json
import re
import unicodedata
import warnings
from collections import Counter

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# Se reutiliza la depuración de doble notificación y el universo de turismo.
_h = open("cruce_rnt_0903.py").read().split("# ── 3 · marca")[0]
_g = {}
exec(_h, _g)
T, R, V, N0, DUPS = _g["T"], _g["R"], _g["V"], _g["N0"], _g["DUPS"]


def sin_tildes(s):
    s = unicodedata.normalize("NFD", str(s).replace("�", "n").lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


# ── tipología de negocio ─────────────────────────────────────────────────
# El orden importa: la primera regla que coincide gana. Alojamiento va antes
# que gastronomía porque «Hotel Restaurante El Mirador» es, ante todo, un hotel.
# Los acentos llegan rotos desde el origen (Helader\ufffda), asi que las claves
# se escriben como raices SIN vocal acentuada: «helader» captura heladeria,
# heladeria y helader�a por igual.
TIPOS = [
    ("Alojamiento", [
        "hotel", "hostal", "hospedaje", "posada", "motel", "apartahotel",
        "aparta hotel", "alojamiento", "caban", "glamping", "camping",
        "hoster", "albergue", "residencias", "centro vacacional",
        "centro recreacional", "club campestre", "zona de camping",
        "finca turistica", "casa campestre", "villa turistica"]),
    ("Restaurantes y comidas", [
        "restaurante", "restaurant", "asader", "asados", "comidas", "comida",
        "cevicher", "ceviche", "parrilla", "pizzer", "pizza", "sazon",
        "fonda", "fogon", "marisquer", "mariscos", "piqueteadero", "chuzos",
        "empanad", "arepas", "almuerzo", "cocina", "gastro", "sushi",
        "burger", "bueguer", "hamburgues", "broaster", "pollo", "carnes",
        "fritanga", "buffet", "lechona", "sancocho", "salpicon", "salchi",
        "food", "foods", "cholado", "chorizo", "wok", "taco", "crepes",
        "pescader", "pescado", "delicias", "sabor", "sabrosur", "menu"]),
    ("Cafes, panaderias y heladerias", [
        "cafeter", "cafe ", " cafe", "coffee", "panader", "pasteler",
        "reposter", "helader", "helados", "fruter", "jugos", "postres",
        "chocolate", "bizcoch", "donas", "galleta", "tortas", "obleas",
        "salpicon de frutas", "yogur", "batidos"]),
    ("Bares y entretenimiento nocturno", [
        "bar ", " bar", "taber", "discotec", "licor", "estadero", "billar",
        "cantina", "rumba", "night", "estanquillo", "cerveceria", "cervecer",
        "cerveza", "musica en vivo", "karaoke", "lounge", "pub"]),
    ("Transporte de pasajeros", [
        "transporte", "transportes", "trasnporte", "taxi", "buses", "bus ",
        "flota", "chiva", "lancha", "embarcacion", "movilidad", "expreso",
        "rent a car", "alquiler de vehiculo", "automotor", "mototaxi"]),
    ("Agencias y operadores turisticos", [
        "agencia de viajes", "viajes", "turismo", "turistic", "tours",
        "tour ", "ecoturismo", "operador turistico", "guia de turismo",
        "travel", "avistamiento"]),
    ("Atractivos y recreacion", [
        "balneario", "piscina", "parque", "zoologico", "museo", "mirador",
        "reserva natural", "acuaparque", "termales", "ecoparque",
        "sendero", "botanico"]),
    ("Eventos y banquetes", [
        "eventos", "salon social", "recepciones", "banquetes", "catering",
        "casa de banquetes"]),
]

# Un nombre de persona natural no es un tipo de negocio: se separa para no
# inflar «Sin clasificar» con algo que en realidad si sabemos que es.
APELLIDOS = {
    "gomez", "rodriguez", "martinez", "lopez", "garcia", "perez", "sanchez",
    "ramirez", "torres", "florez", "vargas", "castro", "ruiz", "diaz",
    "moreno", "munoz", "rojas", "morales", "jimenez", "gutierrez", "alvarez",
    "mejia", "osorio", "salazar", "cardona", "arias", "giraldo", "ocampo",
    "zapata", "valencia", "montoya", "restrepo", "hurtado", "mosquera",
    "caicedo", "velasquez", "bedoya", "agudelo", "quintero", "henao",
    "castano", "loaiza", "benavides", "otalora", "urrea", "narvaez",
    "asprilla", "ibarguen", "lucumi", "urrutia", "gaviria", "hidalgo",
    "sandoval", "bello", "soto", "pino", "rivera", "villa", "osorio",
}
NOMBRES_PILA = {
    "jose", "juan", "luis", "carlos", "jorge", "maria", "ana", "luz",
    "martha", "sandra", "diego", "andres", "javier", "fernando", "ricardo",
    "oscar", "william", "jhon", "john", "jairo", "hernan", "german",
    "alexander", "claudia", "patricia", "liliana", "monica", "gloria",
    "nancy", "rosa", "carmen", "elena", "beatriz", "esperanza", "yenny",
    "yuli", "leidy", "dayana", "carolina", "paola", "sebastian", "edgar",
    "ruben", "dario", "julio", "cesar", "oswaldo", "gladys", "omaira",
    "vivian", "lizeth", "michell", "saray", "mauren", "jaime", "eduardo",
    "diana", "rodolfo", "piedad", "robinson", "leonisa", "jesus",
}


def es_persona(t):
    """Dos o mas palabras y al menos un apellido reconocible, o un nombre de
    pila seguido de apellido. Es conservador: ante la duda, no marca."""
    w = [x for x in t.split() if len(x) > 2]
    if len(w) < 2:
        return False
    ap = sum(1 for x in w if x in APELLIDOS)
    pi = sum(1 for x in w if x in NOMBRES_PILA)
    return ap >= 2 or (ap >= 1 and pi >= 1)


def tipo(nombre):
    if not nombre:
        return "Sin razón social"
    t = " " + sin_tildes(nombre) + " "
    for et, claves in TIPOS:
        if any(k in t for k in claves):
            return et
    if es_persona(t.strip()):
        return "Registrado a nombre de persona natural"
    return "Sin clasificar"


T["tipo"] = [tipo(e) for e in T.Empresa]
T["sector_censo"] = T["Actividad económica/sector"]

# ── qué se dañó ──────────────────────────────────────────────────────────
# Selección múltiple con acentos rotos en el origen; se normaliza y se
# agrupa en las mismas cuatro categorías que usa el informe departamental.
# OJO con la clave «venta»: está contenida dentro de «in-venta-rios», así que
# marcaba como pérdida de ventas todo lo que era pérdida de inventario. Se usa
# «ventas» en plural y el inventario se evalúa primero.
DANO = [
    ("Infraestructura, maquinaria o equipos", ["infraestructura", "maquinaria", "equipo"]),
    ("Inventarios o mercancías", ["inventario", "mercanc"]),
    ("Reducción de clientes, pedidos o ventas", ["cliente", "pedido", "ventas"]),
    ("Proveedores, logística o servicios públicos", ["proveedor", "logistic", "servicios publicos"]),
    ("Restricción de acceso al establecimiento", ["acceso"]),
]


def multiple(serie, cats):
    """Selección múltiple separada por «;». Cada opción marcada cuenta una sola
    vez y en la primera categoría que la reconoce: sin el corte por opción, una
    frase larga cae en varias categorías y los totales se inflan."""
    c = Counter()
    for x in serie.dropna():
        vistos = set()
        for parte in str(x).split(";"):
            t = sin_tildes(parte)
            for k, claves in cats:
                if any(cl in t for cl in claves) and k not in vistos:
                    c[k] += 1
                    vistos.add(k)
                    break
    return c


NEC = [("Capital de trabajo, inventarios o insumos", ["capital de trabajo", "inventario", "insumo"]),
       ("Reparar instalaciones, maquinaria o equipos", ["reparar", "maquinaria", "equipo", "instalacion"]),
       ("Recuperar clientes y ventas", ["cliente", "ventas"]),
       ("Facilitar trámites", ["tramite"]),
       ("Restablecer servicios o logística", ["logistica", "servicios"])]
APO = [("Capital semilla o no reembolsable", ["capital semilla", "no reembolsable"]),
       ("Alivio de obligaciones actuales", ["alivio", "obligacion"]),
       ("Nuevo crédito", ["credito", "financiacion"]),
       ("No requiere apoyo", ["no requiere", "ninguno"])]

SEV = ["Crítica", "Grave"]
PLO = {"Menos de $5 millones.": 0, "Entre $5 y $20 millones.": 5,
       "Más de $20 y hasta $100 millones.": 20, "Más de $100 millones.": 0}
ALTA = ["Más de $20 y hasta $100 millones.", "Más de $100 millones."]


def pct(a, b):
    return round(100 * a / b, 1) if b else None


def bloque(d):
    """Los seis bloques del informe departamental, sobre un subconjunto."""
    niv = d["Nivel de afectación"]
    cont = d["Continuidad operativa"].dropna()
    p = d["Pérdidas económicas"].dropna()
    e = d["Empleos afectados o en riesgo"].dropna()
    reg = d["Empresa registrada"].dropna()
    dan = d["Afectaciones al negocio"].dropna()
    nec = d["Principal necesidad"].dropna()
    apo = d["Apoyo financiero"].dropna()
    ab = int((p == "Más de $100 millones.").sum())
    return {
        "n": int(len(d)),
        # severidad
        "critica": int((niv == "Crítica").sum()),
        "grave": int((niv == "Grave").sum()),
        "moderada": int((niv == "Moderada").sum()),
        "baja": int((niv == "Baja").sum()),
        "no_afectado": int((niv == "no_afectado").sum()),
        "sin_clasif": int((niv == "Sin clasificación").sum()),
        "sev": int(niv.isin(SEV).sum()),
        "pct_sev": pct(int(niv.isin(SEV).sum()), len(d)),
        # el informe departamental calcula la severidad sobre los CLASIFICADOS
        "base_clasif": int((~niv.isin(["Sin clasificación"]) & niv.notna()).sum()),
        "pct_sev_clasif": pct(int(niv.isin(SEV).sum()),
                              int((~niv.isin(["Sin clasificación"]) & niv.notna()).sum())),
        # continuidad
        "base_cont": int(len(cont)),
        "normal": int((cont == "Sí, normalmente").sum()),
        "parcial": int((cont == "Sí, pero parcialmente").sum()),
        "no_opera": int((cont == "No puede operar").sum()),
        "pct_normal": pct(int((cont == "Sí, normalmente").sum()), len(cont)),
        "pct_parcial": pct(int((cont == "Sí, pero parcialmente").sum()), len(cont)),
        "pct_no_opera": pct(int((cont == "No puede operar").sum()), len(cont)),
        "pct_restriccion": pct(int((cont != "Sí, normalmente").sum()), len(cont)),
        # pérdidas
        "base_perd": int(len(p)),
        "perd_min": int(sum(PLO[x] for x in p) + 100 * ab),
        "perd_ab": ab,
        "pct_perd_alta": pct(int(p.isin(ALTA).sum()), len(p)),
        # empleo
        "base_empl": int(len(e)),
        "con_empleo": int((e != "Ninguno").sum()),
        "pct_empleo": pct(int((e != "Ninguno").sum()), len(e)),
        # formalización declarada
        "base_reg": int(len(reg)),
        "registrada": int((reg == "Sí").sum()),
        "pct_registrada": pct(int((reg == "Sí").sum()), len(reg)),
        # qué se dañó · qué necesita · qué apoyo
        "base_dano": int(len(dan)), "dano": dict(multiple(dan, DANO)),
        "base_nec": int(len(nec)), "nec": dict(multiple(nec, NEC)),
        "base_apo": int(len(apo)), "apo": dict(multiple(apo, APO)),
        # tamaño
        "tam": {k: int(v) for k, v in d["Tamaño de empresa"].value_counts().items()},
    }


res = {
    "corte": "2026-09-03",
    "fuente_marco": "Secretaría de Desarrollo Económico, Competitividad y Fomento "
                    "del Empleo · Consejo de Gobierno, 15 de septiembre de 2026",
    "censo": {"recibidos": int(N0), "dobles": int(DUPS), "unicos": int(len(R))},
    "turismo": bloque(T),
    "todos": bloque(R),
    "rnt_vigentes": int(len(V)),
}

# ── tipos de negocio ─────────────────────────────────────────────────────
orden = [t[0] for t in TIPOS] + ["Registrado a nombre de persona natural",
         "Sin clasificar", "Sin razón social"]
res["tipos"] = []
for t in orden:
    d = T[T.tipo == t]
    if not len(d):
        continue
    b = bloque(d)
    b["tipo"] = t
    b["pct_universo"] = pct(len(d), len(T))
    b["top_mun"] = [{"municipio": k.title(), "n": int(v)} for k, v in
                    d.zmun.value_counts().head(5).items()]
    res["tipos"].append(b)
res["tipos"].sort(key=lambda x: -x["n"])
# Base tipificable: los tipos reales, sin los dos cajones de «no se pudo».
NO_TIPO = {"Sin clasificar", "Sin razón social",
           "Registrado a nombre de persona natural"}
res["tipificables"] = [t for t in res["tipos"] if t["tipo"] not in NO_TIPO]
res["base_tipo"] = sum(t["n"] for t in res["tipificables"])
for t in res["tipificables"]:
    t["pct_tipificables"] = pct(t["n"], res["base_tipo"])
res["sin_tipificar"] = {t["tipo"]: t["n"] for t in res["tipos"] if t["tipo"] in NO_TIPO}

# ── contraste con las cifras publicadas por la Secretaría ────────────────
# Se transcriben para poder decir en qué difieren y por qué, no para
# reemplazarlas. La Secretaría no depura doble notificación y su corte es
# posterior (15 de septiembre).
res["secretaria"] = {
    "universo": 15817, "criticos": 3441, "sev": 8634, "pct_sev_clasif": 62.6,
    "base_clasif": 13793, "sin_operacion": 3583, "pct_no_opera": 28.4,
    "parcial": 5325, "pct_parcial": 42.2, "normal": 3721, "pct_normal": 29.5,
    "base_cont": 12629, "formalizadas_ccc": 11032, "pct_formal": 69.7,
    "turismo_pct": 16, "turismo_equiv": 2531,
    "nota": "Corte 15 de septiembre, sin depuración de doble notificación. "
            "El renglón de turismo es «Alojamiento, gastronomía y turismo», "
            "una agrupación más amplia que la cadena de valor usada aquí.",
}


def limpio(o):
    if isinstance(o, dict):
        return {k: limpio(v) for k, v in o.items()}
    if isinstance(o, list):
        return [limpio(v) for v in o]
    if isinstance(o, float) and np.isnan(o):
        return None
    return o


json.dump(limpio(res), open("perfil_turismo.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1, default=str)

TU = res["turismo"]
mil = lambda x: f"{x:,}".replace(",", ".")
c1 = lambda x: f"{x}".replace(".", ",")

print("=" * 78)
print(f"CADENA DE VALOR DEL TURISMO · {mil(TU['n'])} establecimientos · corte 3 sep")
print("=" * 78)
print("\nTIPO DE NEGOCIO")
print(f"{'tipo':38} {'n':>5} {'%':>6} {'crít/grav':>10} {'no opera':>9} {'$ piso':>8}")
for t in res["tipos"]:
    print(f"{t['tipo']:38} {t['n']:>5} {c1(t['pct_universo']):>5}% "
          f"{c1(t['pct_sev']):>9}% {c1(t['pct_no_opera'] or 0):>8}% {mil(t['perd_min']):>8}")

print("\nCONTINUIDAD DEL NEGOCIO  (base " + mil(TU["base_cont"]) + ")")
print(f"  opera normalmente    {TU['normal']:>5}  {c1(TU['pct_normal'])} %")
print(f"  opera parcialmente   {TU['parcial']:>5}  {c1(TU['pct_parcial'])} %")
print(f"  no puede operar      {TU['no_opera']:>5}  {c1(TU['pct_no_opera'])} %")
print(f"  con restricción      {TU['parcial'] + TU['no_opera']:>5}  {c1(TU['pct_restriccion'])} %")

print("\nQUÉ SE DAÑÓ  (base " + mil(TU["base_dano"]) + ", selección múltiple)")
for k, v in sorted(TU["dano"].items(), key=lambda x: -x[1]):
    print(f"  {v:>5}  {c1(pct(v, TU['base_dano'])):>5} %  {k}")

print("\nFORMALIZACIÓN DECLARADA  (base " + mil(TU["base_reg"]) + ")")
print(f"  declara estar registrada {TU['registrada']}  {c1(TU['pct_registrada'])} %")
print(f"  (la Secretaría reporta {res['secretaria']['pct_formal']} % formalizadas en "
      f"Cámara de Comercio para todo el departamento)")

print("\nCONTRASTE CON EL INFORME DE LA SECRETARÍA")
S = res["secretaria"]
TD = res["todos"]
print(f"{'':28} {'Secretaría':>12} {'esta base':>12}")
print(f"{'universo de empresas':28} {mil(S['universo']):>12} {mil(TD['n']):>12}")
print(f"{'% crítico o grave (clasif.)':28} {c1(S['pct_sev_clasif']):>11}% "
      f"{c1(TD['pct_sev_clasif']):>11}%")
print(f"{'% no puede operar':28} {c1(S['pct_no_opera']):>11}% {c1(TD['pct_no_opera']):>11}%")
print(f"{'% opera parcialmente':28} {c1(S['pct_parcial']):>11}% {c1(TD['pct_parcial']):>11}%")
print(f"{'% opera normalmente':28} {c1(S['pct_normal']):>11}% {c1(TD['pct_normal']):>11}%")
print(f"\nescrito: perfil_turismo.json")
