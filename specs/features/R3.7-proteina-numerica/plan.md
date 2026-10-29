# R3.7 — Plan

## Archivos que se tocan
- `src/schema.py` — `normalize_proteina()`
- `src/paises/ecuador/{agripac,agrizon,haid}_parser.py`, `src/paises/_compartido/{aquaxcel,nicovita}_parser.py`, `src/paises/mexico/{apiaba,nutrimar,vimifos}_parser.py` — asignan `proteina_pct` con `normalize_proteina`; los regex aceptan coma decimal
- `tests/test_schema.py` — REQ-1
- `tests/test_proteina_fuentes.py` — REQ-2 (transversal, fixtures existentes)
- Tests de Agripac/Agrizon que esperaban `"35"` pasan a `35.0`

## Pasos
1. Tests (tienen que fallar).
2. Implementar.
3. `pytest -q -x` de los tests tocados; regenerar los masters y comparar `proteina_pct` (REQ-3).
4. Validar ≥3 productos contra la fuente y completar `validation.md`.
5. `pytest -q` completo → `[x]` en el roadmap → commit.

## ¿Cambia la constitución?
Sí: `tech-stack.md` menciona `normalize_proteina` en la fila de `proteina_pct`.
