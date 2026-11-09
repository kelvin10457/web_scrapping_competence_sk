# R8.9 — Plan

## Archivos que se tocan
- `src/registros_oficiales.py` — `parse_mida_nacional`, `parse_mida_pga`, `registros_mida`, descarga en `actualizar()`
- `tests/test_registros_mida.py` — un test por REQ
- `tests/fixtures/mida/*.pdf` — los dos PDF reales (descargados el 2026-11-09)

## Pasos
1. Fixtures y tests (fallan).
2. Nacional con `extract_tables()`; PGA con `extract_words()`: columnas por la x del encabezado y filas ancladas en el `RA-…`; cada línea suelta va al ancla más cercana (empate → la siguiente, como `PANCHO'S` / `KITCHEN S.A.`).
3. `pytest -q -x tests/test_registros_mida.py` y `pipeline.py --actualizar-registros` (o equivalente).
4. Validar 3 registros contra los PDF y completar `validation.md`.

## ¿Cambia la constitución?
Sí: `tech-stack.md` suma MIDA a las fuentes de registros oficiales.
