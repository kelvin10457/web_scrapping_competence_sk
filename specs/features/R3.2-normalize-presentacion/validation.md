# R3.2 — Validación

## Requisito → test
| REQ | Test | Estado |
|---|---|---|
| REQ-1 | `tests/test_schema.py::test_tipo_presentacion_oficial_es_la_lista_de_tech_stack` | ✅ |
| REQ-2 | `tests/test_schema.py::test_normalize_presentacion_valor_oficial_con_grafia_oficial` | ✅ |
| REQ-3 | `tests/test_schema.py::test_normalize_presentacion_pelletizado_pasa_a_pellet` | ✅ |
| REQ-4 | `tests/test_schema.py::test_normalize_presentacion_desconocido_se_conserva` | ✅ |
| REQ-5 | `tests/test_schema.py::test_normalize_presentacion_vacio_es_none` | ✅ |

## Validación contra la fuente real (≥3 productos)
No aplica: fase sin scraping (solo la función). Los casos de prueba son los 5 valores que hoy tiene `master.csv`; la validación contra la fuente se hace en R3.3.

## Conteo antes → después
Sin cambios en el CSV (ningún parser usa la función todavía).

## Resultado
`pytest -q`: 205 pasan
