# R4.4 — Plan

## Archivos que se tocan
- `src/paises/_compartido/aquaxcel_parser.py`: las `etapa_*` en `parse_listing` (Ecuador) y `_parse_cards` (México)
- `tests/test_aquaxcel_parser.py`
- `specs/tech-stack.md`, `specs/decisiones.md`, `specs/roadmap.md`

## Pasos
1. Escribir los tests con los fixtures reales de `tests/fixtures/aquaxcel_*` (tienen que fallar).
2. Implementar.
3. `pytest -q -x tests/test_aquaxcel_parser.py`, y `pipeline.py --empresa aquaxcel` para Ecuador y México.
4. Validar ≥3 productos contra la fuente real en `validation.md`.
5. `pytest -q` completo → `[x]` en el roadmap → commit `R4.4: ...`.

## ¿Cambia la constitución?
Sí, poco: `tech-stack.md` (Aquaxcel entra en la lista de parsers migrados) y `decisiones.md` (INICIO en la columna "ETAPA DE USO" = precria).
