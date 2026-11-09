# R5.1 — Plan

## Archivos que se tocan
- `src/powerbi.py` (nuevo): contrato de columnas y tipos, escritura por país/empresa
- `src/pipeline.py`: `build_master` llama a `powerbi.escribir_todo` después de escribir el master
- `tests/test_powerbi.py` (nuevo)

## Pasos
1. Tests (fallan), 2. implementar, 3. `pytest -q -x tests/test_powerbi.py`, 4. `pytest -q`, 5. `[x]` en roadmap y commit `R5.1: ...`.

## ¿Cambia la constitución?
No. Implementa la tabla que ya está en `tech-stack.md`.
