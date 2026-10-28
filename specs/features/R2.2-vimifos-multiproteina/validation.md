# R2.2 — Validación

## Requisito → test
| REQ | Test | Estado |
|---|---|---|
| REQ-1, REQ-3 | `tests/test_vimifos_parser.py::test_micras_converted_and_multiple_proteins_split_in_skus` | ✅ |
| REQ-2 | `tests/test_vimifos_parser.py::test_varias_proteinas_m_igual_n_empareja_en_orden` | ✅ |
| REQ-4 | `tests/test_vimifos_parser.py::test_varias_proteinas_m_distinto_n_deja_texto_y_registra_conflicto` | ✅ |
| REQ-5 | `tests/test_vimifos_parser.py::test_asociacion_explicita_manda_sobre_el_orden` | ✅ |

## Validación contra la fuente real
Bumper Crop, Natural Force y Total Range traen un solo calibre (2-6) → 3 filas cada uno (REQ-3). No apareció ningún caso de `calibre_no_emparejable` en el sitio real.

## Conteo antes → después
Vimifos México: proteína nula en 3/15 → 0/21.

## Resultado
`pytest -q` en verde al cerrar la ronda 2 (2026-10-20). Detalle: `docs/historico/PROGRESO_REGIONAL.md`.
