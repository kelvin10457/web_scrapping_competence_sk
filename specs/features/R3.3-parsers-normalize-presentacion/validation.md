# R3.3 — Validación

## Requisito → test
| REQ | Test | Estado |
|---|---|---|
| REQ-1 | `tests/test_schema.py::test_detect_tecnologia_devuelve_la_lista_oficial` (+ HAID/Nicovita/Agrizon actualizados a `Pellet`) | ✅ |
| REQ-2 | `tests/test_schema.py::test_umbral_grower_de_pellet_acepta_pellet_y_pelletizado` | ✅ |
| REQ-3 | `tests/test_agripac_parser.py::test_tipo_presentacion_microextruido_desde_la_pestana_tipo` + `tests/test_schema.py::test_normalize_presentacion_alias_de_agripac` | ✅ |
| REQ-4 | `tests/test_agrizon_parser.py::test_tipo_presentacion_microgranulado_se_conserva_si_es_la_unica_tecnologia` + `::test_tipo_presentacion_pelletizado_gana_sobre_microgranulado` | ✅ |
| REQ-5 | `tests/test_aquaxcel_parser.py::test_tipo_presentacion_pelletizado_pasa_a_pellet` | ✅ |
| REQ-6 | `tests/test_ecuador_identity.py` con el baseline actualizado | ✅ |

## Validación contra la fuente real (≥3 productos)
| Producto | Campo | Fuente dice | CSV dice |
|---|---|---|---|
| Agripac MeM 200–300 (`/productos/mem/`) | tipo_presentacion | pestaña Tipo: "Microextruido" | Microextruido |
| Agripac Feedpac 35% Premium | tipo_presentacion | pestaña Tipo: "Pelletizado" | Pellet |
| BioMar Exia Prime 35% Precria 0.6–0.9 (Agrizon) | tipo_presentacion | tags: "…, Microgranulado, …" (sin otra tecnología) | Microgranulado |

## Conteo antes → después
Ecuador: 165 → 165 filas. Solo cambia `tipo_presentacion` (105 filas); ninguna otra columna cambia:
- `Pelletizado` → `Pellet`: 102 (Nicovita 52, Agripac 18, HAID 12, BioMar 10, Cargill 10)
- `Extruido` → `Microextruido`: 2 (Agripac MeM)
- vacío → `Microgranulado`: 1 (BioMar Exia Prime Precria 0.6–0.9)

México y Honduras no se regeneraron en esta fase: su `master.csv` sigue con `Pelletizado` hasta la próxima corrida.

## Resultado
`pytest -q`: 211 pasan
