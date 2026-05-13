import pandas as pd

from src.transform import calcular_indice_oportunidad, construir_pivot, limpiar_datos
from src.frontend_export import construir_payload_geovisor


def test_limpieza_normaliza_municipio():
    df = pd.DataFrame({"municipio": [" cali "], "anio": ["2025"], "visitantes": ["10"]})
    limpio = limpiar_datos(df)
    assert limpio.loc[0, "municipio"] == "CALI"
    assert limpio.loc[0, "visitantes"] == 10


def test_pivot_visitantes():
    df = pd.DataFrame({"municipio": ["CALI"], "anio": [2025], "visitantes": [100]})
    pivot = construir_pivot(df)
    assert pivot.loc["CALI", 2025] == 100


def test_indice_oportunidad_existe():
    df = pd.DataFrame({"municipio": ["CALI"], "visitantes": [100], "atractivos": [5]})
    result = calcular_indice_oportunidad(df)
    assert "indice_oportunidad_turistica" in result.columns


def test_payload_geovisor_agrupa_por_municipio_y_anio():
    df = pd.DataFrame(
        {
            "municipio": ["CALI", "CALI"],
            "anio": [2025, 2026],
            "visitantes": [100, 120],
            "gasto_estimado": [10, 12],
            "indice_oportunidad_turistica": [0.6, 0.7],
            "lat": [3.45, 3.45],
            "lng": [-76.53, -76.53],
        }
    )
    payload = construir_payload_geovisor(df)
    assert payload[0]["municipio"] == "Cali"
    assert payload[0]["visitantes"][2026] == 120
