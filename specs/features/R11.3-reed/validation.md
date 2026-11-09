# R11.3 — Validación

Validado el 2026-11-09. Implementación en los módulos existentes de ProAqua;
no se agregó ningún módulo y no fue necesario modificar `ScraperCompetencia.spec`.

## Requisito → test

| REQ | Test | Estado |
|---|---|---|
| REQ-1 | `tests/test_proaqua_reed.py::test_listado_solo_cinco_microalgas_para_camaron` | ✅ Cinco URL exactas, seis fixtures (listado + cinco fichas), empresa Reed Mariculture y fuente mexico/proaqua activa |
| REQ-2 | `tests/test_proaqua_reed.py::test_nombres_exactos` | ✅ Los cinco nombres exactos de la spec |
| REQ-3 | `tests/test_proaqua_reed.py::test_tamano_celular_primera_dimension_en_mm` | ✅ TP 0.0045–0.008, TW 0.006–0.02, LPB 0.006–0.015 mm; los otros dos vacíos |
| REQ-4 | `tests/test_proaqua_reed.py::test_proteina_publicada_y_empaque_vacio` | ✅ LPB 52.0; las otras proteínas y todos los empaques vacíos |
| REQ-5 | `tests/test_proaqua_reed.py::test_etapas_solo_del_texto_propio_y_aplicacion_camaron` | ✅ Solo larva en Tetraselmis/TP/TW/LPB; Isochrysis sin etapa; tecnología vacía en todos |
| REQ-6 | `tests/test_proaqua_reed.py::test_scraper_y_run_preservan_las_doce_filas_y_agregan_cinco` y `tests/test_proaqua.py` | ✅ Integración listado→descarga→run: 17 filas, las 12 anteriores idénticas; módulos incluidos en el empaquetado |

`tests/test_proaqua.py::test_listado_solo_formulados` continúa pasando: el
`glob("*.html")` del directorio padre no incluye los fixtures del subdirectorio `reed/`.

Los seis tests nuevos se ejecutaron antes de implementar: **6 fallaron** (faltaban
las funciones Reed y la integración devolvía 12 filas en lugar de 17).

## Validación contra la fuente real (≥3 productos)

Descarga directa con `curl -fLsS --max-time 90 -A 'Mozilla/5.0 (Windows NT 10.0;
Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'`.
Las tres respuestas HTML se guardaron en `/tmp/r113-reed-vivo/` (`tp.html`,
`tw.html`, `lpb.html`). Se inspeccionó `#ProductDescription` y se comparó el
resultado del parser sobre cada respuesta con `data/processed/mexico/proaqua.csv`.

Fuentes:

- [TP 1800](https://proaqua.mx/concentrado-de-microalga-instant-algae-tp-1800-thalassiosira-pseudonana/)
- [TW 1200](https://proaqua.mx/concentrado-de-microalga-instant-algae-tw-1200-thalassiosira-weissflogii/)
- [LPB](https://proaqua.mx/concentrado-de-microalgas-lpb-para-larvas-juveniles-y-reproductores-de-reed-mariculture/)

| Producto | Campo | Evidencia de la fuente viva | CSV generado |
|---|---|---|---|
| TP 1800 | Nombre | Título Instant Algae TP 1800 con prefijo comercial y especie entre paréntesis | `Instant Algae TP 1800` |
| TP 1800 | Tamaño celular | Primera dimensión 4,5–8 μm; segunda dimensión 6–10 μm | `0.0045-0.008` mm |
| TP 1800 | Proteína | No publica porcentaje de proteína; los porcentajes de ácidos grasos no se usan | Vacío |
| TP 1800 | Etapas | Párrafo propio describe uso en larvicultura de camarón | `etapa_larva=True`, las otras cinco `False` |
| TP 1800 | Tecnología / empaque kg | Sin tecnología reconocida en el párrafo propio ni peso publicado en kg | Ambos vacíos |
| TW 1200 | Nombre | Título Instant Algae TW 1200 con prefijo comercial y especie entre paréntesis | `Instant Algae TW 1200` |
| TW 1200 | Tamaño celular | Primera dimensión 6–20 μm; segunda dimensión 8–15 μm | `0.006-0.02` mm |
| TW 1200 | Proteína | No publica porcentaje de proteína | Vacío |
| TW 1200 | Etapas | Párrafo propio indica aplicación en camarón larvario | `etapa_larva=True`, las otras cinco `False` |
| TW 1200 | Tecnología / empaque kg | Sin tecnología reconocida en el párrafo propio ni peso publicado en kg | Ambos vacíos |
| LPB | Nombre | Encabezado de descripción con letras L, P y B separadas, seguido de Frozen Shellfish Diet | `LPB Frozen Shellfish Diet` |
| LPB | Tamaño celular | Datos técnicos: tamaño celular de 6–15 micrones | `0.006-0.015` mm |
| LPB | Proteína | Composición de biomasa seca: proteína superior al 52,0 % | `52` en CSV; `52.0` numérico en parser |
| LPB | Etapas | Aplicaciones → Camarón: suplemento para larvas con síndrome de zoea | `etapa_larva=True`, las otras cinco `False` |
| LPB | Tecnología / empaque kg | Aplicación para camarón sin tecnología reconocida; no publica peso en kg | Ambos vacíos |

La tecnología de LPB se evalúa exclusivamente en su aplicación para camarón:
la apariencia líquida al descongelarse, publicada en datos técnicos, no se
traslada a ese campo. Tampoco se usan el encabezado para bivalvos ni las dosis
N, Z1–M3 para detectar etapas. Coincidencia de todos los campos comprobados.

## Conteo antes → después

| Medida en ProAqua México | Antes (R7.9) | Después (R7.9 + R11.3) |
|---|---:|---:|
| Filas totales | 12 | 17 |
| Biogrow | 7 | 7 |
| Epicore | 5 | 5 |
| Reed Mariculture | 0 | 5 |
| Nulos en `tamano_pellet_mm` | 1 | 3 |
| Nulos en `proteina_pct` | 0 | 4 |
| Nulos en `empaque_kg` | 6 | 11 |
| Nulos en `tipo_presentacion` | 4 | 9 |
| Nulos en `etapa_larva` | 3 | 4 |
| Conflictos registrados de ProAqua | 0 | 0 |

`data/processed/mexico/_conflictos.csv` conserva su único conflicto previo,
de otra fuente (1 → 1); esta fase no agrega conflictos. Las 12 filas anteriores
se compararon también contra el CSV guardado antes del pipeline, excluyendo
`fecha_extraccion`: todos los demás campos son idénticos. El test de integración
compara los registros completos de ambos parsers para R7.9.

## Resultado

- `.venv/bin/python -m pytest -q -x tests/test_proaqua_reed.py tests/test_proaqua.py`: **12 passed in 1.68s**.
- `.venv/bin/python -m pytest -q`: **372 passed in 36.42s**.
- `.venv/bin/python src/pipeline.py --pais mexico --empresa proaqua`: **OK: 17 productos**, CSV y Excel de ProAqua generados, maestros regenerados y Excel de Reed Mariculture para Power BI creado.
- Se conservaron las salidas afectadas por Reed; se revirtió la regeneración de Excel de otras fuentes que el pipeline vuelve a escribir.
- Sin commit, sin cambios propios al roadmap y sin tocar `docs/historico/`, según la instrucción del usuario. Los cambios previos del usuario en `specs/decisiones.md` y `specs/roadmap.md` se conservaron.

## Discrepancias

Ninguna entre la spec y las fichas locales o los tres productos contrastados
con la fuente en vivo.
