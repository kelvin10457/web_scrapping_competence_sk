# R8.10 — Validación

## Requisito → test
| REQ | Test | Estado |
|---|---|---|
| REQ-1 | `tests/test_nasafeed.py::test_tres_filas_por_proteina_sin_tamano` | ✅ |
| REQ-2 | `test_empaque_tipo_y_etapas` | ✅ |
| REQ-3 | `test_usa_wayback_si_el_sitio_no_responde`, `test_html_o_captcha_tambien_pasan_a_wayback`, `test_wayback_que_no_es_pdf_falla` | ✅ |
| REQ-4 | `test_registrada_en_panama` | ✅ |

## Validación contra la fuente real (≥3 productos)
Corrida real `pipeline.py --pais panama --empresa nasafeed` (2026-11-09): nasafeed.com dio timeout y se usó Wayback (50 s, por los 2 intentos de 20 s al sitio original). 3 filas.

| Producto | Fuente dice | CSV dice |
|---|---|---|
| Aquanasa Línea Premium 25% | "Proteína Cruda (mínima) 25.00 …" · "100 lbs(45.36 Kg)" · "desde post larva hasta la cosecha" | 25 · 45.36 · Pellet · post_larva→engorde |
| Aquanasa Línea Premium 30% | columna 2: 30.00 | 30 · 45.36 |
| Aquanasa Línea Premium 35% | columna 3: 35.00 | 35 · 45.36 |

## Conteo antes → después
Panamá: +3 filas (primera fuente automatizada; empresa `NasaFeed`). `etapa_skt` = Nursery por el respaldo sin tamaño (etapa más temprana del ciclo con respaldo: precria).

## Revisión de Codex (solo lectura, effort medium)
2 hallazgos, aplicados: (1) un 200 con HTML se tomaba como PDF y no pasaba a Wayback → ahora se exige `%PDF`; (2) un captcha (`netutil.BlockedError`) no pasaba a Wayback → ahora sí.
