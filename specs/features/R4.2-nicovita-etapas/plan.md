# R4.2 — Plan

## Archivos que se tocan
- `src/schema.py`: reglas de `_DETECTAR_RULES` (cosecha, transferencia suelta, PL + número)
- `src/paises/_compartido/nicovita_parser.py`: `_texto_etapas` y las `etapa_*` en `parse_product`; la descripción web sin la etiqueta de categoría
- `src/pipeline.py`: `write_csv` respeta `_etapas_detectadas`
- `tests/test_schema.py`, `tests/test_nicovita_parser.py`, `tests/test_pipeline.py`
- `specs/tech-stack.md`, `specs/decisiones.md`, `specs/roadmap.md`

## Pasos
1. Escribir los tests (tienen que fallar).
2. Implementar.
3. `pytest -q -x` sobre los tres archivos de tests y `pipeline.py --pais ecuador --empresa nicovita` desde los datos guardados.
4. Validar ≥3 productos contra la ficha real en `validation.md`.
5. `pytest -q` completo → `[x]` en el roadmap → commit `R4.2: ...`.

## ¿Cambia la constitución?
Sí. `tech-stack.md` (regla de `detectar_etapas`: cosecha, transferencia suelta, PL + número; las `etapa_*` de los parsers migrados ya no salen del puente) y `decisiones.md` (las 3 decisiones de esta fase).
