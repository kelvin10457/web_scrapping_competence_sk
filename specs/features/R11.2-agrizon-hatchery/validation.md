# R11.2 — Validación

## Requisito → test
| REQ | Test | Estado |
|---|---|---|
| REQ-1 | `tests/test_agrizon_hatchery.py::test_biomasa_artemia_una_fila_prilabsa` | ✅ |
| REQ-2 | `tests/test_agrizon_hatchery.py::test_proteina_bernaqua_del_body_y_rango_vacio` | ✅ |
| REQ-3 | `test_clave_nombre_empata_agripac_con_agrizon`, `test_completa_proteina_vacia_y_registra_origen` | ✅ |
| REQ-4 | `test_no_pisa_proteina_de_agripac` | ✅ |
| REQ-5 | `test_agrizon_caido_devuelve_vacio` | ✅ |
| REQ-6 | `test_megalikuid_filas_megasupply` | ✅ |

## Validación contra la fuente real (agrizon.com `products.json`, 2026-11-09)
| Producto | Campo | Fuente dice | CSV dice |
|---|---|---|---|
| Megalikuid B 1 lt. | proteína / tamaño | "Proteína 6.5%", "(50-120μ)" | 6.5 / 0.05-0.12 |
| Megalikuid C 1 lt. | tamaño | "(120-400μ)" | 0.12-0.4 |
| Royal Caviar 5-50 400 gr | proteína | "Proteína 55%" | 55 (fila de Agripac) |
| Royal Pepper Protein 1lt | proteína | "Proteína 11%" | 11 (fila de Agripac) |
| Biomasa de Artemia Congelada 1 kg. | empaque / etapa | "Funda x 1 kg", tag "Post-larva" | 1 / post_larva → Nursery |

## Conteo antes → después
- Ecuador: 213 → 216 filas (Megalikuid B y C, Biomasa de Artemia).
- Agripac: proteína vacía 18 → 9; las 9 completadas quedan en `_conflictos.csv` con la regla `completado:agrizon`. MPEX 300-500 queda vacío porque la fuente da un rango (55-60%). MeM 200-300 y Mpex 500-800 no están en Agrizon.
- Baseline `tests/fixtures/master_ecuador_baseline.csv` regenerado (único cambio: lo de arriba).

## Resultado
`pytest -q`: 366 pasan
