# R4.9 — Validación

## Requisito → test
| REQ | Test en tests/test_nutrimar_parser.py | Resultado |
|---|---|---|
| 1, 2, 4 | test_etapas_fichas_reales_y_expansion_sku | pasa |
| 3 | test_etapas_sin_ficha_desde_nombre_y_pagina_sin_inferir | pasa |
| 4 | test_ficha_tiene_prioridad_y_retorno_ocr_conserva_marcador | pasa |
| 3 | test_etapas_web_excluyen_menu_footer_y_scripts | pasa |

## Fuente real guardada
| Producto | Fixture | Fuente → parser |
|---|---|---|
| EZ Larva | nutrimar_ez_larva.html | EZ Larva → larva |
| Intensivo | nutrimar_intensivo.html | adulto, crecimiento, sin etapa explícita → vacío |
| PL Raceway 40-9 | nutrimar_ficha_pl_raceway_40_9.txt | post larvas, nursery, hasta el engorde → post_larva + precria + post_transferencia + engorde |
| Semi-intensivo | nutrimar_ficha_semi_intensivo.txt | ENGORDA, hasta la cosecha → engorde en ambos SKU |
| Extensivo | nutrimar_ficha_extensivo_ocr.txt | solo análisis nutricional → vacío |

Las pruebas de fichas reutilizan el HTML de Intensivo como contenedor, igual que los tests previos; se validan las etapas del TXT, no se afirma que ese HTML corresponda a PL Raceway o Semi-intensivo. No se consultaron sitios ni se generaron CSV.

## Conteo antes → después
6 → 6 filas en los cinco casos reales anteriores (Semi-intensivo aporta dos); filas con booleanos informados 0 → 4; dos vacías. Nutrientes/calibres/conflictos originales conservados, ver tests previos.

## Resultado
`.venv/bin/python -m pytest -q -x tests/test_nutrimar*.py`: primero 1 fallo esperado, 8 pasan; después 12 pasan. Sin red, pipeline, suite completa ni commit.

## Decisiones
- Priorizar nombre + ficha completa; sin ficha usar nombre + párrafos/encabezados de main. Descartar HTML global, slug y categorías por contaminación. Archivo: src/paises/mexico/nutrimar_parser.py.
- Aplicar el rango compartido nursery → engorde de PL Raceway, conservando todas las etapas detectadas; descartar elegir solo post_larva o inferir desde gramos. Archivo: src/paises/mexico/nutrimar_parser.py.
- Normalizar ENGORDA a engorde, sin traducir adulto/crecimiento a etapas. Descartar respaldo por calibre. Archivo: src/paises/mexico/nutrimar_parser.py.
- Calcular etapas antes de todos los retornos y expansión multiproteína; descartar delegar al puente del pipeline. Archivo: src/paises/mexico/nutrimar_parser.py.
