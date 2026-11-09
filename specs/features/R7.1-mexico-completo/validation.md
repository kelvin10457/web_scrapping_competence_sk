# R7.1 — Validación

## Requisito → evidencia
| REQ | Evidencia | Estado |
|---|---|---|
| REQ-1 | Corrida 2026-11-09: 7 fuentes OK en 48.6 s, sin bloqueos. Nicovita 26, Aquaxcel (Cargill) 14, Vimifos 21, Api-Aba 3 (1 conflicto resuelto), Nutrimar 19 (6 Nutrimar + 13 Zeigler), El Pedregal 36, AQUATEC 11 → **130 filas** en el master de México | ✅ |
| REQ-2 | `presentaciones_nuevas.csv`: **ninguna de México**. Su única fila es de Ecuador: BioMar "Exia Prime" con `Microgranulado` (tag de agrizon.com). No es de esta fase y queda en `revision_pendiente.md` para que el usuario decida si se agrega a la lista oficial | ✅ |
| REQ-3 | `tests/test_powerbi_contrato.py` en verde | ✅ |

## Validación contra la fuente real (≥3 productos)
Productos de México validados hoy contra la fuente en sus fases: AQUATEC 45% Migaja HD (R7.6), El Pedregal (R7.5) y Nicovita Classic, Katal y Térap (R6.4, etapas). Esta corrida no cambió ningún parser.

## Nulos en México (130 filas)
`proteina_pct` 1 · `tamano_pellet_mm` 10 · `tipo_presentacion` 49 · `empaque_kg` 61 · `etapa_skt` 5. Los vacíos son de la fuente: no publica el dato, o es migaja sin grafía oficial.

## Colaboración
Corrida de Claude. Sin diff de código, así que no hubo revisión de Codex.

## Resultado
`pytest -q`: 331 pasan · commit: `R7.1`
