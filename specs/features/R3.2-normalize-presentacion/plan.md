# R3.2 — Plan

## Archivos que se tocan
- `src/schema.py` — `TIPO_PRESENTACION_OFICIAL` y `normalize_presentacion()`
- `tests/test_schema.py` — un test por REQ

Fixture: no aplica (función pura). Los casos de prueba usan los valores reales del CSV maestro actual.

## Pasos
1. Tests (fallan).
2. Implementar.
3. `pytest -q -x tests/test_schema.py`.
4. `validation.md` → `pytest -q` → `[x]` en el roadmap → commit `R3.2: ...`.

## ¿Cambia la constitución?
No.
