# R4.3 — Validación

## Requisito → test
| REQ | Test | Estado |
|---|---|---|
| REQ-1 | `tests/test_haid_parser.py::test_r43_req1_starter_pro_slug_y_pl10_en_todas_las_filas`, `::test_r43_req1_hasta_la_cosecha_en_recomendaciones_es_engorde`, `::test_r43_req1_shrimpy_juveniles_y_engorde` | ✅ |
| REQ-2 | `tests/test_haid_parser.py::test_r43_req2_gramos_sin_termino_de_etapa_quedan_vacias` | ✅ |

## Validación contra la fuente real (≥3 productos)
`pipeline.py --pais ecuador --empresa haid` (16 filas), contra las fichas PDF guardadas en `data/raw/haid/`.

| Producto | La fuente dice | `etapa_*` en `true` |
|---|---|---|
| Starter Pro (slug + PDF) | "starter" + "a partir de PL 10 hasta 0.25 gramos" | post_larva, precria |
| Starter (slug + PDF) | "starter" + "de 1 gramo hasta 3 gramos" | precria |
| Speed (PDF) | "a partir de los 12 gramos hasta la cosecha" | engorde |
| Happiness Plus (PDF) | "a partir de los 8 gramos hasta la cosecha" | engorde |
| Happiness / Fitness (PDF) | "camarones juveniles y (de) engorde" | engorde |

## Conteo antes → después (Ecuador)
- HAID: 0 filas vacías antes y después. Solo cambian las 3 filas de Starter Pro: ahora también tienen `etapa_post_larva` (PL 10). Se actualizó `tests/fixtures/master_ecuador_baseline.csv` solo en esas 3 filas.
- `etapa_competidor` y `etapa_skt` no cambian.

## Resultado
`pytest -q`: 252 pasan · commit: ver `git log` (`R4.3: ...`)
