# R3.4 — Validación

## Requisito → test
| REQ | Test | Estado |
|---|---|---|
| REQ-1 | `tests/test_schema.py::test_presentaciones_nuevas_solo_valores_fuera_de_la_lista_oficial` | ✅ |
| REQ-2 | `tests/test_pipeline.py::test_write_presentaciones_nuevas_escribe_csv_del_master` + `::test_write_presentaciones_nuevas_sin_valores_deja_solo_encabezado` | ✅ |
| REQ-3 | `tests/test_pipeline.py::test_reportar_presentaciones_nuevas_resume_por_valor` + `::test_reportar_presentaciones_nuevas_calla_si_no_hay` | ✅ |

## Validación contra la fuente real (≥3 productos)
Esta fase no extrae datos nuevos: avisa sobre valores que ya están en el master. Se cruzó el aviso con el master y la fuente:
| Producto | Campo | Fuente / master dice | Aviso dice |
|---|---|---|---|
| BioMar Exia Prime 35% Precria 0.6–0.9 (Agrizon) | tipo_presentacion | tag "Microgranulado" (validado en R3.3) | Microgranulado |
| Nicovita Classic Engorde (Honduras) | tipo_presentacion | master sin regenerar: Pelletizado | Pelletizado |
| Nicovita Classic AD (Ecuador) | tipo_presentacion | Pellet (oficial) | no aparece |

## Conteo antes → después
`pipeline.py --pais ecuador --empresa agripac` → `data/presentaciones_nuevas.csv` con 52 filas:
- `Pelletizado`: 51 (Honduras Nicovita 28, México Nicovita 22, México Cargill 1): master sin regenerar desde R3.3; desaparecen en la próxima corrida de esos países
- `Microgranulado`: 1 (Ecuador BioMar, Agrizon)

Master de Ecuador sin cambios (`test_ecuador_identity` en verde).

## Resultado
`pytest -q`: 216 pasan
