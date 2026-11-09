# R4.1 — Plan

## Archivos que se tocan
- `src/schema.py`: `ETAPAS`, `_DETECTAR_RULES`, `detectar_etapas`, `columnas_etapa`, `etapa_post_larva` en `SCHEMA_COLUMNS`/`ETAPA_COLUMNS` y el respaldo `post_larva` → Nursery
- `tests/test_schema.py`: un test por REQ, con frases reales de `tests/fixtures/` (Nutrimar, Api-Aba, Aquaxcel) y de Nicovita Térap
- `specs/tech-stack.md`, `specs/decisiones.md`, `specs/roadmap.md`

## Pasos
1. Escribir los tests (tienen que fallar).
2. Implementar.
3. Correr `pytest -q -x tests/test_schema.py tests/test_pipeline.py tests/test_merge_human.py`.
4. No hay scraping: la validación es contra frases reales de las fuentes, en `validation.md`.
5. `pytest -q` completo → marcar `[x]` en el roadmap → commit `R4.1: ...`.

## ¿Cambia la constitución?
Sí. `tech-stack.md` suma la fila `etapa_post_larva` y la regla de `detectar_etapas`; `decisiones.md` suma las 3 decisiones del 2026-10-29.
