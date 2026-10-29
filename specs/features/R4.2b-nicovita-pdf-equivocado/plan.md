# R4.2b — Plan

## Archivos que se tocan
- `src/paises/_compartido/nicovita_scraper.py`: `_PDF_CORREGIDO` y `find_pdf_url(html, url)`
- `tests/test_nicovita_parser.py`: un test por REQ, con la página real guardada en `data/raw/nicovita_html/`
- `specs/roadmap.md`, `specs/decisiones.md`, `src/paises/honduras/README.md`

## Pasos
1. Tests (fallan) → implementación → `pytest -q -x tests/test_nicovita_parser.py`.
2. `pipeline.py --pais honduras --empresa nicovita` y comparar con la ficha real.
3. `pytest -q` → `[x]` en el roadmap → commit `R4.2b: ...`.

## ¿Cambia la constitución?
No cambian el esquema ni los patrones. Se suma la decisión a `decisiones.md`.
