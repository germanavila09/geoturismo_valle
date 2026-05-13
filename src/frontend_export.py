import json
from datetime import datetime
from pathlib import Path

import pandas as pd


FIELD_CANDIDATES = {
    "municipio": ["municipio", "nombre_municipio", "mpio", "ciudad"],
    "anio": ["anio", "ano", "year"],
    "visitantes": ["visitantes", "turistas", "visitas"],
    "gasto": ["gasto_estimado", "gasto", "derrama_economica"],
    "accesibilidad": ["accesibilidad", "indice_accesibilidad"],
    "oportunidad": ["indice_oportunidad_turistica", "oportunidad", "indice_oportunidad"],
    "lat": ["lat", "latitude", "latitud"],
    "lng": ["lng", "lon", "long", "longitude", "longitud"],
    "region": ["region", "subregion", "zona"],
    "atractivo": ["atractivo", "atractivo_principal", "nombre", "categoria", "tipo_turismo"],
    "tipo_turismo": ["tipo_turismo", "tipo", "categoria"],
    "tipo_secundario": ["tipo_secundario", "subtipo", "categoria_secundaria"],
    "actividades": ["actividades", "actividad"],
    "altitud": ["altitud", "altura"],
    "temperatura": ["temperatura", "clima"],
    "descripcion": ["descripcion", "description"],
    "costo": ["costo_entrada", "costo", "precio"],
    "fuente": ["fuente", "source"],
}


def _find_column(df, key):
    lower_map = {str(col).lower(): col for col in df.columns}
    for candidate in FIELD_CANDIDATES[key]:
        if candidate in lower_map:
            return lower_map[candidate]
    return None


def _find_municipality_column(df):
    if df is None or df.empty:
        return None
    candidates = [
        "mpio_cnmbr",
        "MPIO_CNMBR",
        "nom_mpio",
        "nombre_mun",
        "nombre_municipio",
        "municipio",
        "nombre",
        "mpio",
        "nam",
        "mpio_cnmbre",
    ]
    lower_map = {str(col).lower(): col for col in df.columns}
    for candidate in candidates:
        if candidate in lower_map:
            return lower_map[candidate]
    for col in df.columns:
        lowered = str(col).lower()
        if "mun" in lowered or "nombre" in lowered:
            return col
    return None


def _normalizar_municipio(value):
    return str(value).strip().title()


def _normalizar_texto(value, fallback="Sin dato"):
    if pd.isna(value):
        return fallback
    text = str(value).strip()
    return text if text else fallback


def _normalizar_clave(value):
    text = _normalizar_texto(value, "")
    replacements = str.maketrans("ÁÉÍÓÚÜÑáéíóúüñ", "AEIOUUNaeiouun")
    key = text.translate(replacements).upper().strip()
    aliases = {
        "SANTIAGO DE CALI": "CALI",
        "GUADALAJARA DE BUGA": "BUGA",
        "GUADALAJARA BUGA": "BUGA",
        "CALIMA": "CALIMA EL DARIEN",
        "EL DARIEN": "CALIMA EL DARIEN",
        "CALIMA DARIEN": "CALIMA EL DARIEN",
    }
    return aliases.get(key, key)


def _serie_texto(grupo, col, fallback="Sin dato"):
    if not col:
        return fallback
    valores = grupo[col].dropna().astype(str).str.strip()
    valores = valores[valores != ""]
    return valores.iloc[-1] if not valores.empty else fallback


def _numeric_series(grupo, col):
    if not col:
        return pd.Series(dtype=float)
    return pd.to_numeric(grupo[col], errors="coerce").dropna()


def _numeric_value(value):
    value = pd.to_numeric(value, errors="coerce")
    if pd.isna(value):
        return None
    return float(value)


def _point_from_geometry(row):
    geom = row.get("geometry", None)
    if geom is None:
        geom = row.get("geom", None)
    if geom is None or pd.isna(geom):
        return None, None
    try:
        point = geom.centroid
        return float(point.y), float(point.x)
    except Exception:
        return None, None


def _normalizar_serie(serie):
    serie = pd.to_numeric(serie, errors="coerce").fillna(0)
    rango = serie.max() - serie.min()
    if rango == 0:
        return pd.Series([1 if value > 0 else 0 for value in serie], index=serie.index)
    return (serie - serie.min()) / rango


def _centroides(gdf):
    if not hasattr(gdf, "geometry") or gdf.empty:
        return {}
    data = gdf.copy()
    try:
        centroids = data.geometry.to_crs(4326).centroid
    except Exception:
        centroids = data.geometry.centroid

    municipio_col = _find_column(data, "municipio")
    if not municipio_col:
        return {}

    salida = {}
    for municipio, geom in zip(data[municipio_col], centroids):
        if geom is None or geom.is_empty:
            continue
        salida[_normalizar_municipio(municipio)] = {"lat": float(geom.y), "lng": float(geom.x)}
    return salida


def _atractivos_por_municipio(atractivos):
    if atractivos is None or atractivos.empty:
        return {}

    municipio_col = _find_column(atractivos, "municipio")
    atractivo_col = _find_column(atractivos, "atractivo")
    if not municipio_col or not atractivo_col:
        return {}

    salida = {}
    for municipio, grupo in atractivos.groupby(municipio_col):
        valores = (
            grupo[atractivo_col]
            .dropna()
            .astype(str)
            .str.strip()
            .replace("", pd.NA)
            .dropna()
            .unique()
            .tolist()
        )
        if valores:
            salida[_normalizar_municipio(municipio)] = ", ".join(valores[:3])
    return salida


def construir_payload_atractivos(atractivos):
    if atractivos is None or atractivos.empty:
        return []

    data = atractivos.copy()
    cols = {
        key: _find_column(data, key)
        for key in [
            "municipio",
            "atractivo",
            "tipo_turismo",
            "tipo_secundario",
            "actividades",
            "altitud",
            "temperatura",
            "descripcion",
            "costo",
            "fuente",
            "lat",
            "lng",
        ]
    }
    if not cols["municipio"]:
        return []

    centroides = _centroides(data)
    payload = []
    for idx, row in data.iterrows():
        municipio = _normalizar_municipio(row[cols["municipio"]])
        lat = _numeric_value(row[cols["lat"]]) if cols["lat"] else None
        lng = _numeric_value(row[cols["lng"]]) if cols["lng"] else None

        if (lat is None or lng is None) and municipio in centroides:
            lat = centroides[municipio]["lat"]
            lng = centroides[municipio]["lng"]

        if lat is None or lng is None:
            lat, lng = _point_from_geometry(row)

        if lat is None or lng is None:
            continue

        payload.append(
            {
                "id": int(row["id"]) if "id" in data.columns and pd.notna(row["id"]) else int(idx),
                "municipio": municipio,
                "nombre": _normalizar_texto(row[cols["atractivo"]], "Atractivo turistico") if cols["atractivo"] else "Atractivo turistico",
                "tipo_turismo": _normalizar_texto(row[cols["tipo_turismo"]], "Sin clasificar") if cols["tipo_turismo"] else "Sin clasificar",
                "tipo_secundario": _normalizar_texto(row[cols["tipo_secundario"]], "") if cols["tipo_secundario"] else "",
                "actividades": _normalizar_texto(row[cols["actividades"]], "") if cols["actividades"] else "",
                "altitud": _normalizar_texto(row[cols["altitud"]], "") if cols["altitud"] else "",
                "temperatura": _normalizar_texto(row[cols["temperatura"]], "") if cols["temperatura"] else "",
                "descripcion": _normalizar_texto(row[cols["descripcion"]], "") if cols["descripcion"] else "",
                "costo_entrada": _normalizar_texto(row[cols["costo"]], "") if cols["costo"] else "",
                "fuente": _normalizar_texto(row[cols["fuente"]], "") if cols["fuente"] else "",
                "lat": float(lat),
                "lng": float(lng),
            }
        )
    return payload


def _agregar_municipios_desde_atractivos(atractivos, anio=None):
    payload_atractivos = construir_payload_atractivos(atractivos)
    if not payload_atractivos:
        return []

    anio = int(anio or datetime.now().year)
    data = pd.DataFrame(payload_atractivos)
    conteos = data.groupby("municipio").size().rename("atractivos")
    diversidad = data.groupby("municipio")["tipo_turismo"].nunique().rename("diversidad")
    base = pd.concat([conteos, diversidad], axis=1).reset_index()
    base["atractivos_norm"] = _normalizar_serie(base["atractivos"])
    base["diversidad_norm"] = _normalizar_serie(base["diversidad"])
    base["oportunidad"] = (base["atractivos_norm"] * 0.65 + base["diversidad_norm"] * 0.35).round(4)

    payload = []
    for _, row in base.iterrows():
        municipio = row["municipio"]
        grupo = data[data["municipio"] == municipio]
        tipo_predominante = grupo["tipo_turismo"].mode().iloc[0] if not grupo["tipo_turismo"].mode().empty else "Sin clasificar"
        tipos = sorted(grupo["tipo_turismo"].dropna().unique().tolist())
        top_nombres = grupo["nombre"].dropna().astype(str).head(3).tolist()
        payload.append(
            {
                "municipio": municipio,
                "lat": float(grupo["lat"].mean()),
                "lng": float(grupo["lng"].mean()),
                "region": "Valle del Cauca",
                "atractivo": ", ".join(top_nombres) if top_nombres else tipo_predominante,
                "tipo_predominante": tipo_predominante,
                "tipos_turismo": tipos,
                "visitantes": {anio: float(row["atractivos"])},
                "gasto": {anio: 0},
                "accesibilidad": {anio: float(row["diversidad"])},
                "oportunidad": {anio: float(row["oportunidad"])},
                "atractivos": {anio: float(row["atractivos"])},
                "diversidad": {anio: float(row["diversidad"])},
            }
        )
    return payload


def construir_resumen_tipos(atractivos):
    payload_atractivos = construir_payload_atractivos(atractivos)
    if not payload_atractivos:
        return []

    data = pd.DataFrame(payload_atractivos)
    resumen = (
        data.groupby("tipo_turismo")
        .agg(atractivos=("id", "count"), municipios=("municipio", "nunique"))
        .reset_index()
        .sort_values(["atractivos", "municipios"], ascending=False)
    )
    total = resumen["atractivos"].sum()
    resumen["participacion"] = (resumen["atractivos"] / total * 100).round(1) if total else 0
    return resumen.to_dict(orient="records")


def construir_geojson_municipios(municipios):
    if municipios is None or municipios.empty or "geom_geojson" not in municipios.columns:
        return {"type": "FeatureCollection", "features": []}

    nombre_col = _find_municipality_column(municipios)
    features = []
    for _, row in municipios.iterrows():
        raw_geom = row.get("geom_geojson")
        if pd.isna(raw_geom) or not raw_geom:
            continue
        try:
            geometry = json.loads(raw_geom) if isinstance(raw_geom, str) else raw_geom
        except Exception:
            continue

        nombre = _normalizar_texto(row[nombre_col], "Municipio") if nombre_col else "Municipio"
        properties = {
            "municipio": _normalizar_municipio(nombre),
            "municipio_key": _normalizar_clave(nombre),
        }
        for col in municipios.columns:
            if col in {"geom", "geometry", "geom_geojson"}:
                continue
            value = row[col]
            if pd.isna(value):
                continue
            if isinstance(value, (int, float, str, bool)):
                properties[str(col)] = value

        features.append({"type": "Feature", "properties": properties, "geometry": geometry})

    return {"type": "FeatureCollection", "features": features}


def construir_payload_geovisor(df, atractivos=None):
    if df is None or df.empty:
        return _agregar_municipios_desde_atractivos(atractivos)

    data = df.copy()
    municipio_col = _find_column(data, "municipio")
    anio_col = _find_column(data, "anio")
    if not municipio_col or not anio_col:
        return _agregar_municipios_desde_atractivos(data if atractivos is None else atractivos)

    cols = {key: _find_column(data, key) for key in ["visitantes", "gasto", "accesibilidad", "oportunidad", "lat", "lng", "region", "atractivo", "tipo_turismo"]}
    centroides = _centroides(data)
    atractivos_municipio = _atractivos_por_municipio(atractivos)
    years = sorted(pd.to_numeric(data[anio_col], errors="coerce").dropna().astype(int).unique().tolist())

    payload = []
    for municipio, grupo in data.groupby(municipio_col):
        nombre = _normalizar_municipio(municipio)
        item = {
            "municipio": nombre,
            "lat": None,
            "lng": None,
            "region": "Valle del Cauca",
            "atractivo": atractivos_municipio.get(nombre, "Oferta turistica territorial"),
            "visitantes": {},
            "gasto": {},
            "accesibilidad": {},
            "oportunidad": {},
            "atractivos": {},
            "diversidad": {},
        }

        if cols["region"]:
            regiones = grupo[cols["region"]].dropna().astype(str).str.strip()
            if not regiones.empty:
                item["region"] = regiones.iloc[-1]

        if cols["atractivo"]:
            atractivos_propios = grupo[cols["atractivo"]].dropna().astype(str).str.strip()
            if not atractivos_propios.empty:
                item["atractivo"] = atractivos_propios.iloc[-1]

        if cols["tipo_turismo"]:
            tipo = _serie_texto(grupo, cols["tipo_turismo"], "")
            if tipo:
                item["tipo_predominante"] = tipo

        if cols["lat"] and cols["lng"]:
            latitudes = pd.to_numeric(grupo[cols["lat"]], errors="coerce").dropna()
            longitudes = pd.to_numeric(grupo[cols["lng"]], errors="coerce").dropna()
            if not latitudes.empty and not longitudes.empty:
                item["lat"] = float(latitudes.iloc[-1])
                item["lng"] = float(longitudes.iloc[-1])
        elif nombre in centroides:
            item.update(centroides[nombre])

        for year in years:
            year_group = grupo[pd.to_numeric(grupo[anio_col], errors="coerce") == year]
            for target, source in [
                ("visitantes", cols["visitantes"]),
                ("gasto", cols["gasto"]),
                ("accesibilidad", cols["accesibilidad"]),
                ("oportunidad", cols["oportunidad"]),
            ]:
                if source and not year_group.empty:
                    item[target][year] = float(pd.to_numeric(year_group[source], errors="coerce").fillna(0).mean())
                else:
                    item[target][year] = 0
            item["atractivos"][year] = item["visitantes"][year]
            item["diversidad"][year] = item["accesibilidad"][year]

        if item["lat"] is not None and item["lng"] is not None:
            payload.append(item)

    return payload or _agregar_municipios_desde_atractivos(atractivos)


def exportar_geovisor_js(df, atractivos, ruta_frontend, municipios=None, nombre_archivo="geoturismo-data.js"):
    ruta = Path(ruta_frontend)
    ruta.mkdir(parents=True, exist_ok=True)
    payload = construir_payload_geovisor(df, atractivos)
    payload_atractivos = construir_payload_atractivos(atractivos)
    resumen_tipos = construir_resumen_tipos(atractivos)
    municipios_geojson = construir_geojson_municipios(municipios)
    destino = ruta / nombre_archivo
    destino_municipios = ruta / "geoturismo-municipios.js"
    contenido = (
        "window.GEOTURISMO_DATA = "
        + json.dumps(payload, ensure_ascii=False, indent=2)
        + ";\nwindow.GEOTURISMO_ATTRACTIONS = "
        + json.dumps(payload_atractivos, ensure_ascii=False, indent=2)
        + ";\nwindow.GEOTURISMO_TYPE_SUMMARY = "
        + json.dumps(resumen_tipos, ensure_ascii=False, indent=2)
        + ";\n"
    )
    destino.write_text(contenido, encoding="utf-8")
    destino_municipios.write_text(
        "window.GEOTURISMO_MUNICIPALITIES = "
        + json.dumps(municipios_geojson, ensure_ascii=False, indent=2)
        + ";\n",
        encoding="utf-8",
    )
    return {
        "data": destino,
        "municipios": destino_municipios,
        "municipios_count": len(payload),
        "atractivos_count": len(payload_atractivos),
        "atractivos_db_count": 0 if atractivos is None else len(atractivos),
        "tipos_count": len(resumen_tipos),
        "poligonos_count": len(municipios_geojson.get("features", [])),
    }
