# R3.5 — Plan

## Archivos que se tocan
- `src/schema.py`: `ETAPA_COLUMNS`, `etapas_desde_competidor()` y las 5 columnas en `SCHEMA_COLUMNS`
- `src/pipeline.py`: `write_csv` completa las 5 columnas (mismo lugar donde hoy se deriva `etapa_skt`)
- `src/merge_human.py`: las 5 pasan a `DERIVED_COLUMNS`, son opcionales en los encabezados y se recalculan al fusionar
- `tests/test_schema.py`, `tests/test_pipeline.py`, `tests/test_merge_human.py`: un test por REQ
- `tests/fixtures/master_ecuador_baseline.csv`: se le agregan las 5 columnas derivadas de su propio `etapa_competidor` (el resto no cambia)

## Pasos
1. Escribir los tests (tienen que fallar). 2. Implementar. 3. Correr los tests de lo tocado y `pipeline.py --pais ecuador`.
4. Validar contra el master y completar `validation.md`. 5. `pytest -q` → roadmap → commit.

## ¿Cambia la constitución?
Sí: en `tech-stack.md` se aclara que, por ahora, las etapa_* se derivan de `etapa_competidor` (TRUE en una, FALSE en las demás). En `decisiones.md` se registra la decisión TRUE/FALSE.
