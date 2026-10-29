# R4.6 — Plan

## Archivos que se tocan
- `src/paises/ecuador/agripac_parser.py`: las `etapa_*` en `parse_product`
- `tests/test_agripac_parser.py` y fixtures reales nuevos (`agripac_larfeed.html`, `agripac_vitellus_small.html`, `agripac_mpex_100_200.html`, `agripac_new_royal_oyster.html`, `agripac_royal_pepper_protein.html`)
- `specs/tech-stack.md`, `specs/decisiones.md`, `specs/roadmap.md`, baseline de Ecuador

## Pasos
1. Escribir los tests con fixtures reales. Tienen que fallar.
2. Implementar.
3. `pytest -q -x tests/test_agripac_parser.py` y `pipeline.py --pais ecuador --empresa agripac`.
4. Validar ≥3 productos contra la fuente real en `validation.md`.
5. `pytest -q` completo → `[x]` en el roadmap → commit `R4.6: ...`.

## ¿Cambia la constitución?
Sí, poco: en `tech-stack.md` Agripac entra en la lista de parsers migrados.
