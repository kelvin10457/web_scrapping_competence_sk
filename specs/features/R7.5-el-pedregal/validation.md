# R7.5 — Validación

## Requisito → test
| REQ | Test | Estado |
|---|---|---|
| REQ-1 | `tests/test_elpedregal_parser.py::test_urls_de_imagenes_y_tabla_mp` | ✅ |
| REQ-2 | `::test_una_fila_por_tamano_y_tipo_por_linea` | ✅ |
| REQ-3 | `::test_proteina_y_diametro_con_punto_perdido_por_ocr` | ✅ |
| REQ-4 | `::test_detectar_etapas_engorda_y_preengorda`, `::test_etapas_por_seccion_y_uso` | ✅ |
| REQ-5 | `::test_tabla_migajas_post_larva` | ✅ |
| REQ-6 | `::test_registrada_en_mexico` | ✅ |

## Validación contra la fuente real (≥3 productos, 2026-11-09)
| Producto | Campo | Fuente dice | CSV dice |
|---|---|---|---|
| Microtek Crustáceos BD (45-11) (imagen 2) | proteína / tamaños | 45 %; micropartículas 200, 300, 500 µm; micropelets 0.6, 0.8, 1.0, 1.4 mm | 45; 0.2/0.3/0.5 Microparticulado; 0.6/0.8/1/1.4 Extruido |
| Microtek Crustaceos RC (40-10) (imagen 2) | proteína / tamaños / etapa | 40 %; 0.8, 1.0, 1.4 mm; "Postlarvas", PL 22 a 3 g | 40; 0.8/1/1.4; post_larva |
| Engorda Extruido 2.1 mm BD (25-8) SHP (imagen 5) | proteína / tamaño | 25 %; "Pelets: 2.1 x 3 mm" (OCR leyó "21x 3") | 25; 2.1; Extruido; engorde |
| Migajas # 1 Peletizado (45-9) (`?t=mp`) | tamaño / proteína | 0.600 - 0.850; 45 | 0.6-0.85; 45; Pellet; post_larva |

## Conteo antes → después
- `mexico/elpedregal`: 0 → 36 filas (imágenes 4 + 12 + 6 + 3 + 3; migajas 8). Sin conflictos.
- El cambio en `detectar_etapas` no altera Nutrimar, Vimifos ni Apiaba (Nutrimar sale idéntico con el `schema.py` anterior; las diferencias de Ez-mate/Redi-mate contra el CSV viejo vienen de R4.9).

## Resultado
`pytest -q`: 297 pasan · commit: ver `git log` (R7.5)
