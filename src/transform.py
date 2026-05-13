import pandas as pd


def limpiar_datos(gdf):
    df = gdf.copy()
    if "municipio" in df.columns:
        df["municipio"] = df["municipio"].astype(str).str.upper().str.strip()
    if "anio" in df.columns:
        df["anio"] = pd.to_numeric(df["anio"], errors="coerce").astype("Int64")

    numericas = [
        "visitantes",
        "atractivos",
        "ocupacion_hotelera",
        "gasto_estimado",
        "indice_seguridad",
        "tiempo_acceso_min",
    ]
    for col in numericas:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df


def construir_pivot(df, valor="visitantes"):
    if not {"municipio", "anio", valor}.issubset(df.columns):
        return pd.DataFrame()
    return df.pivot_table(
        index="municipio",
        columns="anio",
        values=valor,
        aggfunc="sum",
        fill_value=0,
    )


def calcular_indice_oportunidad(df):
    data = df.copy()
    defaults = {
        "visitantes": 0,
        "atractivos": 0,
        "ocupacion_hotelera": 0,
        "gasto_estimado": 0,
        "indice_seguridad": 0,
        "tiempo_acceso_min": 0,
    }
    for col, default in defaults.items():
        if col not in data.columns:
            data[col] = default

    def norm(col):
        serie = data[col].astype(float)
        rango = serie.max() - serie.min()
        if rango == 0:
            return serie * 0
        return (serie - serie.min()) / rango

    accesibilidad = 1 - norm("tiempo_acceso_min")
    data["indice_oportunidad_turistica"] = (
        norm("visitantes") * 0.25
        + norm("atractivos") * 0.20
        + norm("ocupacion_hotelera") * 0.15
        + norm("gasto_estimado") * 0.15
        + norm("indice_seguridad") * 0.15
        + accesibilidad * 0.10
    ).round(4)
    return data


def calcular_priorizacion(df):
    data = calcular_indice_oportunidad(df)
    if "municipio" not in data.columns:
        return pd.DataFrame()
    columnas_num = [
        "visitantes",
        "atractivos",
        "ocupacion_hotelera",
        "gasto_estimado",
        "indice_oportunidad_turistica",
    ]
    columnas_num = [c for c in columnas_num if c in data.columns]
    resultado = (
        data.groupby("municipio", as_index=False)[columnas_num]
        .mean(numeric_only=True)
        .sort_values("indice_oportunidad_turistica", ascending=False)
    )
    # Conserva tipo_turismo_predominante si está disponible
    if "tipo_turismo_predominante" in data.columns:
        tipo = (
            data.drop_duplicates("municipio")[["municipio", "tipo_turismo_predominante"]]
        )
        resultado = resultado.merge(tipo, on="municipio", how="left")
    return resultado


def calcular_distribucion_tipo_turismo(df_atractivos):
    """Distribución de atractivos por tipo y municipio.

    Recibe el DataFrame de atractivos_turisticos (con tipo_turismo).
    Retorna dos DataFrames:
        - global_dist: conteo y porcentaje por tipo_turismo
        - por_municipio: conteo por municipio × tipo_turismo (pivot)
    """
    if df_atractivos is None or df_atractivos.empty or "tipo_turismo" not in df_atractivos.columns:
        return pd.DataFrame(), pd.DataFrame()

    df = df_atractivos.copy()
    if "municipio" in df.columns:
        df["municipio"] = df["municipio"].astype(str).str.upper().str.strip()

    # Distribución global
    global_dist = (
        df.groupby("tipo_turismo", as_index=False)
        .size()
        .rename(columns={"size": "cantidad"})
        .sort_values("cantidad", ascending=False)
    )
    total = global_dist["cantidad"].sum()
    global_dist["porcentaje"] = (global_dist["cantidad"] / total * 100).round(1)

    # Distribución por municipio (pivot)
    por_municipio = pd.DataFrame()
    if "municipio" in df.columns:
        por_municipio = (
            df.groupby(["municipio", "tipo_turismo"])
            .size()
            .unstack(fill_value=0)
            .reset_index()
        )

    return global_dist, por_municipio


def calcular_indicadores_por_tipo(df_municipal):
    """Promedio de indicadores turísticos agrupados por tipo_turismo_predominante.

    Recibe turismo_municipal con tipo_turismo_predominante.
    Retorna un DataFrame con medias de visitantes, ocupación, etc. por tipo.
    """
    if "tipo_turismo_predominante" not in df_municipal.columns:
        return pd.DataFrame()

    metricas = [
        "visitantes",
        "atractivos",
        "ocupacion_hotelera",
        "gasto_estimado",
        "indice_seguridad",
    ]
    metricas = [m for m in metricas if m in df_municipal.columns]

    return (
        df_municipal.groupby("tipo_turismo_predominante")[metricas]
        .mean(numeric_only=True)
        .round(2)
        .sort_values("visitantes", ascending=False)
        .reset_index()
    )


def calcular_analisis_geoespacial_turismo(df_atractivos):
    """Resume concentracion territorial de atractivos por municipio y tipo."""
    if df_atractivos is None or df_atractivos.empty:
        return pd.DataFrame(), pd.DataFrame()

    required = {"municipio", "tipo_turismo"}
    if not required.issubset(df_atractivos.columns):
        return pd.DataFrame(), pd.DataFrame()

    df = df_atractivos.copy()
    df["municipio"] = df["municipio"].astype(str).str.upper().str.strip()
    df["tipo_turismo"] = df["tipo_turismo"].fillna("Sin clasificar").astype(str).str.strip()

    if "lat" not in df.columns or "lng" not in df.columns:
        if hasattr(df, "geometry"):
            try:
                puntos = df.geometry.to_crs(4326)
            except Exception:
                puntos = df.geometry
            df["lat"] = puntos.y
            df["lng"] = puntos.x

    resumen = (
        df.groupby(["municipio", "tipo_turismo"], as_index=False)
        .agg(
            atractivos=("tipo_turismo", "size"),
            lat_centro=("lat", "mean") if "lat" in df.columns else ("tipo_turismo", "size"),
            lng_centro=("lng", "mean") if "lng" in df.columns else ("tipo_turismo", "size"),
        )
        .sort_values(["municipio", "atractivos"], ascending=[True, False])
    )

    totales = (
        df.groupby("municipio", as_index=False)
        .agg(
            atractivos_total=("tipo_turismo", "size"),
            diversidad_tipos=("tipo_turismo", "nunique"),
        )
    )
    tipo_lider = resumen.drop_duplicates("municipio")[["municipio", "tipo_turismo"]].rename(
        columns={"tipo_turismo": "tipo_turismo_predominante"}
    )
    municipios = totales.merge(tipo_lider, on="municipio", how="left")
    resumen = resumen.merge(totales, on="municipio", how="left")
    resumen["participacion_municipal"] = (
        resumen["atractivos"] / resumen["atractivos_total"] * 100
    ).round(2)

    max_atractivos = municipios["atractivos_total"].max()
    max_diversidad = municipios["diversidad_tipos"].max()
    municipios["indice_potencial_inventario"] = (
        (municipios["atractivos_total"] / max_atractivos if max_atractivos else 0) * 0.65
        + (municipios["diversidad_tipos"] / max_diversidad if max_diversidad else 0) * 0.35
    ).round(4)

    return resumen, municipios.sort_values("indice_potencial_inventario", ascending=False)
