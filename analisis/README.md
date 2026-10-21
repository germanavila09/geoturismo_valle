# Análisis e informes de turismo

Esta carpeta reúne lo que antes vivía en `observatorios/turismo` (fusionado en GeoTurismo el 2026-10-19).
Son análisis con **datos reales**: el RNT del Valle, los reportes de la emergencia del sismo del 10 de
agosto de 2026 y el consolidado de gestión del riesgo, para los 42 municipios del Valle del Cauca.

| Carpeta | Qué contiene | Entregable final (en `../informes/`) |
| --- | --- | --- |
| `impacto_sismo/analisis/` | Depuración de reportes, cruce con el observatorio, prioridad por municipio | Informe sector turismo (2026-09-01) |
| `impacto_sismo/impacto_economico/` | Índice de afectación económica (IAE), duplicados, mapas | Informe impacto económico GAR (docx + pdf) |
| `impacto_sismo/orientacion_ayuda/` | Brecha necesidad–ayuda, ICM, rutas de entrega | Informe ejecutivo orientación de ayuda v4 |
| `impacto_sismo/cadena_valor_rnt/` | Cruce RNT × reportes, perfil del sector, priorizados | Afectación RNT y perfil del sector (2026-09-21), cruce RNT (xlsx) |
| `impacto_sismo/figuras/` y CSV sueltos | Figuras y tablas municipales compartidas | — |
| `agroturismo_icetex/` | Línea base de agroturismo para ICETEX | Línea base agroturismo ICETEX (2026-10-19) |

Las versiones anteriores de los entregables (v1–v3, borradores) están en `../archivo/turismo_versiones/`, fuera de git.

## Fuentes y rutas

`rutas.py` reemplaza las rutas fijas de la sesión original (`/sessions/.../mnt/...`). Las fuentes se buscan en
`TURISMO_FUENTES`, luego en `../fuentes/turismo/` y por último en `observatorios/georiesgo/docs/`.

```bash
python analisis/rutas.py      # dice qué fuentes encuentra y cuáles faltan
```

- `rnt valle.xlsx` y `reportes_emergencia_2026-09-01.xlsx`: en `georiesgo/docs/`.
- `reportes_emergencia_2026-09-03.xlsx`: **falta**. La usan `cruce_rnt_0903.py` y `turismo_mun_0903.py`; cópiala a `fuentes/turismo/`.
- `municipios_valle.geojson`: se lee de `georiesgo/fuentes/`.

Los scripts escriben sus salidas (json, csv, png) en la carpeta desde donde se ejecutan: córrelos desde su propia carpeta.

## Siguiente paso

Reemplazar los valores escritos a mano en `scripts/seed_db.py` por indicadores calculados desde el RNT
(`impacto_sismo/cadena_valor_rnt/turismo_mun*.py`), para que el dashboard y el chatbot usen datos reales de los 42 municipios.
