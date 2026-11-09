# R6.3 + R6.4 — Validación

## Requisito → test / evidencia
| REQ | Evidencia | Estado |
|---|---|---|
| REQ-1 | `tests/test_nicovita_activa.py::test_nicovita_activa_en_los_tres_paises` | ✅ |
| REQ-2 | Honduras: en frío 35 productos en 61 s (R6.1); corrida real 35 en 2.8 s; sin captcha | ✅ |
| REQ-3 | Ecuador 57 → 57 y México 26 → 26 productos; diferencias abajo | ✅ |

## Validación contra la fuente real (Honduras, 3 productos)
Las páginas `nicovita.com/productos/*-honduras/` y sus fichas PDF se bajaron hoy en frío (R6.1) y el parser no cambió. Se comparó el CSV con los datos de la ficha:

| Producto | Proteína | Tamaño | Empaque | `etapa_skt` |
|---|---|---|---|---|
| Nicovita Classic Engorde | 35 | 2.0 | 25 | Grower |
| Nicovita Classic Organic Engorde | 35 | 2.5 | 25 | Grower |
| Nicovita Katal Engorde | 35 | 1.2 | 25 | Nursery |

## Comparación contra el 2026-10-29 (`data.zip`)
Mismos productos en los 3 países (sin filas nuevas ni faltantes). Campos que cambiaron, todos con causa conocida:
- **Nicovita Origin** (Ecuador, Honduras, México) y **Origin Organic** (Honduras): `etapa_skt` pasa de Hatchery a **Nursery**. Lo causa la regla de R4.10, que ya figura como decisión n.º 1 pendiente en `revision_pendiente.md`. En México, además, `etapa_larva` pasa de True a False por el cambio de etapas de R4.2.
- **México, Nicovita Classic, Katal y Térap:** `etapa_post_transferencia` y `etapa_engorde` pasan de False a True. Lo causa R7.5: `detectar_etapas` reconoce "engorda"/"preengorda", que es como lo escriben las fichas de México.
- Contra la copia previa del día (2026-11-09): sin diferencias.

## Colaboración
- **Claude:** corridas y comparación. Sin código nuevo de scraping, así que no hubo revisión de diff de Codex (el código que usa esta corrida, `netutil`, ya lo revisó en R6.1+R6.2).

## Resultado
`pytest -q`: 331 pasan · commit: `R6.3+R6.4`
