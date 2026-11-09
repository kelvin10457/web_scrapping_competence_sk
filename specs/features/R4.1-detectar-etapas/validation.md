# R4.1 — Validación

## Requisito → test
| REQ | Test | Estado |
|---|---|---|
| REQ-1 | `tests/test_schema.py::test_req1_etapa_post_larva_entre_larva_y_precria` | ✅ |
| REQ-2 | `tests/test_schema.py::test_req2_detectar_etapas_devuelve_todas_las_explicitas` | ✅ |
| REQ-3 | `tests/test_schema.py::test_req3_post_larva_no_es_larva` | ✅ |
| REQ-4 | `tests/test_schema.py::test_req4_palabras_genericas_no_marcan_etapa` | ✅ |
| REQ-5 | `tests/test_schema.py::test_req5_rango_marca_extremos_e_intermedias` | ✅ |
| REQ-6 | `tests/test_schema.py::test_req6_columnas_etapa` | ✅ |
| REQ-7 | `tests/test_schema.py::test_req7_respaldo_skt_post_larva_es_nursery` | ✅ |

## Validación contra la fuente real (≥3 productos)
Esta fase no hace scraping: se valida con frases reales de las fichas guardadas en `tests/fixtures/`.

| Producto | Fuente dice | `detectar_etapas` |
|---|---|---|
| Aquaxcel México (listing) | "para la etapa de post-larva en … raceways o precrías hasta los 0.20g" | post_larva, precria |
| Nutrimar (listing) | "para post larvas hasta 1.0g de peso vivo" | post_larva |
| Nutrimar (intensivo) | "etapa de transición hacia la fase de engorde hasta los 12g" | post_transferencia, engorde |
| Api-Aba Apicamarón Dorado 40% | "fase postlarval hasta 3–4 g de peso. Favorece el crecimiento" | post_larva (crecimiento no cuenta) |
| Nicovita Térap | "post larva hasta tamaño de mercado" | post_larva, precria, post_transferencia, engorde |

## Conteo antes → después
Los parsers todavía no usan la función (eso es R4.2–R4.9). En el CSV, la columna nueva `etapa_post_larva` queda en `False` cuando hay `etapa_competidor` y vacía cuando no hay (puente R3.5). Un `master.xlsx` anterior a esta fase se completa al fusionar (`merge_human._normalize_master_dtypes`).

## Resultado
`pytest -q`: 238 pasan · commit: ver `git log` (`R4.1: ...`)
