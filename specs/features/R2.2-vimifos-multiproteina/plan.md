# R2.2 — Plan

## Archivos que se tocan
- `src/paises/mexico/vimifos_parser.py`: `_proteinas()`, `_calibres()` y `_expandir_proteinas()` (fan-out a SKUs + `schema.registrar_conflicto`)
- `tests/test_vimifos_parser.py`: un test por regla
- `tests/fixtures/`: páginas reales de Vimifos

## Pasos
1. Fixture con una celda real de varias proteínas y tests de REQ-1 a REQ-5.
2. `_expandir_proteinas(record, proteina_txt, tamano_txt)` devuelve `list[dict]`.
3. `pipeline.py --pais mexico --empresa vimifos` y conteo de nulos antes y después.

## ¿Cambia la constitución?
No. Usa el registro de conflictos de R2.1, que ya está en `tech-stack.md`.
