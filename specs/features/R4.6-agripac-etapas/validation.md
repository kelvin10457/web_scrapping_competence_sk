# R4.6 — Validación

## Requisito → test
| REQ | Test | Estado |
|---|---|---|
| REQ-1 | `tests/test_agripac_parser.py::test_r46_req1_descripcion_marca_todas_las_etapas` | ✅ |
| REQ-2 | `tests/test_agripac_parser.py::test_r46_req2_sin_termino_de_etapa_usa_el_tamano_de_pellet` | ✅ |
| REQ-3 | `tests/test_agripac_parser.py::test_r46_req3_royal_pepper_protein_queda_vacio` | ✅ |

## Validación contra la fuente real (≥3 productos)
`pipeline.py --pais ecuador --empresa agripac` (38 filas). La fuente son las pestañas WooCommerce de cada página de agripac.com.ec/productos/.

| Producto | La fuente dice | `etapa_*` en `true` |
|---|---|---|
| Larfeed | "para larvas y post-larvas de camarón"; tabla Mysis 3 – PL20 | larva, post_larva |
| Vitellus Small | "ideal para zoea 3 – mysis 3", "para las larvas y post larvas" | larva, post_larva |
| Mpex 100-200 | "particulado para postlarvas", "estadios PL1 a PL6" | post_larva |
| Royal Caviar 5-50 | "alimento para larvas", "ideal para zoeas" | larva |
| New Royal Oyster | "alimento suplementario para reproductores" | reproductores |
| Feedpac 35% Ultra Micropellet 1.2mm | "camarones adultos y juveniles" (sin término); 1.2 mm | precria (por tamaño) |
| Royal Pepper Protein | modo de uso "Criterio técnico", sin término ni tamaño | ninguna (vacío) |

## Conteo antes → después
- Larfeed, las 3 Royal Seafood y las 3 Vitellus: larva → larva + post_larva (7 filas).
- Las 2 MeM y las 4 Mpex: larva → post_larva (6 filas).
- Las otras 25 filas no cambian (los 20 Feedpac siguen por banda de tamaño; 4 sin tamaño quedan vacíos, como antes).
- `etapa_competidor` y `etapa_skt` no cambian.

## Resultado
`pytest -q`: 261 pasan · commit: ver `git log` (`R4.6: ...`)

## Nota: baseline de Ecuador
`test_ecuador_identity` mostró solo las 13 filas de Agripac de arriba (`etapa_larva` / `etapa_post_larva`). Las demás columnas y empresas quedan idénticas. Se actualizó `tests/fixtures/master_ecuador_baseline.csv`.
