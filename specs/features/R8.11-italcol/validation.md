# R8.11 — Validación

## Requisito → test
| REQ | Test | Estado |
|---|---|---|
| REQ-1 | `tests/test_italcol.py::test_una_fila_con_proteina`, `test_html_cambiado_no_rompe_ni_inventa` | ✅ |
| REQ-2 | `test_etapa_engorde_y_vacios` | ✅ |
| REQ-3 | `test_registrada_en_panama` | ✅ |

## Validación contra la fuente real
La fuente tiene **un solo producto**, así que no se pueden validar 3. Corrida real `pipeline.py --pais panama --empresa italcol` (2026-11-09):

| Producto | Fuente dice | CSV dice |
|---|---|---|
| AQUACAMARON 35 | "PROTEÍNA (MIN) 35.0%" · "hasta peso de cosecha en sistemas intensivos" | 35 · engorde · Grower (respaldo sin tamaño) |

## Conteo antes → después
Panamá: +1 fila (empresa nueva `Italcol`).

## Revisión de Codex (solo lectura, effort medium)
2 hallazgos, aplicados: (1) el bloque de composición era el `div` inmediato → ahora es el primer ancestro con descripción y listas; (2) el nombre salía de cualquier `<title>` (uno de SVG daba "Buscar") → ahora sale de `.product_title`, con el `<title>` del `<head>` como respaldo.
