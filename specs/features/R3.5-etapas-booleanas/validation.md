# R3.5 — Validación

## Requisito → test
| REQ | Test | Estado |
|---|---|---|
| REQ-1 | `tests/test_schema.py::test_etapas_desde_competidor_marca_una_true_y_las_demas_false` + `::test_etapas_desde_competidor_vacio_deja_las_cinco_vacias` | ✅ |
| REQ-2 | `tests/test_schema.py::test_schema_columns_incluye_etapas_despues_de_salud` + `tests/test_pipeline.py::test_write_csv_completa_etapas_booleanas` + `::test_build_master_deriva_etapas_de_csv_viejos` | ✅ |
| REQ-3 | `tests/test_merge_human.py::test_validate_headers_acepta_excel_sin_columnas_etapa` + `::test_apply_merge_recalcula_etapas_desde_etapa_competidor` | ✅ |

`build_master` también deriva las 5 columnas para los CSV escritos antes de R3.5 (hoy, México y Honduras), sin volver a scrapear.

## Validación contra la fuente real (≥3 productos)
Esta fase no extrae datos nuevos: deriva columnas de `etapa_competidor`, que ya está validado.
| Producto | etapa_competidor | etapa_* en el master |
|---|---|---|
| Nicovita Classic AD (EC) | engorde | engorde=True, otras False |
| Nicovita Térap E+ (EC) | precria | precria=True, otras False (la fuente también dice engorde: lo corrige R4) |
| Nicovita Origin (EC) | larva | larva=True, otras False |

## Conteo antes → después
`pipeline.py --pais ecuador --empresa agripac` → master con 286 filas (EC 165, HN 38, MX 83):
- True por columna: reproductores 2, larva 32, precria 63, post_transferencia 2, engorde 127
- 60 filas sin `etapa_competidor` → las 5 vacías; ninguna fila con más de un True
- Baseline de Ecuador (`master_ecuador_baseline.csv`): se agregaron las 5 columnas derivadas de su propio `etapa_competidor`; el resto no cambia (`test_ecuador_identity` en verde).

## Resultado
`pytest -q`: 223 pasan
