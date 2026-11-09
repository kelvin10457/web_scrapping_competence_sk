# R4.2b — Validación

## Requisito → test
| REQ | Test | Estado |
|---|---|---|
| REQ-1 | `tests/test_nicovita_parser.py::test_r42b_req1_corrige_solo_el_enlace_equivocado` | ✅ |
| REQ-2 | `tests/test_nicovita_parser.py::test_r42b_req2_queda_como_alias_de_classic_organic` | ✅ |

## Validación contra la fuente real
`pipeline.py --pais honduras --empresa nicovita`, contra `FT-NICOVITA-CLASSIC-ORGANIC-CAMARON-HO.pdf`:

| Campo | Ficha | CSV (Classic Organic Engorde) |
|---|---|---|
| Pares proteína / tamaño | 30% y 35% × 1.2 / 2.0 / 2.5 mm | las mismas 6 filas |
| Descripción | "peletizada… desde 1 gramo de peso vivo hasta tamaño de mercado" | Pellet · solo `etapa_engorde` |
| Origin Orgánico (control) | microesferas 45%, 0.3 / 0.5 / 0.8 mm, PL4 a 1 g | sin cambios: Extruido · `etapa_post_larva` |

## Conteo antes → después (Honduras)
- Antes: 38 filas. Classic Orgánico Engorde (3 filas) tenía los datos de Origin Orgánico, y Classic Orgánico (6 filas) estaba aparte.
- Después: 35 filas. Las dos páginas se juntan en una sola fuente (`…classic-organic-engorde-honduras/`, 6 filas con la ficha correcta), con el mismo criterio que ya junta Classic con Classic Engorde.

## Resultado
`pytest -q`: 248 pasan · commit: ver `git log` (`R4.2b: ...`)

## Nota: baseline de Ecuador
Al regenerar `data/master.csv`, `test_ecuador_identity` mostró las diferencias de R4.1/R4.2 que el baseline todavía no tenía: la columna `etapa_post_larva` y las `etapa_*` de Nicovita. Todas las demás columnas y empresas quedan idénticas. Se actualizó `tests/fixtures/master_ecuador_baseline.csv`.
