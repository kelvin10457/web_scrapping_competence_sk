# Tech stack

> El mapa del código, los comandos y el procedimiento ante captchas están en `README.md`. Las fuentes de cada país, en `src/paises/<pais>/README.md`.

## Stack

- **Python** con `requests` (siempre a través de `netutil.get()`), `BeautifulSoup` + `lxml`, `pdfplumber` / `PyMuPDF`, `pytesseract` (Tesseract instalado aparte, en español), `pandas` y `openpyxl`.
- **App de escritorio:** Tkinter (`gui.py`) empaquetada con PyInstaller (`ScraperCompetencia.spec`). **Congelada** desde el 2026-10-29 (ver `decisiones.md`): no se adapta al esquema nuevo.
- **Tests:** `pytest`, con fixtures **reales** (descargados, no armados a mano) en `tests/fixtures/`. Corren sin red.
- **Prohibido:** Playwright o Selenium (rompen el `.exe`), LLM o APIs pagas, proxies o suplantar el navegador.

## Patrones

- **Una fuente = un módulo `paises/<pais>/<empresa>.py` con `run()`**, que une un `_scraper` (descarga) y un `_parser` (devuelve `list[dict]`). Los parsers no escriben `pais`.
- Una empresa presente en varios países usa un motor en `paises/_compartido/` con `pais_slug`.
- **Cada (país, empresa) corre aislado:** si falla uno, el resto sigue. Si una corrida trae 0 filas, nunca sobrescribe el archivo anterior.
- **El vocabulario se normaliza en el parser**, con funciones de `schema.py` (`normalize_presentacion`, etapas). Lo que no está en el vocabulario se conserva y se reporta en `data/presentaciones_nuevas.csv` y en el resumen final del CLI.
- **Conflictos:** cuando hay varios valores para un mismo campo, `schema.resolver_campo` elige uno con reglas fijas y deja el caso en `_conflictos.csv`.
- **Ritmo:** pausas aleatorias solo para los dominios en `netutil.PACED_HOSTS`, más caché de HTML y PDF, dentro de un presupuesto de tiempo por corrida.

## Esquema

Una fila por **SKU** (un tamaño de pellet concreto) cuando la fuente lo publica. Si no, una fila por producto. Los nombres de columna son **los mismos** en el CSV interno y en el Excel de Power BI.

### Excel para Power BI: `data/powerbi/<pais>/<empresa>.xlsx`

| Columna | Tipo | Valores |
|---|---|---|
| `pais` | texto | `ecuador`, `mexico`, `honduras`, `nicaragua`, `panama` |
| `empresa` | texto | Marca del fabricante (p. ej. `Cargill` para Aquaxcel) |
| `nombre_producto` | texto | Incluye marca y submarca |
| `es_producto_de_salud` | booleano | Función terapéutica (p. ej. anti-Vibrio), independiente de la etapa |
| `etapa_reproductores` | booleano | Un producto puede tener varias etapas en `true`. Vacío si la fuente no dice nada. **Hoy (puente R3.5)** se derivan de `etapa_competidor`: esa etapa en `true` y las otras 4 en `false`; sin etapa, las 5 vacías. Son derivadas: el Excel manual puede no traerlas |
| `etapa_larva` | booleano | |
| `etapa_precria` | booleano | |
| `etapa_post_transferencia` | booleano | |
| `etapa_engorde` | booleano | |
| `etapa_skt` | texto | `Hatchery`, `Nursery`, `Pre Grower`, `Grower` (ver regla abajo) |
| `tamano_pellet_mm` | texto | Tal cual lo publica la fuente; puede ser un rango (`1.2-1.5`) |
| `particula_min_mm` | número decimal | Extremo inferior del rango; si es un solo valor, ese mismo |
| `particula_max_mm` | número decimal | Extremo superior |
| `tipo_presentacion` | texto | `Extruido`, `Granulado`, `Líquido`, `Microencapsulado`, `Microextruido`, `Microparticulado`, `Nauplios de artemia`, `Otro`, `Pellet`, `Polvo`, `Quistes de artemia`, `Suspensión`. Un valor fuera de esta lista **no es un error**: se conserva y se avisa |
| `proteina_pct` | número decimal | Porcentaje tal cual: `35`, `37.5` (no `0.375`) |

Incluye las filas cargadas a mano (`competencia_human.xlsx`) para ese país y empresa.

### Columnas solo internas (CSV en `data/processed/<pais>/<empresa>.csv`)

`empaque_kg`, `fuente_url` y `fecha_extraccion`, además de `_conflictos.csv` y `master.csv` (unión de todo, usada por la GUI y por `merge_human`).

### Regla de `etapa_skt`: una columna, criterio propio de Skretting

Se calcula a partir del **tamaño del pellet** y no de cómo llama a la etapa el competidor:

- Etapa del competidor `larva`, o división Larvicultura de Agripac → `Hatchery`, **aunque tenga tamaño** (Nicovita Origin, 0.3-0.8 mm)
- menos de 1.6 mm → `Nursery`
- 1.6 mm → `Pre Grower`
- más de 1.6 mm → `Grower` (sin distinguir entre pellet y extruido; p. ej. 1.7 mm → `Grower`)
- **Rango** (`1.4-2.0`): manda el tamaño mínimo.
- **Sin tamaño:** se usa la etapa del competidor como respaldo: `precria` → `Nursery`, `post_transferencia` → `Pre Grower`, `engorde` → `Grower`. `reproductores` o sin etapa → vacío.
