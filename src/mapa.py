from pathlib import Path

import folium
import pandas as pd


def _serializable_gdf(gdf):
    data = gdf.copy()
    for col in data.columns:
        if col == getattr(data, "geometry", None).name:
            continue
        if pd.api.types.is_datetime64_any_dtype(data[col]):
            data[col] = data[col].dt.strftime("%Y-%m-%dT%H:%M:%S")
        elif data[col].dtype == "object":
            data[col] = data[col].map(
                lambda value: value.isoformat() if hasattr(value, "isoformat") else value
            )
    return data


def generar_mapa_html(gdf, ruta_salida, columna="indice_oportunidad_turistica"):
    ruta = Path(ruta_salida)
    ruta.mkdir(parents=True, exist_ok=True)
    mapa = folium.Map(location=[3.45, -76.53], zoom_start=8, tiles="CartoDB positron")

    if hasattr(gdf, "geometry") and not gdf.empty:
        data = _serializable_gdf(gdf)
        folium.Choropleth(
            geo_data=data.to_json(),
            data=data,
            columns=["municipio", columna],
            key_on="feature.properties.municipio",
            fill_color="YlGnBu",
            fill_opacity=0.75,
            line_opacity=0.25,
            legend_name="Indice de oportunidad turistica",
        ).add_to(mapa)

        folium.GeoJson(
            data,
            name="Municipios",
            tooltip=folium.GeoJsonTooltip(
                fields=[field for field in ["municipio", columna] if field in gdf.columns],
                aliases=["Municipio", "Indice"],
            ),
        ).add_to(mapa)

    salida = ruta / "mapa_actual.html"
    mapa.save(salida)
    return salida
