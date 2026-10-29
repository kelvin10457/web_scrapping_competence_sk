# R4.4 — Validación

## Requisito → test
| REQ | Test | Estado |
|---|---|---|
| REQ-1 | `tests/test_aquaxcel_parser.py::test_r44_req1_ecuador_etapa_de_uso_inicio_es_precria_engorde_es_engorde` | ✅ |
| REQ-2 | `tests/test_aquaxcel_parser.py::test_r44_req2_mexico_linea_mas_descripcion` | ✅ |
| REQ-3 | `tests/test_aquaxcel_parser.py::test_r44_req3_mexico_adapt_sin_termino_de_etapa_queda_vacio` | ✅ |

## Validación contra la fuente real (≥3 productos)
`pipeline.py --pais ecuador --empresa aquaxcel` (37 filas) y `--pais mexico --empresa aquaxcel` (14 filas), contra el sitio en vivo (aquaxcel.com/productos/ecuador y /mexico).

| Producto | La fuente dice | `etapa_*` en `true` |
|---|---|---|
| EC: Advance 35% 0.8 | ETAPA DE USO "INICIO" | precria |
| EC: Maxima 35% 2.0 | ETAPA DE USO "ENGORDE" | engorde |
| MX: Transition 38% | "etapa de transición hacia la fase de engorde" | post_transferencia, engorde |
| MX: Nursery 45% SmartShield | "etapa de post-larva ... o precrías" | post_larva, precria |
| MX: Advance 35% AP | "desde los 12g hasta peso de cosecha" | engorde |
| MX: Adapt Shock (5) | línea de salud, sin término de etapa | (vacío) |

## Conteo antes → después
- Ecuador: 0 filas vacías antes y después, sin cambios en las 37 filas. El baseline no cambia.
- México: Adapt Shock (5 filas) sigue vacío. Transition y Advance/Active (4 filas) pasan de vacío a tener etapa. Nursery y los dos Pre-Starter suman `etapa_post_larva`.
- `etapa_competidor` y `etapa_skt` no cambian.

## Resultado
`pytest -q`: 255 pasan · commit: ver `git log` (`R4.4: ...`)
