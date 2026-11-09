# R4.7 — Validación

## Requisito → test
| REQ | Test en tests/test_vimifos_parser.py | Resultado |
|---|---|---|
| 1 | test_etapas_explicitas_por_sku | pasa |
| 2 | test_sin_etapa_explicita_no_infiere_por_peso_o_tamano | pasa |
| 3 | test_cosecha_marca_engorde_en_todas_las_proteinas | pasa |

## Fuente real guardada
| Producto | Fixture | Fuente → parser |
|---|---|---|
| Xtrudix 00 | vimifos_xtrudix.html | PL'S A 500 MG → post_larva |
| Strong Breed | vimifos_strong_breed.html | REPRODUCTORES → reproductores |
| Special Race Way | vimifos_race_way.html | INICIACIÓN / pesos → vacío |
| Bumper Crop 30/35/40% | vimifos_bumper_crop.html | 3G A COSECHA → engorde |

## Conteo antes → después
13 → 13 filas en estos cuatro fixtures; booleanos informados: 0 → 5 filas; las otras 8 quedan vacías. Sin cambios de proteínas, tamaños o conflictos.

## Resultado
`.venv/bin/python -m pytest -q -x tests/test_vimifos*.py`: primero 1 fallo esperado y 7 pasan; después 10 pasan. Validación offline, sin pipeline ni commit.

## Decisiones
- Usar encabezado + peso por columna; descartar texto global y presentación para no mezclar SKU. Archivo: src/paises/mexico/vimifos_parser.py.
- Normalizar «A COSECHA» a «hasta cosecha» antes del detector; descartar inferencia por gramos/calibre y cambios fuera de alcance en schema.py. La grafía real se anotó en requirements.md antes de implementar. Archivo: src/paises/mexico/vimifos_parser.py.
- Conservar etapa_competidor legado y heredar booleanos/marcador al expandir proteínas; descartar migración R4.10 anticipada. Archivo: src/paises/mexico/vimifos_parser.py.
