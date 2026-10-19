# Arquitectura del proyecto

Scraping de competencia de alimento para camarón, **separado por país**. Estado y decisiones: `PROGRESO_REGIONAL.md`, `PLAN_REGIONAL.md`, `MEMORY.md`.

## Mapa del código (`src/`)

| Archivo / carpeta | Qué hace |
|---|---|
| `pipeline.py` | Orquestador y CLI. Corre cada (país, empresa) de forma aislada, escribe los CSV/XLSX y arma los masters. |
| `fuentes.py` | Registro de fuentes. **Se deriva de las carpetas** `paises/<pais>/` (no hay lista aparte que mantener). |
| `schema.py` | Columnas del esquema (`pais` primera), `PAIS_VALUES`, normalización de etapas/tipos. |
| `netutil.py` | `get()` con reintentos y detección de bloqueo anti-bot (`BlockedError`, no se evade). |
| `merge_human.py`, `manual_store.py` | Fusión de datos cargados a mano (Excel / SQLite) con el master. `pais` forma parte de la identidad. |
| `gui.py` | Interfaz para el equipo comercial: una tarjeta por (país, empresa) y formulario manual. |
| `paises/<pais>/` | **Todo lo específico de un país.** Ver abajo. |
| `paises/_compartido/` | Motores usados por más de un país (Nicovita, Aquaxcel). |

## Una fuente = un módulo con `run()`

```
paises/mexico/__init__.py          FUENTES = ["nicovita", "aquaxcel", "vimifos", ...]
paises/mexico/vimifos.py           def run() -> list[dict]          # une scraper + parser
paises/mexico/vimifos_scraper.py   descarga (requests)  -> [{url, html, ...}]
paises/mexico/vimifos_parser.py    parsea               -> list[dict] con las columnas del esquema
```

- Los **parsers no escriben `pais`**; lo agrega `fuentes.run_fuente`.
- Una empresa presente en varios países (Nicovita, Aquaxcel) tiene **un módulo por país** (`paises/honduras/nicovita.py`, …) que llama al motor de `_compartido/` con sus parámetros. Si un país diverge (otros productos, otro layout), se cambia solo ese módulo.
- Un país sin fuente pública (`nicaragua`, `panama`) tiene `FUENTES = []` y se carga a mano por la GUI.

## Salidas (`data/`)

```
data/raw/<empresa>/*.pdf                        PDFs descargados (compartidos entre países: el nombre de archivo es la clave)
data/processed/<pais>/<empresa>.csv|xlsx        una empresa en un país
data/processed/<pais>/master_<pais>.csv|xlsx    todo un país
data/master.csv|xlsx                            todos los países (columna `pais`)
```

## Comandos

```
python src/pipeline.py                          # todo
python src/pipeline.py --pais honduras          # un país
python src/pipeline.py --pais mexico --empresa vimifos
python src/pipeline.py --empresa nicovita       # una empresa en todos sus países
.venv/Scripts/python -m pytest -q               # tests (usan fixtures en tests/fixtures/, sin red)
```

## Agregar una fuente nueva

1. Crear `paises/<pais>/<empresa>_scraper.py` y `<empresa>_parser.py` (copiar un par existente, p. ej. `mexico/vimifos_*`).
2. Crear `paises/<pais>/<empresa>.py` con `run()`.
3. Agregar la empresa a `FUENTES` en `paises/<pais>/__init__.py`.
4. Guardar un fixture en `tests/fixtures/` y escribir `tests/test_<empresa>_parser.py`.
5. Agregar los módulos a `hiddenimports` de `ScraperCompetencia.spec` (se cargan con `importlib`).
6. Documentarla en `paises/<pais>/README.md`.

## Reglas que no se rompen

No inventar ni inferir valores (`null` si la fuente no lo publica) · sin LLM ni APIs de pago · `requests` + `BeautifulSoup`, sin Playwright (rompe el `.exe`) · pausa entre requests y respeto a `robots.txt` · si un sitio bloquea, **no se evade**: se documenta y pasa a carga manual.
