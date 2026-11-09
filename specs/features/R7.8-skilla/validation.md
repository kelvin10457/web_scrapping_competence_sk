# R7.8 — Validación

## Requisito → test
| REQ | Test | Estado |
|---|---|---|
| REQ-1 | `tests/test_skilla.py::test_una_fila_por_codigo_y_diametro` | ✅ |
| REQ-2 | `test_foto_se_asigna_por_orden_y_sin_pie_queda_vacio`, `test_pie_malformado_no_da_diametro`, `test_foto_faltante_conserva_el_producto_sin_tamano` | ✅ |
| REQ-3 | `test_etapas_tipo_y_vacios` | ✅ |
| REQ-4 | `test_registrada_en_mexico` | ✅ |

## Validación contra la fuente real (≥3 productos)
Corrida real `pipeline.py --pais mexico --empresa skilla` (2026-11-09): 4 filas. Pies de foto verificados a ojo en las imágenes.

| Producto | Fuente dice | CSV dice |
|---|---|---|
| SKILLA 4008 (Inicio) | foto `Skilla-4008-1x15`: "1 x 1.5 mm" | 1 · sin etapa · Nursery (banda) |
| SKILLA 4008 (Pre-engorda) | foto `Skilla_4008`: "1.5 x 2.5 mm" | 1.5 · post_transferencia |
| SKILLA 3505 (Engorda) | foto `Skilla_3505-3`: "2.5 x 4 mm" | 2.5 · engorde · Grower |

## Conteo antes → después
México: +4 filas (empresa nueva `Skilla`). Proteína y empaque vacíos en las 4 (no se publican en texto).

## Revisión de Codex (solo lectura, effort medium)
3 hallazgos, los 3 aplicados: (1) si faltaba una foto se perdía la etapa entera → ahora el producto queda sin tamaño; (2) la regex del pie aceptaba coincidencias parciales (`1.5.5 x 2.5 mm` → 5.5) → ahora exige el pie completo; (3) el parser contaba cualquier PNG → comparte con el scraper el filtro de fotos de producto.
