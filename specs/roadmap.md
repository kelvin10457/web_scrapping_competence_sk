# Roadmap

> **Orden de implementación de alto nivel.** Cada fase es chica: un cambio, sus tests y **un commit** (`<ID>: ...`). Se hacen en orden; no se empieza una fase sin cerrar la anterior, salvo que diga "en paralelo".
> Al empezar una fase se crea `specs/features/<ID>-<slug>/` a partir de `_plantilla/`. Este archivo es el **único** lugar donde se marca el estado.
> Estados: `[ ]` pendiente · `[~]` en curso · `[x]` cerrada · `[?]` espera una decisión del usuario · `[-]` descartada

## Hecho (resumen)

- [x] **Fase 1 — Ecuador** (sep. 2026): Nicovita, HAID, Aquaxcel, BioMar (vía Agrizon) y Agripac. Detalle en `docs/historico/PLAN.md`.
- [x] **Ronda 1 — Regional** (oct. 2026): columna `pais`, código por país, México (Nicovita, Aquaxcel, Vimifos, Api-Aba, Nutrimar). Detalle en `docs/historico/PLAN_REGIONAL.md`.
- [x] **Ronda 2 — Calidad de datos** (2026-10-20): registro de conflictos, Vimifos multiproteína ([spec](features/R2.2-vimifos-multiproteina/)), Api-Aba, Nutrimar con fichas, registros oficiales y GUI unificada con el CLI. Detalle en `docs/historico/RONDA2_REGIONAL.md`.

---

## R3 — Esquema nuevo (el script genera las columnas de Power BI)

Objetivo: que el CSV interno ya tenga las columnas y los nombres del Excel de Power BI, normalizados desde el origen.

- [x] **R3.1** Renombrar `producto_salud` → `es_producto_de_salud` en todo el código (schema, parsers, merge_human, GUI, tests, baseline de Ecuador). Sin cambios de lógica.
- [x] **R3.2** `schema.normalize_presentacion(texto)` con la lista oficial (`Pelletizado` → `Pellet`). Lo desconocido se devuelve tal cual. Solo la función y sus tests.
- [x] **R3.3** Los parsers usan `normalize_presentacion` al extraer: `detect_tecnologia`, Agripac y Agrizon. Se regenera Ecuador y se compara con el baseline.
- [x] **R3.4** Aviso de presentaciones desconocidas: resumen al final del CLI + `data/presentaciones_nuevas.csv` (pais, empresa, producto, valor, url).
- [x] **R3.5** Agregar las 5 columnas `etapa_*` (booleanas), derivadas por ahora del `etapa_competidor` actual. Es un paso puente: todavía marca una sola etapa por fila.
- [x] **R3.6** `etapa_skt` con la regla nueva: más de 1.6 mm → Grower (cierra el hueco de 1.6–1.8 mm y deja de depender de `tipo_presentacion`); rango → mínimo; sin tamaño → etapa del competidor como respaldo.
- [x] **R3.7** `proteina_pct` siempre numérico decimal (`37.5`), con un test que lo verifique en todas las fuentes.

## R4 — Etapas múltiples en el origen (una fase por empresa)

Objetivo: que cada parser marque **todas** las etapas que declara la fuente (por ejemplo, Térap: precria + engorde), en vez de dejar vacío cuando hay más de una.

- [x] **R4.1** `schema.detectar_etapas(texto) -> set` (función compartida + tests) y columna `etapa_post_larva`
- [x] **R4.2** Nicovita
- [x] **R4.2b** Nicovita Classic Orgánico Engorde (Honduras): usar su ficha real (el sitio enlaza la de Origin Orgánico)
- [x] **R4.3** HAID
- [x] **R4.4** Aquaxcel
- [x] **R4.5** Agrizon (BioMar)
- [x] **R4.6** Agripac
- [x] **R4.7** Vimifos (codex)
- [x] **R4.8** Api-Aba (codex)
- [x] **R4.9** Nutrimar (codex)
- [x] **R4.10** Quitar `etapa_competidor` (ya reemplazada por los booleanos). Se actualizan merge_human y el baseline.

## R5 — Excel para Power BI

- [x] **R5.1** `pipeline` escribe `data/powerbi/<pais>/<empresa>.xlsx`: selección de columnas con tipos fijos (booleano, decimal, texto). Sin transformaciones.
- [x] **R5.2** Incluir las filas cargadas a mano (`competencia_human.xlsx`) en el Excel de su país y empresa.
- [x] **R5.3** Test de contrato: todos los Excel tienen exactamente las mismas columnas, en el mismo orden y con los mismos tipos. Así Power BI los puede unir sin errores.
- [x] **R5.4** Guía `docs/powerbi.md` (1 página): cómo unir los Excel de `data/powerbi/` desde una carpeta y cómo despivotar las 5 columnas `etapa_*` para graficar por etapa. Incluye el código M listo para pegar en Power Query y la advertencia de que un producto con varias etapas se cuenta una vez en cada una.

## R6 — Nicovita reactivada, rápida y con cuidado

- [ ] **R6.1** Presupuesto de tiempo (acordado con el usuario): medir una corrida en frío. Límite: **≤3 min por país** y segundos con caché. Pausas aleatorias más cortas, y la pausa larga solo después de varias consultas nuevas (no después de las que salen de caché).
- [ ] **R6.2** Si una página muestra captcha, solo ese dominio pasa a un ritmo más lento y aleatorio. Se usa la página guardada si existe y se sigue con lo demás, sin esperar indefinidamente.
- [ ] **R6.3** Quitar Nicovita de `fuentes.INACTIVAS`. Correr Honduras, validar 3 productos y anotar el tiempo.
- [ ] **R6.4** Correr Ecuador y México, y comparar con los CSV guardados el 2026-10-20.

## R7 — México (territorio separado)

- [ ] **R7.1** Correr México completo con el esquema nuevo y revisar `presentaciones_nuevas.csv`.
- [x] **R7.2** Revisar las 144 pistas de SENASICA y listar los competidores nuevos con datos útiles (Aquatec, El Pedregal, Oromar, Skilla, Winfish Zeigler).
- [?] **R7.3** El usuario decide cuáles de esos competidores se agregan (por registro oficial o por carga manual).

## R8 — Centroamérica (Honduras, Nicaragua, Panamá)

Cada país sigue dos pasos: primero **descubrir** (solo buscar y anotar en el README del país, sin código), después **construir** (solo si apareció una fuente).

- [x] **R8.1** Honduras: buscar un registro público de alimentos para animales (SENASA).
- [-] **R8.2** Honduras: implementarlo como fuente complementaria (igual que SENASICA), si existe.
- [x] **R8.3** Nicaragua: buscar un registro público (IPSA).
- [-] **R8.4** Nicaragua: implementarlo, si existe.
- [x] **R8.5** Panamá: buscar un registro público (MIDA / APA).
- [-] **R8.6** Panamá: implementarlo, si existe.
- [x] **R8.7** Plantilla Excel de carga manual por país, con las mismas columnas, que `merge_human` importa. Puede hacerse en paralelo a R8.1–R8.6.

## R9 — Corrida completa

- [x] **R9.1** `pipeline.py` completo: los 5 países, tiempo total, nulos por columna y presentaciones nuevas. Se entregan los Excel de `data/powerbi/`.

## Después (a conversar)

- [?] Entregable / reporte de Power BI para gerencia.
- [?] Histórico vs snapshot (¿se acumulan las corridas por fecha?).
- [?] Tesseract dentro del `.exe` o como requisito de instalación.
- [?] Agripac Ecuador: 18/38 filas sin proteína (artemia/larvicultura que la fuente no publica).
