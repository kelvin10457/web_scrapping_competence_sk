# Decisiones vigentes

> Una línea por decisión tomada por el usuario, con su fecha. Si una decisión cambia, se tacha la anterior y se agrega la nueva debajo. La evidencia y el contexto completo están en `docs/historico/MEMORY.md` (sección "Decisiones tomadas en conversación con el usuario" y el historial del esquema).

## Método
- **Sin LLM ni APIs pagas**, por costo. Todo con regex o keywords.
- **2026-08-31:** el OCR local (Tesseract) sí está permitido.
- Un parser por empresa, no por producto.

## Esquema
- **2026-09-02:** se quitan `fibra_pct`, `ceniza_pct`, `humedad_pct`, `estabilidad_agua_min` y los campos cualitativos. Marca y submarca van dentro de `nombre_producto`.
- **2026-09-02:** `salud` deja de ser una etapa. Pasa a ser la columna booleana `producto_salud`.
- **2026-09-02:** se agrega la clasificación de 4 etapas de la jefatura (hoy `etapa_skt`), separada de la etapa que publica el competidor.
- **2026-09-03:** `particula_min_mm` y `particula_max_mm` se derivan de `tamano_pellet_mm`, que se mantiene como texto.
- **2026-09-03:** cada CSV tiene un `.xlsx` espejo con columnas numéricas reales (Excel en español corrompe los decimales).
- **2026-09-15:** se quita `grasa_pct`.
- **2026-09-15:** renombres: `etapa` → `etapa_competidor` y `clasificacion_camaron` → `etapa_skt`.
- **2026-10-19:** se agrega `pais` como primera columna. Indica dónde se vende, no dónde se fabrica.
- **2026-10-28:** el destino final es un **Excel por país y empresa** (`data/powerbi/<pais>/<empresa>.xlsx`) para unir en Power BI. Columnas en `tech-stack.md`. Se agregan `empresa` y `etapa_skt` a la lista del usuario.
- **2026-10-28:** la etapa del competidor pasa a 5 booleanos (`etapa_reproductores`, `etapa_larva`, `etapa_precria`, `etapa_post_transferencia`, `etapa_engorde`). `post_transferencia` tiene columna propia.
- **2026-10-28:** `etapa_skt` es una sola columna, calculada por tamaño de pellet (criterio propio de Skretting). En un rango manda el mínimo; sin tamaño, se usa la etapa del competidor como respaldo.
- **2026-10-28:** cortes de `etapa_skt`: menos de 1.6 mm → Nursery; 1.6 mm → Pre Grower; más de 1.6 mm → Grower (1.7 mm es Grower). Se elimina la distinción 1.8 pellet / 1.9 extruido.
- **2026-10-28:** `proteina_pct` va como porcentaje decimal (`37.5`).
- **2026-10-28:** lista oficial de `tipo_presentacion` (ver `tech-stack.md`); `Pelletizado` pasa a `Pellet`. Se normaliza al extraer, no al final. Los valores nuevos no son error: se conservan y se avisan.
- **2026-10-29:** Agripac MeM queda `Microextruido` (valor oficial), no `Extruido`. El tag `Microgranulado` de Agrizon se conserva tal cual (no se fuerza a `Granulado`) y lo avisará R3.4.

## Fuentes
- **2026-09-03:** BioMar solo por Agrizon. biomar.com queda deshabilitado aunque se pierdan productos sin match (los módulos se conservan).
- **2026-10-20:** Nicaragua y Panamá **no** duplican las filas de Honduras. Se cargan a mano.
- **2026-10-20:** HAID y Agripac solo en Ecuador.
- **2026-10-20:** Fase 5 (SENASICA / eaduana) ejecutada como fuente complementaria. Nunca pisa un dato del sitio.
- ~~**2026-10-20:** Nicovita pausada en todos los países (`fuentes.INACTIVAS`).~~
- **2026-10-28:** Nicovita se reactiva con cuidado: pausas aleatorias solo para las páginas problemáticas, con un límite de ≤3 min por país en la primera corrida, sin caché (roadmap R6).
- **2026-10-29:** Nicovita sale de `fuentes.INACTIVAS`: corrió sin captcha en Ecuador (57, 2 min 56 s), México (26) y Honduras (38).
- **2026-10-29:** Pausas de `netutil` más irregulares: corta triangular 1.5–7 s (moda 2.5), larga 15–40 s cada 3–6, reintentos con +0–50 % al azar y nunca menos que `Retry-After`.
- **2026-10-29:** Agrizon (complemento de BioMar) pasa a `netutil.PACED_HOSTS` con las mismas pausas aleatorias que Nicovita, tras responder 429 el 2026-10-28.
- **2026-10-28:** Centroamérica: buscar registros oficiales de cada país; lo que no aparezca se carga a mano con una plantilla.
- No se borran módulos viejos que quedan sin uso.

## Salida
- **2026-09-01:** `master.csv` es snapshot y se sobrescribe. Es provisorio (ver [roadmap](roadmap.md)).
- **2026-10-29:** La prioridad es que los datos se puedan analizar; el dashboard lo arma el usuario y la gerencia no necesita correr el script. La GUI (`gui.py`) queda congelada: no se le agregan funciones nuevas ni se la adapta al esquema nuevo, y tampoco se borra. Las salidas y los avisos van solo por CLI y archivos en `data/`.
- **2026-10-29:** `merge_human.py` probablemente se reemplace por archivos aislados por país y empresa (para completar a mano sin un Excel gigante). ~~Mientras tanto no se adapta al esquema nuevo.~~ Cambiado el mismo día: sí se adapta (ver abajo).
- **2026-10-29:** puente R3.5: las `etapa_*` se derivan de `etapa_competidor`, que queda en `true`; las otras 4 van en `false` (no vacías). Sin `etapa_competidor`, las 5 quedan vacías. En el Excel manual son derivadas y opcionales.
- **2026-10-29:** `merge_human.py` se adapta al esquema nuevo a medida que avanza R3 (las columnas derivadas se recalculan y el Excel manual no necesita traerlas). La GUI sigue congelada.
- **2026-10-29:** respaldo de `etapa_skt` sin tamaño: `larva` → Hatchery, `precria` → Nursery, `post_transferencia` → Pre Grower, `engorde` → Grower, `reproductores` → vacío. `larva` (y Larvicultura de Agripac) es Hatchery aunque tenga tamaño.
- **2026-10-29:** se agrega el booleano `etapa_post_larva`, entre `etapa_larva` y `etapa_precria`: la post larva es una fase intermedia entre larva y precría. "post larva" / "PL" deja de marcarse como `larva`. En `etapa_skt` sin tamaño, `post_larva` → Nursery. Se implementa dentro de R4.1.
- **2026-10-29:** en un rango de etapas ("post larva hasta tamaño de mercado"), se marcan los extremos y también las intermedias.
- **2026-10-29:** las palabras genéricas ("crecimiento", "inicio") no marcan etapa en `detectar_etapas`.
- **2026-10-29:** las `etapa_*` de Nicovita salen del slug más la descripción del PDF. La descripción de la web solo se usa si no hay PDF, y sin la etiqueta de categoría del sitio (R4.2).
- **2026-10-29:** las `etapa_*` de HAID salen del slug más la descripción y las recomendaciones de uso del PDF, igual que Nicovita. Los rangos en gramos no se traducen a etapa (R4.3).
- **2026-10-29:** en Aquaxcel Ecuador, `INICIO` en la columna "ETAPA DE USO" cuenta como `precria`: es una columna de etapa explícita, no prosa. La regla de palabras genéricas sigue valiendo para el texto libre (R4.4).
- **2026-10-29:** en Agrizon (BioMar), si los tags nombran más de una etapa ("engorde" + "Iniciadores"), se marcan todas, ya no se desempata por tamaño de pellet. Sin término de etapa en el título o los tags, se usa la banda de tamaño de pellet (`etapa_from_tamano`), porque nada la contradice (R4.5).
- **2026-10-29:** "tamaño/peso de cosecha" y "hasta la cosecha" cuentan como engorde en `detectar_etapas`.
- **2026-10-29:** "transferencia" suelta ("en sistemas de transferencia") no marca post transferencia: nombra el traslado al final de la precría. Sí lo marcan "post transferencia" y "transición".
- **2026-10-29:** Classic Orgánico Engorde (Honduras) usa la ficha de Classic Orgánico, porque el sitio enlaza por error la de Origin Orgánico. La corrección solo se aplica mientras el sitio siga enlazando esa ficha exacta (R4.2b).
- **2026-10-29:** en Agripac se aplican las mismas reglas que en Agrizon (R4.5): se marcan todas las etapas que nombra la ficha ("larvas y post-larvas" → las dos) y, sin término, la banda de tamaño de pellet. MeM y Mpex ("postlarvas", "PL1 a PL6") pasan de larva a solo post_larva (R4.6).
- **2026-11-09 (confirmado por el usuario el mismo día):** R4.10 quita `etapa_competidor`. `etapa_skt` sale de las `etapa_*`: Hatchery si la etapa más temprana del ciclo es `larva` (o Larvicultura de Agripac); sin tamaño, la etapa más temprana con respaldo. Alternativa descartada: conservar la columna como respaldo. Efecto en Ecuador: Nicovita Origin (3 filas, `post_larva`) y MeM/Mpex (6 filas, `post_larva` desde R4.6) pasan de Hatchery a Nursery. Revisar con el usuario si Origin debe seguir Hatchery.
- **2026-11-09:** el entregable son los Excel con datos scrapeados; las filas humanas quedan en pausa. Las fórmulas cambian poco: no hace falta re-scrapear seguido. Orden: buscar más competidores (R7.4) y después Nicovita (R6). Se usa Codex como herramienta.
- **2026-11-09:** se implementan El Pedregal (R7.5), AQUATEC (R7.6, aceptando el certificado SSL inválido de nutrimentos.com.mx) y Prilabsa (R7.7). Orden: primero los scrapers nuevos, después R6. Los competidores fuera de Ecuador tienen prioridad (los principales de Ecuador ya están mapeados). Buscar listados en los ministerios de agricultura (R8.8).
- **2026-11-09:** se permite evadir bloqueos (antes prohibido): cabeceras/User-Agent, huella TLS de navegador, otro cliente, proxies o copias públicas. Siguen prohibidos Playwright/Selenium y los servicios pagos (incluidos resolvedores de captcha). Motivo: `mida.gob.pa` corta el TLS desde la red del usuario y los PDF son públicos (R8.8).
- **2026-11-09:** El Pedregal (R7.5): fuentes = imágenes del catálogo (OCR) + solo la tabla `?t=mp` (migajas post-larva). No entran `?t=ep` (reemplazada por las imágenes) ni `?t=p` / `?t=e` (título "(NO)", sin enlace en el sitio). "Preengorda" → `post_transferencia` (Pre Grower); "engorda" → `engorde`.
- **2026-11-09 (confirmado por el usuario el mismo día):** R7.7 Prilabsa. (a) Zeigler se incluye en Ecuador, porque ahí no estaba cubierto (solo en México vía Nutrimar). (b) `empresa` = fabricante (Zeigler, Mackay Marine, Higashimaru), no `Prilabsa`, como hace Nutrimar con Zeigler. (c) Ficha con dos proteínas distintas (peso seco/líquido en EZ Artemia/EZ Larva, dos dietas en ZM Feed) o con rango (Espirulina 60–70 %) → proteína vacía. (d) Tamaño `<50 µm` → `<0.05` con `particula_min_mm` vacío. Alternativas: empresa `Prilabsa`; tomar la proteína en peso seco.
- **2026-11-09:** `Microgranulado` entra a la lista oficial de `tipo_presentacion` (BioMar Exia Prime, Agrizon). No se convierte a `Granulado`.
- **2026-11-09:** R7.3: por ahora no se agrega ningún competidor nuevo; los candidatos quedan anotados en `revision_pendiente.md`.
- **2026-11-09:** el reporte de Power BI para gerencia lo hace el usuario.
- **2026-11-09:** cada corrida **reemplaza** a la anterior (snapshot); no se guarda histórico por fecha.
- **2026-11-09:** Tesseract va **dentro del `.exe`** (no como requisito de instalación aparte).
- **2026-11-09:** las proteínas que la fuente no publica (p. ej. 18/38 de Agripac Ecuador) quedan vacías y se llenan a mano.
- **2026-11-09 (confirmado por el usuario):** quedan como están los puntos abiertos de `revision_pendiente.md`: AQUATEC con "(Línea X)" y proteína del % del nombre; AQUANASA del MIDA por el cruce curado; Prilabsa PRE-MIX PL y ESPIRULINA incluidos; reproductores con tamaño caen en la banda; se mantiene "etapa más temprana = larva"; filas humanas sin cambios.
- **2026-11-09:** R7.3 se reabre para México y Panamá (Ecuador no): Skilla (R7.8), ProAqua (R7.9), NasaFeed (R8.10), Italcol (R8.11). Oromar y Avícola Grecia no tienen sitio: siguen solo por registro oficial. ProAqua: solo alimentos formulados (Biogrow Formula 1–4, XT Ultra, Epicore Epifeed/Epibal); `empresa` = fabricante. NasaFeed: copia de Wayback de la ficha; 3 filas por proteína y tamaño vacío, porque la ficha no dice qué diámetro va con cada proteína. Italcol (colombiano) entra como fuente de Panamá. Alternativas descartadas: toda la categoría de ProAqua, 6 combinaciones en NasaFeed, Italcol solo en el README.
- **2026-11-09 (confirmado por el usuario):** se cierran los puntos abiertos de `revision_pendiente.md`. AQUATEC y la regla de AQUANASA del MIDA (sin proteína tomada del nombre) quedan como estaban. Prilabsa PRE-MIX PL y ESPIRULINA quedan incluidos, y sus 10 filas sin proteína se llenan a mano. NasaFeed usa el nombre del registro MIDA (`AQUANASA 25/30/35` en vez de "Aquanasa Línea Premium NN%"), así que los 3 registros pasan de `sin_match` a `coincide`.
- **2026-11-09:** se eliminan `data.zip` (copia del 2026-10-29) y el código M de `docs/powerbi.md`, que no se había probado. Los resultados del pipeline (`data/master.*`, `data/processed/`, `registros_oficiales.*`, `conflictos.csv`, `presentaciones_nuevas.csv`) se versionan para bajarlos con `git fetch`. Siguen fuera de git `data/raw/` (caché de 194 MB) y `competencia_human.xlsx` (carga manual).
- **2026-11-09:** se agrega R11, la competencia directa de Ignis e InVita (Skretting LifeStart). Entran todos los competidores que se encuentren. En Honduras, Nicaragua y Panamá primero se descubre (sin código) y se construye solo si aparece una fuente.
- **2026-11-09:** R11.3 reabre R7.9: de ProAqua México también entran las microalgas Reed Instant Algae de `/reed-mariculture/`, como competencia de hatchery.
- **2026-11-09 (confirmado por el usuario el mismo día):** R11.3 Reed en ProAqua. Entran solo las microalgas marcadas para camarón (Instant Algae Isochrysis 1800, Tetraselmis 3600, TW 1200, TP 1800) y LPB Frozen Shellfish Diet. N-Rich, Rotigrow y RotiGreen (rotífero), Nanno, Rot-Diet y Shellfish Diet 1800 quedan fuera. El tamaño de la célula publicado va a `tamano_pellet_mm` (µm → mm; con dos dimensiones, la primera). Alternativas descartadas: incluir los N-Rich; dejar el tamaño vacío.
