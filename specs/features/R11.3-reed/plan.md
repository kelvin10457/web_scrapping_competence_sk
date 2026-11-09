# R11.3 — Plan

Reparto: Codex implementa (tests + código + fixtures), Claude escribió la spec y revisa el diff.

## Archivos que se tocan
- `src/paises/mexico/proaqua_scraper.py`: además del listado de `/camaron/`, baja `https://proaqua.mx/reed-mariculture/` y las fichas que pasan el filtro de Reed.
- `src/paises/mexico/proaqua_parser.py` (o un módulo `proaqua_reed_parser.py` nuevo, si queda más limpio): `productos_reed_de_listado(html)` y `parse_reed(url, html)`.
- `src/paises/mexico/proaqua.py`: despacha cada ficha a su parser.
- `tests/test_proaqua_reed.py`: un test por REQ.
- `tests/fixtures/proaqua/reed/`: `listado.html` + las 5 fichas, copiadas de `data/raw/proaqua_reed/` (descargadas 2026-11-09, reales).
- `ScraperCompetencia.spec`, solo si hay un módulo nuevo. `src/paises/mexico/README.md`: la fila de ProAqua y el párrafo de Reed.

## Pasos
1. Fixtures y tests (tienen que fallar).
2. Implementar.
3. `pytest -q -x tests/test_proaqua_reed.py tests/test_proaqua.py`, después `pipeline.py --pais mexico --empresa proaqua`.
4. Validar ≥3 productos contra la fuente real → `validation.md` (lo revisa Claude).
5. `pytest -q` completo → `[x]` en el roadmap → commit `R11.3: ...`.

## ¿Cambia la constitución?
No. El esquema no cambia.
