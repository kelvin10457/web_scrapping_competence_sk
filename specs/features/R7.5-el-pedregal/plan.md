# R7.5 — Plan

## Archivos que se tocan
- `src/schema.py` — `detectar_etapas`: "engorda" y "preengorda".
- `src/paises/mexico/elpedregal_scraper.py` — página principal, imágenes (OCR con pytesseract, mismo setup que HAID) y `?t=mp`.
- `src/paises/mexico/elpedregal_parser.py` — bloques OCR y tabla HTML.
- `src/paises/mexico/elpedregal.py`, `__init__.py`, `fuentes.EMPRESA_ORDER`, `ScraperCompetencia.spec`.
- `tests/test_elpedregal_parser.py`, `tests/test_schema.py`.
- `tests/fixtures/elpedregal_crustaceos.html`, `elpedregal_crustaceos_t_mp.html`, `elpedregal_info{1..5}.ocr.txt` (salida real de `tesseract -l spa` sobre las imágenes del 2026-11-09).

## Pasos
1. Fixtures y tests (fallan). 2. Implementar. 3. `pytest -q -x tests/test_elpedregal_parser.py`, `pipeline.py --pais mexico --empresa elpedregal`. 4. Validar 3 productos. 5. Suite completa, roadmap, commit.

## ¿Cambia la constitución?
Sí: `tech-stack.md` (El Pedregal usa OCR de imágenes) y `decisiones.md` (fuentes y "preengorda").
