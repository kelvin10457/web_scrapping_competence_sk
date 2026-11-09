# Revisión pendiente (expansion-regional)

> Lista para revisar juntos. Se actualiza después de cada commit. Arriba va el resumen final; abajo, el registro cronológico de decisiones.

## Resumen final
_Se completa al cerrar la corrida (ver CIERRE del pedido)._

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
  - *Efecto en Ecuador (verificado: solo cambia `etapa_skt`, 11 filas):*
    - **Nicovita Origin (3 filas, 0.3–0.8 mm):** booleanos = `post_larva`, así que pasa de Hatchery a **Nursery**. Contradice el ejemplo de la decisión de 2026-10-29 (Origin es Hatchery por tipo de producto). **Decidir:** ¿Origin es larva o post larva? Si es larva, hay que corregir su detección en el parser de Nicovita.
    - **Agripac MeM/Mpex (6 filas):** `post_larva` desde R4.6, pasan a **Nursery** (regla de post larva sin tamaño). Antes salían Hatchery por la etapa vieja; R4.6 ya los había movido a post larva y el skt no se había recalculado.
    - **Agripac New Royal Oyster y Royal Pepper Protein (2 filas):** pierden Hatchery porque la bandera `_es_larvicultura` del parser no está en el CSV. **Se restaura con el pipeline final**, que vuelve a correr el parser de Agripac. Si el pipeline final no corre, quedan vacías.
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
