# R3.1 — Plan

## Archivos que se tocan
- `src/schema.py`, `src/merge_human.py`, `src/gui.py`, parsers de `src/paises/` — rename
- `tests/test_*.py` y `tests/fixtures/master_ecuador_baseline.csv` — rename

## Pasos
1. `sed 's/producto_salud/es_producto_de_salud/g'` sobre los archivos de `src/` y `tests/` que lo contienen (también renombra `detect_producto_salud` → `detect_es_producto_de_salud`).
2. `git grep` para confirmar REQ-2.
3. `pytest -q` completo.

## ¿Cambia la constitución?
No: `tech-stack.md` ya usaba el nombre nuevo.
