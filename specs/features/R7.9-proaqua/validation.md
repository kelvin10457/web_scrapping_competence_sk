# R7.9 — Validación

## Requisito → test
| REQ | Test | Estado |
|---|---|---|
| REQ-1 | `tests/test_proaqua.py::test_listado_solo_formulados` | ✅ |
| REQ-2 | `test_variantes_por_columna_y_por_ficha`, `test_variante_nombrada_sin_columna_no_se_reparte` | ✅ |
| REQ-3 | `test_tamano_y_empaque` | ✅ |
| REQ-4 | `test_etapas_y_presentacion` | ✅ |
| REQ-5 | `test_registrada_en_mexico` | ✅ |

## Validación contra la fuente real (≥3 productos)
Corrida real `pipeline.py --pais mexico --empresa proaqua` (2026-11-09): 12 filas (Biogrow 7, Epicore 5).

| Producto | Fuente dice | CSV dice |
|---|---|---|
| Biogrow Formula 2 (040-150 Micras Mysis) | "de 40-150 micras" · "Proteína 59.0% min" · "[Lata 1 libra]" · "etapas de mysis y en su metamorfosis a postlarva" | 0.04-0.15 · 59 · 0.45 · larva + post_larva · Hatchery |
| Epibal-300 | tabla: Granular, 300 microns; "Proteína (%) 49"; "[Cuñete 20 kilos]"; "etapas post-larvales y juveniles" | 0.3 · Granulado · 49 · 20 · post_larva |
| Epifeed MBF | "Proteína (%) 43"; "mantener prolíficos reproductores" | 43 · reproductores · sin tamaño ni etapa_skt |
| Biogrow XT ultra | fichas 0.3/0.6/0.8 MM; "Proteína 45.0% min" | 3 filas · 45 · sin etapa (laboratorio y race-way no es etapa) |

## Conteo antes → después
México: +12 filas (empresas nuevas `Biogrow` y `Epicore`).

## Revisión de Codex (solo lectura, effort medium)
1 hallazgo, aplicado: un título que nombra una variante sin columna propia (p. ej. "Epibal-200") repartía la ficha en todas las columnas. Ahora queda una sola fila con los datos comunes.
