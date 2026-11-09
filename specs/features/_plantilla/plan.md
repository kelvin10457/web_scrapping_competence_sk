# <ID> — Plan

## Archivos que se tocan
- `src/...` — qué cambia
- `tests/...` — tests nuevos (uno por REQ)
- `tests/fixtures/...` — fixture real (descargado, no armado a mano)

## Pasos
1. Guardar el fixture y escribir los tests (tienen que fallar).
2. Implementar.
3. Correr `pytest -q -x tests/test_<x>.py`, después `pipeline.py --pais <p> --empresa <e>`.
4. Validar contra la fuente real y completar `validation.md`.
5. `pytest -q` completo → marcar `[x]` en el roadmap → commit `<ID>: ...`.

## ¿Cambia la constitución?
No / Sí: qué cambia en `mission.md` o `tech-stack.md` (va en el mismo commit).
