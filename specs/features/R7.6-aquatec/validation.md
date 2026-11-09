# R7.6 — Validación

## Requisito → test
| REQ | Test | Estado |
|---|---|---|
| REQ-1 | `tests/test_aquatec_parser.py::test_una_fila_por_sku_sin_duplicados`, `test_span_dentro_del_titulo_no_parte_la_linea` | ✅ |
| REQ-2 | `test_sku_con_ficha_toma_analisis_y_saco` | ✅ |
| REQ-3 | `test_variante_de_plantilla_no_hereda` | ✅ |
| REQ-4 | `test_tamano_y_tipo_desde_el_nombre` | ✅ |
| REQ-5 | `test_scraper_verify_false_solo_para_nutrimentos`, `test_redireccion_a_otro_dominio_no_lleva_verify_false` | ✅ |
| REQ-6 | `test_registrada_en_mexico` | ✅ |

## Validación contra la fuente real (≥3 productos)
Corrida real `pipeline.py --pais mexico --empresa aquatec` (2026-11-09): 11 productos. Comparado con el texto visible de la página.

| Producto | Campo | Fuente dice | CSV dice |
|---|---|---|---|
| AQUATEC 45% - MIGAJA (Línea HD) | proteína / empaque | "Proteina cruda Min. 45.0 %" · "Saco de 25 kg." | 45 · 25 |
| AQUATEC 40% - MIGAJA (Línea Performance) | proteína / empaque | "Proteina cruda Min. 40.0 %" · "Saco de 25 kg." | 40 · 25 |
| AQUATEC 45% - MIGAJA 0.3 mm (Línea HD) | proteína / tamaño / empaque | nombre "45% … 0.3 mm"; solo texto de plantilla | 45 · 0.3 · vacío |
| AQUATEC 25% - PELLET 2.0 mm (Línea Estándar) | proteína / tamaño / tipo | nombre "25% - PELLET 2.0 mm"; plantilla | 25 · 2 · Pellet |

## Conteo antes → después
México: +11 filas (empresa nueva `AQUATEC`, `data/powerbi/mexico/AQUATEC.xlsx`). Etapas vacías en las 11: "juveniles hasta 5 gramos" no nombra una etapa del ciclo. `etapa_skt` sale de la banda de tamaño (regla existente): 7 filas con tamaño. Sin conflictos: título y análisis coinciden en las 3 fichas.

## Decisiones (conservadoras)
- `nombre_producto` lleva `(Línea X)`, porque el mismo nombre se publica en varias líneas (p. ej. "35% - PELLET 2.0 mm" en las tres).
- La ficha "Línea Estándar AQUATEC 40% - MIGAJA" no figura en la columna Estándar, pero igual es una SKU (la publica la ficha).
- La proteína de las variantes sale del `NN%` de su nombre, como Vimifos ("Bumper Crop 30%"). En las 3 fichas, el % del nombre coincide con el análisis.
- Migaja: `tipo_presentacion` vacío (no hay grafía oficial; mismo criterio que El Pedregal).

## Colaboración
- **Codex (implementación):** no pudo. Su entorno monta `../wt-codex` como solo lectura y no resuelve DNS. La implementación la hizo Claude.
- **Codex (revisión de solo lectura):** 2 hallazgos, **ambos aplicados**:
  1. *Media:* `verify=False` se propagaba en un 302 hacia otro dominio. Ahora las redirecciones se siguen a mano y `verify` se decide por host en cada salto. Test nuevo.
  2. *Media:* un `<span>` dentro del título partía la línea y perdía "PELLET 1.8 mm". Ahora solo los elementos de bloque cortan línea. Test nuevo.
  - Codex reportó una corrida de pytest con exit 1 sin motivo. Repetida a mano: 8/8 en verde y la suite completa también. Era el mismo problema de temporales no escribibles de su entorno que en R8.9.
- **Descartado:** nada.

## Resultado
`pytest -q`: 315 pasan · commit: `R7.6`
