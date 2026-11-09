# Revisión pendiente (expansion-regional)

> Lista para revisar juntos. Se actualiza después de cada commit. Arriba va el resumen final; abajo, el registro cronológico de decisiones.

## Resumen final
**Corrida:** suite 288/288 en verde. Pipeline corrido por país: Ecuador (parcial, ver bloqueo), Honduras, México, Agripac; master reconstruido. Power BI regenerado.

**Excel generados** (`data/powerbi/<pais>/<empresa>.xlsx`, 12 archivos, 288 filas, mismas 16 columnas y tipos):
Ecuador: Agripac 38 · BioMar 17 · Cargill 37 · HAID 17 · Nicovita 61 · Honduras: Nicovita 35 · México: Api-Aba 3 · Cargill 14 · Nicovita 26 · Nutrimar 6 · Vimifos 21 · Zeigler 13.

**Fases cerradas:**
- Claude: R5.1, R5.2, R5.3, R5.4, R4.10, R7.2, R8.1, R8.3, R8.5, R8.7, R9.1. Y `CLAUDE.md` (ruta Linux).
- Codex: R4.7 Vimifos, R4.8 Api-Aba, R4.9 Nutrimar (revisadas por mí; sin objeciones).
- **Pendientes:** R6 (no tocada) y R7.3 (decide el usuario). R8.2, R8.4, R8.6 descartadas (sin fuente implementable).

**Países investigados:**
- *Honduras:* marco legal SENASA y fichas Nicovita (ya en el pipeline). Sin listado público de piensos. Sin fuente nueva.
- *Nicaragua:* marco IPSA, procedimiento de registro y noticia de Cargill (2017). Sin listado público. Sin fuente nueva.
- *Panamá:* resolución APA 2021 (trámite por plataforma), catálogo Nicovita y Italcol. Sin listado público. Sin fuente nueva.
- Detalle en `src/paises/<pais>/README.md`.

**Competidores nuevos de México para decidir en R7.3:** Malta Texo (Apicamarón, 36 registros), Nueva Tecnología en Alimentación (Aquatec, 15), El Pedregal (5), Oromar (2), Multiservicios 2001 (Skilla, 2). Nutrición Marina (1, confirmar si es Nutrimar). Winfish Zeigler, Skretting y BioMar no aparecen en el registro.

**Bloqueos y páginas a guardar a mano:**
- **Agrizon (BioMar) respondió 429** en la corrida de Ecuador. No reintenté en bucle. Se conservó su CSV anterior, así que BioMar puede estar desactualizado. Para reintentar después: esperar y volver a correr `--pais ecuador --empresa biomar`. Si sigue bloqueando, guardar a mano la colección `https://agrizon.com/en/collections/nutricion-animal` (HTML) en `data/manual/` (ignorado por git, es tuyo).
- Ningún otro bloqueo (sin captcha ni 403) en Honduras, México y Agripac.

**Decisiones para revisar juntos (de la más importante a la menos):**
1. **Nicovita Origin (3 filas, 0.3–0.8 mm):** booleanos = `post_larva`, sale `Nursery`. Antes `Hatchery`. Tu ejemplo de 2026-10-29 decía Hatchery. Decidir si Origin es larva (corregir el parser) o post larva (aceptar Nursery).
2. **Regla de Hatchery (R4.10):** Hatchery si la etapa más temprana es `larva` (o Larvicultura de Agripac). Se descartó "solo larva exacto". Confirmar.
3. **Quitar `etapa_competidor` (R4.10):** las filas humanas ya no tienen etapa salvo que se pasen a booleanos (hoy ninguna lo tiene). Confirmar que es aceptable.
4. **Filas humanas sin `pais` → ecuador** (regla existente, PLAN_REGIONAL 2.5).
5. **Filas humanas no se deduplican contra el master.** Una fila humana repetida aparece dos veces en el Excel.
6. **Plantillas R8.7 con 19 columnas** (las de `merge_human`), no las 16 de Power BI.
7. **El Excel se borra si su par (pais, empresa) desaparece.** Alternativa: dejarlo.
8. **Código M de `docs/powerbi.md` sin probar en Power BI Desktop.**
9. **Nutrimar trae 13 productos de Zeigler** (la ficha de Nutrimar los publica). Ya estaban antes como Zeigler; sin cambio.

**Cómo revertir:** cada fase es un commit. R4.10 en `8fdc0ca`; R5 en `db5a5d2`, `c688b30`; R4.7–R4.9 en `5015153`; R8/R7.2 en `3a1e538`.

## Registro de decisiones y cambios

### Sesión 1 (2026-11-09)

- **Commit `edca063` — docs: ruta del Python en Linux/macOS.** CLAUDE.md ahora lista la ruta de Windows y la de Linux/macOS. Revertir: `git revert edca063`.
- **Reparto:** R5.1–R5.3 y R5.4 los hace Claude; R4.7–R4.9 los hace Codex (plugin `codex:rescue`, en segundo plano), una por vez. Codex no commitea ni toca el roadmap.
- **R5.2, `pais` faltante en `competencia_human.xlsx`:** el archivo no tiene columna `pais`. Se aplica la regla ya existente de `merge_human._with_default_pais` (fila sin país → `ecuador`, PLAN_REGIONAL 2.5). Alternativa descartada: dejarlas fuera del Excel (perdería 5 filas que el usuario cargó). Para revertir: quitar el default y excluir filas sin `pais`.
- **Commit `db5a5d2` — R5.1 + R5.2 (Claude).** `src/powerbi.py` escribe `data/powerbi/<pais>/<empresa>.xlsx` desde `data/master.csv` más `competencia_human.xlsx`. 16 columnas de tech-stack, sin `etapa_competidor`. Se llama desde `pipeline.build_master`. 12 archivos generados (ver `specs/features/R5.1-excel-powerbi/validation.md`).
  - *Decisión:* un valor no vacío que no se puede tipar (ej. `35%`, `desconocido`) queda vacío en el Excel y se imprime un AVISO. Alternativa descartada: fallar la corrida. Revertir: quitar el aviso o cambiar a error.
  - *Decisión:* al escribir, se borran los `data/powerbi/*/*.xlsx` de pares (pais, empresa) que ya no existen. Alternativa descartada: dejarlos (Power BI los seguiría uniendo con datos viejos). Revertir: quitar el `unlink` en `powerbi.escribir_todo`.
  - *Hallazgo de revisión (Codex adversarial-review, 2026-11-09):* los dos puntos de arriba salieron de esa revisión y se aplicaron. Los demás hallazgos: ninguno.
  - *Pendiente:* las filas humanas se agregan sin deduplicar contra el master. Si una fila humana repite una scrapeada, aparece dos veces. Revisar contra `merge_human` (que sí casa por nombre+pais).
- **Commit `c688b30` — R5.3 + R5.4 (Claude).** `tests/test_powerbi_contrato.py` valida los 12 Excel reales; `docs/powerbi.md` tiene la guía y el código M. *No probado en Power BI Desktop* (no disponible aquí): el código M queda sin ejecutar.
- **Commit `5015153` — R4.7, R4.8, R4.9 (Codex).** Vimifos, Api-Aba y Nutrimar marcan etapas con `detectar_etapas`. Codex corrió sus tests (10, 8 y 12 en verde). Revisé el diff contra cada spec: sin objeciones. Decisiones de Codex en cada `validation.md`.
  - *Incidente:* al correr la suite, los tests de `build_master` escribían `data/powerbi/` real con datos de prueba, y mi limpieza de archivos viejos borró 6 Excel. **Corregido:** `tests/conftest.py` redirige la salida de Power BI en todos los tests. Los Excel se restauraron desde git y se regeneraron.
- **Commit R4.10 (Claude).** `etapa_competidor` sale del esquema, de los parsers, de `merge_human` y de los tests. `etapa_skt` sale de las `etapa_*`:
  - *Decisión (pendiente de confirmar):* Hatchery si la etapa **más temprana** del ciclo es `larva` (o Larvicultura de Agripac); "en un rango manda el mínimo". Alternativa descartada: solo `larva` exacto (dejaba Larviva fuera de Hatchery). Revertir: `schema.etapa_skt_from_row`.
  - *Decisión (pendiente de confirmar):* sin tamaño, el respaldo es la etapa más temprana con mapa en `_ETAPA_SKT_RESPALDO`. Alternativa descartada: conservar `etapa_competidor` como respaldo.
  - *Efecto en Ecuador (verificado: solo cambia `etapa_skt`, 11 filas tras la corrida real):*
    - **Nicovita Origin (3 filas, 0.3–0.8 mm):** booleanos = `post_larva`, así que pasa de Hatchery a **Nursery**. Contradice el ejemplo de la decisión de 2026-10-29 (Origin es Hatchery por tipo de producto). **Decidir:** ¿Origin es larva o post larva? Si es larva, hay que corregir su detección en el parser de Nicovita.
    - **Agripac MeM/Mpex (6 filas) y New Royal Oyster, Royal Pepper Protein:** el re-derivado offline (sin red) las dejó en Nursery o vacío, porque la bandera `_es_larvicultura` del parser no está en el CSV. **Corrida real de Agripac (2026-11-09): vuelven a Hatchery.** Son la división Larvicultura, así que Hatchery viene de la bandera y no de las etapas booleanas. No hay regresión.
  - *Cómo se regeneró sin red:* `data/processed/*.csv` se re-derivó con `pipeline.write_csv` (sin scrapear) y se reconstruyó `data/master.csv`. El baseline de Ecuador (`tests/fixtures/master_ecuador_baseline.csv`) se reescribió con ese master.
  - *`merge_human`:* `etapa_competidor` se acepta en el archivo humano y se ignora (`LEGACY_COLUMNS`). Las `etapa_*` las carga el humano como booleanos (vacío = no dice nada). **Decidir:** las filas humanas cargadas con `etapa_competidor` pierden su etapa hasta que se pasen a booleanos. Hoy el archivo humano trae esa columna y ninguna fila tiene booleanos.
  - *`gui.py`:* sigue referenciando `etapa_competidor` (congelada según decisiones.md). No se adaptó.
- **Hallazgos de Codex (adversarial-review del R4.10, 2026-11-09), aplicados:**
  - *Power BI usaba `etapa_competidor` como texto en `etapa_skt_from_row`* (alto): reproducido, `'larva'` se convertía en conjunto de caracteres. **Corregido:** `filas_humanas` deriva de los booleanos. Prueba: `test_filas_humanas_usan_booleanos_no_etapa_competidor`.
  - *`is True` no reconoce `numpy.bool_`* (alto): con columnas sin nulos, una actualización ajena a etapas reclasificaba Hatchery a Nursery. **Corregido:** helper `merge_human._verdadero`. Pruebas con columnas sin nulos.
  - *Etapas humanas sin validación* (medio): `verdaderoo` se volvía `False` en silencio. **Corregido:** `ETAPA_COLUMNS` entran en `BOOLEAN_COLUMNS`. Prueba `test_validate_rows_rechaza_etapa_con_texto_que_no_es_booleano`.
  - *Hallazgo descartado:* ninguno.
- **Pasada final de R5.3:** el test de contrato pasa en los 12 Excel tras R4.10. Codex revisó el contrato en la misma revisión.
- **Power BI sin probar en Power BI Desktop:** el código M de `docs/powerbi.md` no se ejecutó aquí.

## Estado de la corrida (al cierre de esta sesión)
- **Cerradas:** R4.7–R4.9 (Codex), R4.10 y R5.1–R5.4 (Claude). Suite: 288 tests en verde.
- **Pendientes:** R8 (research y construcción de Honduras, Nicaragua, Panamá), R7.2 (pistas de SENASICA), R8.7 (plantilla manual), R9 (pipeline completo, país por país), y el `git push`.
- **Pendiente de correr:** el pipeline final (restaura la bandera de Larvicultura y re-scrapea con la caché).

## Actualización: R7.2 y R8 (research, sin implementar fuentes nuevas)

- **R8.1 Honduras, R8.3 Nicaragua, R8.5 Panamá: descubrimiento (Claude).** Se buscó con búsqueda web estándar y extendida. Ninguno de los tres países publica un listado público de alimentos registrados para camarón. Las fuentes encontradas son marcos legales o fichas de Nicovita, todas anotadas en `src/paises/<pais>/README.md`.
  - *Decisión:* R8.2, R8.4 y R8.6 quedan descartadas (`[-]`). No hay fuente pública utilizable (no hay login ni captcha, pero tampoco hay listado). Alternativa descartada: implementar el marco legal como fuente, que daría datos de registro sin productos.
  - *Pendiente de verificar a mano:* portales de SENASA (Honduras), IPSA (Nicaragua) y APA (Panamá) si existen listados que la búsqueda no encontró. Las fichas de Nicovita Honduras tienen 5–6 años.
- **R8.7 plantillas de carga manual (Claude).** `data/plantillas/plantilla_carga_manual_{honduras,nicaragua,panama}.xlsx`. *Decisión:* las 19 columnas de `schema.SCHEMA_COLUMNS`, no las 16 del contrato de Power BI, porque `merge_human` rechaza cualquier encabezado distinto (verificado: sin errores). **Nota:** `merge_human` solo lee `data/competencia_human.xlsx`; estas plantillas se copian a mano allí. Revertir: borrar `data/plantillas/plantilla_carga_manual_*.xlsx`.
- **R7.2 competidores de México en SENASICA (Claude, solo listar).** Ver `specs/features/R7.2-senasica-competidores/validation.md`. Nuevos con datos útiles: **Malta Texo (Apicamarón, 36 registros de camarón), Nueva Tecnología en Alimentación (Aquatec, 15), El Pedregal (5), Oromar (2), Multiservicios 2001 (Skilla, 2)**. Nutrición Marina (1, larval; confirmar si es Nutrimar). Winfish Zeigler, Skretting y BioMar no aparecen en el registro. Agregarlos es R7.3 (decisión tuya).
- **Estado final de R8/R7.2:** R7.2 `[x]`; R8.1, R8.3, R8.5, R8.7 `[x]`; R8.2, R8.4, R8.6 `[-]`. R6 y R7.3 no se tocaron (necesitan decisiones tuyas).
