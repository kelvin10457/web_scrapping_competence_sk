# R4.5 — Plan

## Archivos que se tocan
- `src/paises/ecuador/agrizon_parser.py`: las `etapa_*` en `parse_product`
- `tests/test_agrizon_parser.py`
- `specs/tech-stack.md`, `specs/decisiones.md`, `specs/roadmap.md`

## Pasos
1. Escribir los tests con el fixture real `tests/fixtures/agrizon_biomar_products.json`. Tienen que fallar.
2. Implementar.
3. `pytest -q -x tests/test_agrizon_parser.py` y `pipeline.py --pais ecuador --empresa biomar`.
4. Validar ≥3 productos contra la fuente real en `validation.md`.
5. `pytest -q` completo → `[x]` en el roadmap → commit `R4.5: ...`.

## ¿Cambia la constitución?
Sí, poco: en `tech-stack.md` Agrizon entra en la lista de parsers migrados, y `decisiones.md` suma los tags múltiples y el caso sin término.
