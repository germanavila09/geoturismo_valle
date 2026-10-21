"""Datos leidos de las dos plataformas oficiales de la Gobernacion.

FUENTE 1 · Matriz GRD publica (SOCK2 / K2 Digital para la Gobernacion)
  https://sock2.k2digital.co/grd-publico
  Endpoint: /api/v1/public/grd-matriz/tablero
  Corte: 2026-09-02 14:04 UTC · 41 municipios (excluye Santiago de Cali)
  ICM = indice de criticidad municipal, tres ejes: impacto humano,
  vivienda y servicios, conectividad. Se acompana de un indice de
  vulnerabilidad estructural del municipio.

FUENTE 2 · Ruta de la Solidaridad (Valle Humanitario, Gobernacion)
  https://sigesi.valledelcauca.gov.co/valle-humanitario
  Corte: 2026-08-27 · entregas y toneladas efectivamente despachadas.

Los valores se transcriben literalmente. No se recalculan ni se corrigen:
si una cifra oficial parece inconsistente, se deja y se anota.
"""
import io

import pandas as pd

GRD = """municipio|codigo_dane|rank_icm|icm|icm_semaforo|eje_humano|eje_vivienda|eje_conectividad|vulnerabilidad|semaforo_vuln|fallecidos|heridos|viv_destruidas|viv_averiadas|poblacion_afectada|albergados|sin_agua|emprendimientos|perdidas_est|vias_cerradas|centros_com|sedes_edu|estudiantes|salud_pct
Trujillo|76828|1|86.4|Crítico|91.5|75.5|90|66.25|Alta|3|36|1157|1389|5904|7|0|30|2113000064|4|25|32|1938|20
Toro|76823|2|82.05|Crítico|92|68.49|77.5|66.25|Alta|2|31|700|1590|4603|48|0|42|719951210|0|7|22|1735|2
El Cairo|76246|3|77.83|Crítico|88.75|93.17|27.5|58.13|Alta|3|4|70|800|2683|55||13|161500000|6|0|20|1259|40
Roldanillo|76622|4|75.52|Crítico|65.75|85.5|85|47.5|Media-alta|2|14|2535|2537|5999|67|0|247|24358397789|2|0|40|3963|80
El Águila|76243|5|72.7|Crítico|91|90.67|0|50|Media-alta|1|25|419|891|2619|9|0|10|138500001|1|4|29|1083|100
Yotoco|76890|6|69.22|Crítico|51.75|84.49|90|51.25|Media-alta|0|14|808|1202|5395|39|400|47|2909837276|1|9|24|2393|70
Sevilla|76736|7|66.4|Crítico|78|53.01|57.5|46.88|Media-alta|3|58|623|2210|8260|20|0|142|3855810941|0|9|60|5994|5
La Unión|76400|8|65.9|Crítico|70.5|63.84|57.5|48.13|Media-alta|1|28|478|1933|6065|52|0|261|9247888101|6|11|25|5087|30
El Dovio|76250|9|63.53|Crítico|44.25|73.01|97.5|66.88|Alta|0|3|395|734|2978|6|0|117|799000004|0|13|79|1049|10
Versalles|76863|10|62.45|Crítico|60|89.83|27.5|37.5|Media-baja|0|18|145|346|2797|0|0|50|1088350815|0|5|13|864|30
Dagua|76233|11|59.17|Crítico|74.25|55.16|27.5|35.63|Media-baja|6|58|217|1717|7596|0|0|29|639967004|5|13|72|4713|30
Bolívar|76100|12|59.05|Alto|45|70.18|77.5|61.25|Alta|0|9|120|3238|3898|0|0|24|149400004|0|13|36|4115|20
Argelia|76054|13|58.4|Alto|51|91.33|27.5|62.5|Alta|0|3|977|280|3433|22|0|108|31969470365|0|16|17|420|60
Restrepo|76606|14|55.9|Alto|57|73|27.5|49.38|Media-alta|0|60|679|924|4723|29|492|78|3020401543|6|14|22|2528|10
Ulloa|76845|15|55.55|Alto|40.5|57.68|90|66.25|Alta|0|2|69|722|1256|10|0|30|465712250|2|1|11|720|10
Alcalá|76020|16|53.38|Alto|47.25|60.84|57.5|62.5|Alta|0|20|120|1432|2800|0||75|1716310435|6|5|4|4352|20
La Cumbre|76377|17|53.27|Alto|38.25|62.16|77.5|66.88|Alta|0|7|163|1199|2935|0|16500|13|469500200|0|16|22|3939|20
Zarzal|76895|18|52.97|Alto|70.75|40.33|27.5|42.5|Media-baja|2|75|143|1032|4326|0||235|3746637225|0|4|14|5002|10
Buenaventura|76109|19|52.8|Alto|72.5|55.17|0|51.88|Media-alta|27|476|954|9194|31518|70|0|180|10301182859|2|45|||45
Ansermanuevo|76041|20|48.45|Alto|27|78.17|57.5|56.88|Alta|0|0|196|1211|4310|30|21500|23|2040400125|6|7|42|4144|50
Tuluá|76834|21|39.8|Alto|46|17.66|57.5|31.25|Media-baja|3|67|27|3999|1484|0|0|79|1272502151|0|8|||6.67
La Victoria|76403|22|39.4|Medio|37.5|50.51|27.5|61.88|Alta|0|6|12|1550|1967|19|0|30|191903119|1|11|14|4830|40
Florida|76275|23|35.9|Medio|41|13|57.5|46.88|Media-alta|1|2|4|267|474|0|0|18|47300618|0|3|47|6831|5
Obando|76497|24|34.83|Medio|24.75|36.51|57.5|46.25|Media-baja|0|1|24|511|1844|0|0|22|124050600|1|1|20|3580|0
Calima|76126|25|34.55|Medio|0|48.49|100|25|Baja|6|74|676|616|3352|28||58|1031651282||9|||0
Riofrío|76616|26|34|Medio|0|56.66|85|21.25|Baja|1|3|480|600|3809||||||12|||
Caicedonia|76122|27|33.08|Medio|32.25|56.51|0|21.25|Baja|0|8|183|2367|4616|0|0|114|2595955666|0|16|25|1818|30
Bugalagrande|76113|28|32.8|Medio|40.5|41.82|0|36.88|Media-baja|0|30|125|877|2921|100|442|81|422558216|6|0|38|3287|0
Yumbo|76892|29|31.1|Medio|53.5|14.49|0|26.88|Baja|8|28|54|650|1135|30|2150|28|1132979696|0|14|||0
Vijes|76869|30|28.92|Medio|35.25|37.66|0|53.75|Media-alta|0|12|31|220|871|0|0|32|128755600|5|5|15|1796|10
Guacarí|76318|31|27.17|Medio|18.75|21|57.5|52.5|Media-alta|0|4|31|191|314|0|0|9|63800011|0|14|21|7493|10
Andalucía|76036|32|25|Bajo|16.5|37.5|27.5|46.88|Media-alta|0|0|77|1120|2216|0|0|48|492680003|6|13|16|2107|20
Cartago|76147|33|22.55|Bajo|18|26.83|27.5|20.63|Baja|0|30|40|801|970|0|145000|83|1933001627|6|17|||12.5
San Pedro|76670|34|22.45|Bajo|18|26.5|27.5|33.13|Media-baja|0|0|4|72|1659|0|9860|17|464705001|5|0|17|2210|0
Ginebra|76306|35|22|Bajo|19.5|22.5|27.5|50|Media-alta|0|2|37|91|352|0|0|2|55000000|0|1|22|6879|0
Jamundí|76364|36|18.53|Bajo|23.25|23|0|19.38|Baja|0|47|17|2682|4111|0||54|631069545|5|14|||10
Pradera|76563|37|16.55|Bajo|15|11.84|27.5|33.75|Media-baja|0|1|4|98|448|0|0|10|60233343|0|5|33|7240|0
El Cerrito|76248|38|11.38|Bajo|15.75|11.67|0|21.25|Baja|0|7|3|146|291|0|75900|4|15380000|6|13|33|5326|5
Candelaria|76130|39|10.55|Bajo|18|5.17|0|21.88|Baja|0|30|27|534|404|0|3195|4|10000000|3|1|28|14021|0
Palmira|76520|40|5.85|Bajo|7.5|7|0|25|Baja|0|0|2|1073|506|0|0|306|2228522159|1|5|||10
Buga|76111|41|4.7|Bajo|0|15.67|0|0|Baja|1|38|42|570|1074|0|0|12|45700502|0|20|||2.5"""

AYUDA = """municipio|entregas|zona|toneladas
Dagua|22|Pacífico|30
Sevilla|21|Norte|29
Yotoco|16|Centro|22
Restrepo|14|Centro|19
Trujillo|14|Centro|19
Argelia|13|Norte|18
Bolívar|13|Norte|18
Buenaventura|13|Pacífico|18
Calima|13|Centro|18
La Cumbre|13|Sur|18
Cartago|12|Norte|17
Riofrío|12|Centro|17
Roldanillo|12|Norte|17
Versalles|12|Norte|17
El Águila|11|Norte|15
La Unión|11|Norte|15
Ansermanuevo|10|Norte|14
Caicedonia|8|Norte|11
La Victoria|8|Norte|11
Alcalá|7|Norte|10
Bugalagrande|7|Centro|10
Obando|7|Norte|10
Palmira|7|Sur|10
Zarzal|7|Norte|10
Andalucía|6|Centro|8
Buga|6|Centro|8
Toro|6|Norte|8
Vijes|6|Centro|8
El Cairo|5|Norte|7
El Cerrito|5|Centro|7
Jamundí|5|Sur|7
Ulloa|5|Norte|7
Yumbo|5|Sur|7
El Dovio|4|Norte|6
San Pedro|4|Centro|6
Tuluá|4|Centro|6
Guacarí|3|Centro|4
Ginebra|2|Centro|3
Pradera|2|Sur|3
Candelaria|0|Sur|0
Florida|0|Sur|0"""

# Totales departamentales publicados, para citarlos sin recalcular.
GRD_KPI = {
    "fecha_corte": "2026-09-02", "municipios": 41, "excluye": "Santiago de Cali",
    "fallecidos": 70, "heridos": 1331, "personas_afectadas": 148916,
    "viviendas_averiadas": 53616, "viviendas_destruidas": 12868,
    "personas_albergadas": 641, "centros_comunitarios": 399,
    "personas_sin_agua": 275439, "estudiantes_afectados": 122716,
    "sedes_educativas": 913, "vias_cerradas": 92, "puentes_afectados": 22,
    "emprendimientos_afectados": 2765, "perdidas_estimadas": 112858967350,
    "icm_criticos": 11, "icm_altos": 10, "icm_medios": 10, "icm_bajos": 10,
    "icm_max": 86.4, "icm_promedio": 43.95, "ips_reportadas": 45,
    "salud_pct_promedio": 20.59, "nivel_alerta": "Roja",
    "fase": "Respuesta inmediata",
}
AYUDA_KPI = {
    "fecha_corte": "2026-08-27", "recibidas_t": 562, "distribuidas_t": 561,
    "despachos": 434, "mun_con_ayuda": 39, "mun_total": 41,
    "entregas_municipios": 351, "toneladas_municipios": 480,
    "ruta_municipios_pct": 72, "ruta_cartago_pct": 9, "ruta_otras_pct": 19,
    "pct_48h": 16, "entregas_48h": 57, "dia_pico": "17 de agosto",
    "entregas_dia_pico": 58, "dias_con_entrega": 16, "dias_totales": 17,
    "zonas_completas": 3, "zonas_totales": 4,
    "cali_unidades": 27245, "cali_entregas": 59,
    # composicion de lo entregado, en % del total
    "composicion": {"Aseo personal": 31, "Alimentos": 22,
                    "Protección y seguridad": 14, "Líquidos e hidratación": 13,
                    "Descanso y abrigo": 5, "Kits sin desagregar": 3, "Bebé": 3,
                    "Menaje y utensilios": 2, "Sin clasificar": 2, "Mascotas": 1,
                    "Ropa y calzado": 1, "Aseo del hogar": 1,
                    "Herramientas y materiales": 0.5, "Salud": 0.5},
}


def leer(txt):
    return pd.read_csv(io.StringIO(txt), sep="|")


if __name__ == "__main__":
    g, a = leer(GRD), leer(AYUDA)
    g.to_csv("grd_sock2.csv", index=False)
    a.to_csv("ayuda_ruta.csv", index=False)
    print(f"GRD {len(g)} municipios · AYUDA {len(a)} municipios")
    print(f"sin entregas: {list(a[a.entregas == 0].municipio)}")
    print(g.head(3).to_string())
