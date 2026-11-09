# R4.8 — Validación

## Requisito → test
REQ-1/2/3: tests/test_apiaba_parser.py::test_etapas_de_tres_productos_reales (pasa).
REQ-3: test_etapas_no_contaminadas_por_navegacion_o_relacionados (pasa).

## Fuente real guardada
| Producto | Fixture | Fuente → parser |
|---|---|---|
| Dorado 40 | apiaba_dorado40.html | postlarval / postlarva → post_larva |
| Dorado 35 | apiaba_dorado35.html | iniciación o engorda → engorde |
| Raceways | apiaba_raceways.html | crecimiento / micropellet → vacío |

## Conteo antes → después
3 → 3 filas; filas con booleanos informados 0 → 2; una vacía. Proteínas y conflicto Dorado 35 conservados (tests anteriores verdes).

## Resultado
`.venv/bin/python -m pytest -q -x tests/test_apiaba*.py`: primero 1 fallo esperado, 6 pasan; después 8 pasan. Sin red, pipeline ni commit.

## Decisiones
- Corregir primero la premisa «sin etapa» con evidencia real; descartar conservarla ante las menciones de postlarva y engorda. Archivo: specs/features/R4.8-apiaba-etapas/requirements.md.
- Normalizar engorda a engorde para detectar; iniciación queda sin interpretación. Descartar inferir por gramos o raceways. Archivo: src/paises/mexico/apiaba_parser.py.
- Usar título y párrafos de article .entry-content; descartar texto de toda la página para excluir menú y relacionados. Archivo: src/paises/mexico/apiaba_parser.py.
