# R3.7 — Validación

## Requisito → test
| REQ | Test | Estado |
|---|---|---|
| REQ-1 | `tests/test_schema.py::test_normalize_proteina_acepta_numero_texto_y_coma_decimal`, `::test_normalize_proteina_ambiguo_o_fuera_de_rango_queda_vacio` | ✅ |
| REQ-2 | `tests/test_proteina_fuentes.py::test_proteina_pct_es_float_o_vacio_en_todas_las_fuentes` (9 fuentes: Agripac, Agrizon, Aquaxcel, BioMar, Api-Aba, Nutrimar, Vimifos, Haid y Nicovita) | ✅ |
| REQ-3 | Comparación de los masters antes y después (multiconjunto de empresa, producto, tamaño, url y proteína) | ✅ |

## Validación contra la fuente real (≥3 productos)
| Producto | Campo | Fuente dice | Parser da |
|---|---|---|---|
| Agripac Feedpac 35% Premium (`agripac_feedpac_35_premium.html`) | proteina_pct | título "Feedpac 35% Premium" | `35.0` (antes `"35"`) |
| Nicovita Classic AD (`data/raw/nicovita/FT-NICOVITA-CLASSIC-CAMARON-AD.pdf`) | proteina_pct | tabla Presentación Comercial: 28 % y 35 % | `28.0`, `35.0` (antes `"28"`, `"35"`) |
| Zeigler PL Raceway 40-9 (`nutrimar_ficha_pl_raceway_40_9.txt`) | proteina_pct | "Proteína cruda Mínimo 40,0%" | `40.0` |

## Conteo antes → después
| Master | Filas | Con proteína | Valores distintos |
|---|---|---|---|
| Ecuador | 165 → 165 | 146 → 146 | 0 |
| Honduras | 38 → 38 | 38 → 38 | 0 |
| México | 83 → 83 | 82 → 82 | 0 |

Ningún valor cambia en los CSV: el cambio es de tipo (texto → `float`) y de robustez (coma decimal). En los `.xlsx`, `proteina_pct` sigue saliendo como número.

## Resultado
`pytest -q`: 231 pasan
