# Tech stack

> El mapa del código, los comandos y el procedimiento ante captchas están en `README.md`. Las fuentes de cada país, en `src/paises/<pais>/README.md`.

## Stack

- **Python** con `requests` (siempre a través de `netutil.get()`), `BeautifulSoup` + `lxml`, `pdfplumber` / `PyMuPDF`, `pytesseract` (Tesseract con español; en el `.exe` va empaquetado, ver `src/ocr.py`), `pandas` y `openpyxl`.
- **App de escritorio:** Tkinter (`gui.py`) empaquetada con PyInstaller (`ScraperCompetencia.spec`). **Congelada** desde el 2026-10-29 (ver `decisiones.md`): no se adapta al esquema nuevo.
- **Tests:** `pytest`, con fixtures **reales** (descargados, no armados a mano) en `tests/fixtures/`. Corren sin red.
- **Prohibido:** Playwright o Selenium (rompen el `.exe`), LLM o APIs pagas. Evadir un bloqueo (User-Agent de navegador, huella TLS, otro cliente, proxy, copias públicas) **sí** se permite desde 2026-11-09 (`decisiones.md`, README § Bloqueos).
- **Registros oficiales** (`registros_oficiales.py`, complementarios, nunca crean filas): SENASICA y eaduana (México), MIDA Panamá (R8.9: PDF nacional con tabla y PGA sin bordes, filtrado a camarón explícito o curado y vigente).

## Patrones

- **Una fuente = un módulo `paises/<pais>/<empresa>.py` con `run()`**, que une un `_scraper` (descarga) y un `_parser` (devuelve `list[dict]`). Los parsers no escriben `pais`.
- Una empresa presente en varios países usa un motor en `paises/_compartido/` con `pais_slug`.
- **Cada (país, empresa) corre aislado:** si falla uno, el resto sigue. Si una corrida trae 0 filas, nunca sobrescribe el archivo anterior.
- **El vocabulario se normaliza en el parser**, con funciones de `schema.py` (`normalize_presentacion`, etapas). Lo que no está en el vocabulario se conserva y se reporta en `data/presentaciones_nuevas.csv` y en el resumen final del CLI.
- **Conflictos:** cuando hay varios valores para un mismo campo, `schema.resolver_campo` elige uno con reglas fijas y deja el caso en `_conflictos.csv`.
- **Ritmo:** pausas aleatorias solo para los dominios en `netutil.PACED_HOSTS` (0.5–2.5 s, y 5–12 s cada 6–10 consultas nuevas; la caché no cuenta), más caché de HTML y PDF. Presupuesto: ≤3 min por país en frío (Nicovita Honduras: 61 s). Después de un captcha, solo ese dominio pasa a 6–15 s; después de 2, no se consulta más en la corrida (R6.2).

## Esquema

Una fila por **SKU** (un tamaño de pellet concreto) cuando la fuente lo publica. Si no, una fila por producto. Los nombres de columna son **los mismos** en el CSV interno y en el Excel de Power BI.

### Excel para Power BI: `data/powerbi/<pais>/<empresa>.xlsx`

| Columna | Tipo | Valores |
|---|---|---|
| `pais` | texto | `ecuador`, `mexico`, `honduras`, `nicaragua`, `panama` |
| `empresa` | texto | Marca del fabricante (p. ej. `Cargill` para Aquaxcel) |
| `nombre_producto` | texto | Incluye marca y submarca |
| `es_producto_de_salud` | booleano | Función terapéutica (p. ej. anti-Vibrio), independiente de la etapa |
| `etapa_reproductores` | booleano | Un producto puede tener varias etapas en `true`. Vacío si la fuente no dice nada. Cada parser las marca con `schema.detectar_etapas` (ver regla abajo). Desde R4.10 no hay columna `etapa_competidor`: el Excel manual las puede traer como booleanos o dejarlas vacías |
| `etapa_larva` | booleano | Hatchery, mysis, zoea, nauplio |
| `etapa_post_larva` | booleano | Post larva / PL: fase intermedia entre larva y precría |
| `etapa_precria` | booleano | |
| `etapa_post_transferencia` | booleano | |
| `etapa_engorde` | booleano | |
| `etapa_skt` | texto | `Hatchery`, `Nursery`, `Pre Grower`, `Grower` (ver regla abajo) |
| `tamano_pellet_mm` | texto | Tal cual lo publica la fuente; puede ser un rango (`1.2-1.5`) |
| `particula_min_mm` | número decimal | Extremo inferior del rango; si es un solo valor, ese mismo. Si el tamaño es `<X` (solo máximo publicado, Prilabsa), vacío |
| `particula_max_mm` | número decimal | Extremo superior |
| `tipo_presentacion` | texto | `Extruido`, `Granulado`, `Líquido`, `Microencapsulado`, `Microextruido`, `Microgranulado`, `Microparticulado`, `Nauplios de artemia`, `Otro`, `Pellet`, `Polvo`, `Quistes de artemia`, `Suspensión`. Un valor fuera de esta lista **no es un error**: se conserva y se avisa |
| `proteina_pct` | número decimal | Porcentaje tal cual: `35`, `37.5` (no `0.375`). Los parsers lo asignan con `schema.normalize_proteina` (acepta coma decimal; ambiguo o fuera de (1, 100] → vacío) |

Incluye las filas cargadas a mano (`competencia_human.xlsx`) para ese país y empresa.

### Columnas solo internas (CSV en `data/processed/<pais>/<empresa>.csv`)

`empaque_kg`, `fuente_url` y `fecha_extraccion`, además de `_conflictos.csv` y `master.csv` (unión de todo, usada por la GUI y por `merge_human`).

### Regla de las `etapa_*`: `schema.detectar_etapas`

- Solo cuentan los términos de etapa explícitos. Las palabras genéricas ("crecimiento", "inicio") no marcan nada.
- "post larva", "postlarval", "PL" y "PL" + número ("PL10", "PL 4") → `post_larva`, no `larva`.
- "nauplio" no marca `larva` si el mismo texto marca `reproductores`: en una dieta de maduración los nauplios son lo que producen los reproductores, no a quién se alimenta (Revisión Opus: Zeigler Ez-mate y Redi-mate, "producción de nauplios"). Otro término de larva ("larvicultura", "zoea") sí sigue contando.
- "post transferencia", "transición" y "alevinaje" → `post_transferencia`. "transferencia" suelta ("en sistemas de transferencia") no cuenta: es el traslado al final de la precría.
- Un rango entre dos etapas ("X hasta Y", "X hacia Y", "X a Y") marca los extremos y las intermedias del ciclo larva → post_larva → precria → post_transferencia → engorde. "tamaño de mercado", "a mercado", "tamaño/peso de cosecha" y "hasta (la) cosecha" cuentan como engorde. `reproductores` nunca se rellena.
- `schema.columnas_etapa(set)`: las detectadas en `true` y las demás en `false`; con un set vacío, todas quedan vacías.
- `etapa_skt` (R4.10) sale de las `etapa_*`: Hatchery si la etapa más temprana del ciclo es `larva` (o es Larvicultura de Agripac); con tamaño, la banda; sin tamaño, la etapa más temprana con respaldo (`_ETAPA_SKT_RESPALDO`).
- Todos los parsers marcan `_etapas_detectadas` y `pipeline.write_csv` respeta sus `etapa_*` aunque queden vacías. El puente R3.5 (derivar desde `etapa_competidor`) se quitó en R4.10; BioMar (módulo deshabilitado) también marca sus etapas con `detectar_etapas`. Nicovita usa el slug más la descripción del PDF (la web solo si no hay PDF, sin la etiqueta de categoría). HAID usa el slug más la descripción y las recomendaciones de uso del PDF. Aquaxcel Ecuador usa la columna "ETAPA DE USO" de cada SKU (ahí `INICIO` = `precria`); Aquaxcel México, la línea de la tarjeta más su descripción. Agrizon (BioMar) usa el título más los tags, sin el slug; si no nombran etapa, la banda de tamaño de pellet (`etapa_from_tamano`). Agripac usa el título, la descripción, el modo de uso y los ingredientes; si no nombran etapa (todos los Feedpac), la banda de tamaño de pellet. El Pedregal (México) usa el encabezado de sección de la imagen más la línea "Uso:" (OCR) y el `<h1>` en la tabla de migajas; "engorda" → engorde y "preengorda" → post_transferencia. AQUATEC (México) usa solo las INDICACIONES de su ficha ("juveniles hasta 5 g" no nombra etapa: quedan vacías); sus variantes sin ficha no heredan nada. Prilabsa (Ecuador) usa el texto completo de cada ficha del catálogo para todas sus filas (una por tamaño), sin el encabezado de tabla "TAMAÑO DE PARTÍCULAS Y ESTADIO LARVAL"; `empresa` = fabricante (Zeigler, Mackay Marine, Higashimaru), como Nutrimar con Zeigler. Su scraper usa `verify=False` acotado a `nutrimentos.com.mx` (certificado inválido, decisión del usuario). Megasupply (Megalikuid) y la Biomasa de Artemia de Prilabsa (R11.2, Agrizon en español) usan el título, los tags y, en Megalikuid, también la descripción.
- El Pedregal (R7.5): el catálogo está en imágenes y se lee con OCR local (`pytesseract`, mismo setup que HAID); una fila por tamaño publicado. Los fixtures guardan la salida OCR (`*.ocr.txt`), no las imágenes.

### Regla de `etapa_skt`: una columna, criterio propio de Skretting

Se calcula a partir del **tamaño del pellet** y no de cómo llama a la etapa el competidor:

- Etapa más temprana del ciclo `larva` (R4.10: antes, la etapa del competidor), o división Larvicultura de Agripac → `Hatchery`, **aunque tenga tamaño**. Nicovita Origin (0.3-0.8 mm) hoy marca `post_larva` y sale `Nursery`: pendiente de confirmar
- menos de 1.6 mm → `Nursery`
- 1.6 mm → `Pre Grower`
- más de 1.6 mm → `Grower` (sin distinguir entre pellet y extruido; p. ej. 1.7 mm → `Grower`)
- **Rango** (`1.4-2.0`): manda el tamaño mínimo.
- **Sin tamaño:** se usa la etapa del competidor como respaldo: `post_larva` y `precria` → `Nursery`, `post_transferencia` → `Pre Grower`, `engorde` → `Grower`. `reproductores` o sin etapa → vacío.
