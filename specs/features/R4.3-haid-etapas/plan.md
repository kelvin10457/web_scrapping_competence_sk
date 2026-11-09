# R4.3 — Plan

## Archivos que se tocan
- `src/paises/ecuador/haid_parser.py`: las `etapa_*` en `parse_product`
- `tests/test_haid_parser.py`
- `specs/tech-stack.md`, `specs/decisiones.md`, `specs/roadmap.md`

## Pasos
1. Escribir los tests con las fichas reales de `data/raw/haid/` (tienen que fallar).
2. Implementar.
3. `pytest -q -x tests/test_haid_parser.py` y `pipeline.py --pais ecuador --empresa haid`.
4. Validar ≥3 productos contra la ficha real en `validation.md`.
5. `pytest -q` completo → `[x]` en el roadmap → commit `R4.3: ...`.

## ¿Cambia la constitución?
Sí, poco: `tech-stack.md` (HAID entra en la lista de parsers migrados) y `decisiones.md` (slug + PDF para HAID).
