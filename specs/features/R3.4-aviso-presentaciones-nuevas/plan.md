# R3.4 — Plan

## Archivos que se tocan
- `src/schema.py` — `presentaciones_nuevas(df)` y `PRESENTACION_NUEVA_COLUMNS`
- `src/pipeline.py` — `build_master` escribe `data/presentaciones_nuevas.csv`; `main` imprime el resumen
- `tests/test_schema.py`, `tests/test_pipeline.py` — un test por REQ, con filas reales del master de Ecuador

## Pasos
1. Tests (fallan). 2. Implementar. 3. Tests de lo tocado y `pipeline.py --pais ecuador --empresa agrizon`.
4. Validar contra el master y completar `validation.md`. 5. `pytest -q` → roadmap → commit.

## ¿Cambia la constitución?
No: `tech-stack.md` ya describe el archivo y el resumen.
