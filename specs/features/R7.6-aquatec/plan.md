# R7.6 — Plan

## Archivos que se tocan
- `src/paises/mexico/aquatec.py`, `aquatec_scraper.py`, `aquatec_parser.py` — nuevos (modelo: El Pedregal)
- `src/paises/mexico/__init__.py`, `src/fuentes.py` (orden), `ScraperCompetencia.spec` — registro
- `tests/test_aquatec_parser.py` — un test por REQ
- `tests/fixtures/aquatec_acuicultura_1.html` — página real (2026-11-09, `curl -k` con UA de navegador)

## Pasos
1. Fixture + tests (fallan). 2. Parser sobre el texto visible (líneas). 3. `pipeline.py --pais mexico --empresa aquatec`. 4. Validar 3 SKU. 5. Revisión de Codex, suite, roadmap, commit.

## ¿Cambia la constitución?
Sí: `tech-stack.md` (etapas de AQUATEC y `verify=False` acotado).
