# R4.2 — Validación

## Requisito → test
| REQ | Test | Estado |
|---|---|---|
| REQ-1 | `tests/test_nicovita_parser.py::test_r42_req1_terap_marca_todo_el_rango_en_todas_las_filas`, `::test_r42_req1_slug_y_pdf_se_suman`, `::test_r42_req1_web_solo_sin_pdf_y_sin_etiqueta_de_categoria`, `::test_r42_req1_sin_texto_de_etapa_quedan_vacias` | ✅ |
| REQ-2 | `tests/test_pipeline.py::test_write_csv_respeta_etapas_del_parser` | ✅ |
| REQ-3 | `tests/test_schema.py::test_r42_req3_cosecha_es_engorde` | ✅ |
| REQ-4 | `tests/test_schema.py::test_r42_req4_transferencia_suelta_no_es_post_transferencia` | ✅ |
| REQ-5 | `tests/test_schema.py::test_r42_req5_pl_con_numero_es_post_larva` | ✅ |

## Validación contra la fuente real (≥3 productos)
`pipeline.py --pais ecuador --empresa nicovita` (57 filas), contra la ficha PDF / la página guardadas en `data/raw/`.

| Producto | Fuente dice | `etapa_*` en `true` |
|---|---|---|
| Térap (PDF) | "desde post larva hasta tamaño de mercado" | post_larva, precria, post_transferencia, engorde |
| Classic Precría (slug + PDF) | "precria" + "PL10 a 1 gramo de peso, en sistemas de transferencia" | post_larva, precria |
| Classic Post Transferencia (slug + PDF) | "post transferencia" + "desde 1 hasta 3 gramos" | post_transferencia |
| Katal AD (PDF) | "desde 1 gramo de peso vivo hasta tamaño de cosecha" | engorde |
| Katal Precría (web, sin PDF) | "para precrías desde PL20 hasta 1 g" (sin la etiqueta "Pre engorde") | post_larva, precria |
| Origin (PDF) | "Post Larvas … desde PL4 a 1 gramo" | post_larva |

Ojo: Origin antes figuraba como `larva` (puente). Ahora queda en `post_larva`, que es lo que dice la ficha (decisión de R4.1).

## Conteo antes → después (Ecuador, 57 filas)
- Antes (puente R3.5): una sola etapa por fila, y 2 filas vacías (sin `etapa_competidor`).
- Después: 0 filas vacías y 31 filas con más de una etapa.
- `etapa_competidor` y `etapa_skt` no cambian.

## Hallazgo fuera de alcance
La página Classic Orgánico Engorde (Honduras) enlaza el PDF de Origin Orgánico (error del sitio), así que sus etapas salen de esa ficha equivocada.

## Resultado
`pytest -q`: 246 pasan · commit: ver `git log` (`R4.2: ...`)
