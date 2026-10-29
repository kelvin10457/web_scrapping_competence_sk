# R3.3 — Plan

## Archivos que se tocan
- `src/schema.py` — `detect_tecnologia` normaliza; alias nuevos; umbral Grower acepta `Pellet`
- `src/paises/ecuador/agripac_parser.py` — pestaña "Tipo" → `normalize_presentacion`
- `src/paises/ecuador/agrizon_parser.py` — respaldo `Microgranulado`
- `src/paises/_compartido/aquaxcel_parser.py` — `normalize_presentacion`
- `tests/test_schema.py`, `test_agripac_parser.py`, `test_agrizon_parser.py`, `test_aquaxcel_parser.py`, y los que esperaban `Pelletizado`
- `tests/fixtures/agripac_mem.html` — ficha real de MeM
- `tests/fixtures/master_ecuador_baseline.csv` — se actualiza tras revisar el diff

## Pasos
1. Fixture + tests (fallan). 2. Implementar. 3. Tests de lo tocado y `pipeline.py --pais ecuador`.
4. Diff contra baseline, validar ≥3 productos y completar `validation.md`. 5. `pytest -q` → roadmap → commit.

## ¿Cambia la constitución?
No: `tech-stack.md` ya tenía la lista oficial. Las decisiones van a `decisiones.md`.
