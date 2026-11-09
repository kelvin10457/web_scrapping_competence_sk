# R3.6 — Plan

## Archivos que se tocan
- `src/schema.py`: `etapa_skt_from_row(etapa_competidor, tamano_pellet_mm, es_larvicultura=False)`, sin `tipo_presentacion`
- `src/pipeline.py`, `src/merge_human.py`: llamadas sin `tipo_presentacion`
- `tests/test_schema.py`: tests de `etapa_skt` reescritos, uno por REQ
- `tests/fixtures/master_ecuador_baseline.csv`: si cambia `etapa_skt`, se regenera y se documenta el diff

## Pasos
1. Tests (fallan). 2. Implementar. 3. `pytest -q -x tests/test_schema.py` y regenerar por país.
4. Comparar `etapa_skt` antes y después en el master y validar ≥3 productos. 5. `pytest -q` → roadmap → commit.

## ¿Cambia la constitución?
Sí: en `tech-stack.md`, Hatchery por larva no depende de que falte el tamaño, y se agrega la tabla de respaldo. En `decisiones.md` se registra la tabla de respaldo.
