# R3.6 — Validación

## Requisito → test
| REQ | Test | Estado |
|---|---|---|
| REQ-1 | `tests/test_schema.py::test_etapa_skt_cortes_por_tamano_sin_importar_presentacion` | ✅ |
| REQ-2 | `tests/test_schema.py::test_etapa_skt_rango_usa_el_minimo` | ✅ |
| REQ-3 | `tests/test_schema.py::test_etapa_skt_sin_tamano_usa_etapa_del_competidor` + `::test_etapa_skt_sin_tamano_ni_etapa_conocida_queda_vacio` | ✅ |
| REQ-4 | `tests/test_schema.py::test_etapa_skt_larva_overrides_to_hatchery_regardless_of_tamano` + `::test_etapa_skt_es_larvicultura_overrides_to_hatchery_regardless_of_tamano` | ✅ |

`test_umbral_grower_de_pellet_acepta_pellet_y_pelletizado` (R3.3) ya no verifica `etapa_skt`, porque ya no depende de la presentación. Sigue verificando `etapa_from_tamano`.

## Validación contra la fuente real (≥3 productos)
| Producto | Campo | Fuente dice | CSV dice |
|---|---|---|---|
| BioMar Exia Prime (EC) | tamaño → etapa_skt | URL `exia-prime-35-extruido-1-8-mm` (1.8 mm extruido) | 1.8 → Grower (antes vacío) |
| Aquaxcel Adapt Shock 35% (MX) | tamaño → etapa_skt | nombre "1.8mm", extruido | 1.8 → Grower (antes vacío) |
| Vimifos Bumper Crop (MX) | tamaño → etapa_skt | tabla `1.8MM - 3MM` (`tests/fixtures/vimifos_bumper_crop.html`) | 1.8-3 → Grower (antes vacío) |
| Nicovita Katal Precría (EC) | respaldo | sin tamaño, ficha "Precría" | precria → Nursery (antes vacío) |

## Conteo antes → después
Pipeline completo, master de 286 filas (igual que antes):
- Grower 100 → 121, Nursery 94 → 95, Hatchery 34, Pre Grower 25, vacío 33 → 11
- 24 filas pasan de vacío a un valor y **ninguna fila que tenía valor cambia**
- 11 vacíos: no tienen ni tamaño ni etapa del competidor (Feedpac Premium ×4, Zeigler ×4, Nutrimar ×2, Api-Aba ×1)
- Baseline de Ecuador: `etapa_skt` actualizado en esas 2 filas (Exia Prime y Katal Precría)

## Resultado
`pytest -q`: 220 pasan
