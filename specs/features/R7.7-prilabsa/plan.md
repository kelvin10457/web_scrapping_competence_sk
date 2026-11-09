# R7.7 — Plan

## Archivos que se tocan
- `src/paises/ecuador/prilabsa.py`, `prilabsa_scraper.py`, `prilabsa_parser.py` — nuevos
- `src/paises/ecuador/__init__.py`, `src/fuentes.py`, `ScraperCompetencia.spec` — registro
- `src/schema.py` — `parse_particula_range` con `<X` (REQ-6)
- `tests/test_prilabsa_parser.py`; fixture `tests/fixtures/prilabsa_catalogo_p3-23.pdf` (págs. 3–23 del PDF real, sin imágenes)

## ¿Cambia la constitución?
Sí: `tech-stack.md` (Prilabsa y el `<X` en `parse_particula_range`).
