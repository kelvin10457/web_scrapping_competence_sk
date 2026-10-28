# R3.1 — Validación

## Requisito → test
| REQ | Test | Estado |
|---|---|---|
| REQ-1 | `tests/test_schema.py` (columnas del esquema) | ✅ |
| REQ-2 | `git grep producto_salud -- src tests` sin apariciones fuera de `es_producto_de_salud` | ✅ |
| REQ-3 | `tests/test_ecuador_identity.py::test_master_ecuador_matches_pre_refactor_baseline` + suite completa | ✅ |

## Validación contra la fuente real (≥3 productos)
No aplica: rename sin cambios de lógica ni de scraping. La identidad contra el baseline de Ecuador (165 filas) cubre que los valores no cambiaron.

## Conteo antes → después
- Ecuador: 165 → 165 filas, idénticas al baseline salvo el nombre de la columna.
- `data/master.csv`: 286 filas, 43 vacíos en `es_producto_de_salud`.
- Biomar (Agrizon) respondió 429 al regenerar: no se reintentó. Su CSV previo y los de Nicovita (EC/HN) y México se dejaron con sus valores y solo se renombró el encabezado.

## Resultado
`pytest -q`: 197 pasan
