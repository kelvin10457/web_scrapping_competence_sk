# R4.5 — Validación

## Requisito → test
| REQ | Test | Estado |
|---|---|---|
| REQ-1 | `tests/test_agrizon_parser.py::test_r45_req1_titulo_mas_tags_marca_todas_las_etapas` | ✅ |
| REQ-2 | `tests/test_agrizon_parser.py::test_r45_req2_sin_termino_de_etapa_usa_el_tamano_de_pellet` | ✅ |
| REQ-3 | `tests/test_agrizon_parser.py::test_r45_req3_el_slug_no_se_usa` | ✅ |

## Validación contra la fuente real (≥3 productos)
`pipeline.py --pais ecuador --empresa biomar` (17 filas). La fuente es agrizon.com/collections/biomar/products.json: título y tags de cada producto.

| Producto | La fuente dice (título + tags) | `etapa_*` en `true` |
|---|---|---|
| Exia Prime 35% Pelletized 1.2 mm | tags "engorde", "Iniciadores" | precria, engorde |
| Exia Prime 35% Pelletized 1.6 mm | tags "crecimiento", "engorde", "Iniciadores" | precria, engorde |
| Larviva 55% 250-375 microns | tags "larvas", "Post-larva" | larva, post_larva |
| Exia Start 38% 0.9-1.2 mm | tags "Inicio", "Precrías" (el slug dice "dieta-para-larvas") | precria |
| Exia Pro 35% Pelletized 2.0 mm | tags sin etapa ("Prevención", "Probióticos", "Salud"); 2.0 mm Pelletized | engorde (por tamaño) |
| Exia Perform 35% Pelletized 2.0 mm | tags "crecimiento", "engorde" | engorde |

## Conteo antes → después
- Filas sin etapa: 1 → 0. Exia Prime 1.6 mm pasa de vacío a precria + engorde.
- Exia Prime 1.2 mm: precria → precria + engorde. Las 3 Larviva: larva → larva + post_larva.
- Las otras 12 filas no cambian. Exia Pro 2.0 mm sigue en engorde, ahora por la banda de tamaño.
- `etapa_competidor` y `etapa_skt` no cambian.

## Resultado
`pytest -q`: 258 pasan · commit: ver `git log` (`R4.5: ...`)

## Nota: baseline de Ecuador
`test_ecuador_identity` mostró solo las 5 filas de BioMar de arriba (Exia Prime 1.2 y 1.6 mm, las 3 Larviva). Las demás columnas y empresas quedan idénticas. Se actualizó `tests/fixtures/master_ecuador_baseline.csv`.
