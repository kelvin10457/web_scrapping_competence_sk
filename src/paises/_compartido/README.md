# _compartido/

Motores para sitios que sirven varios países con la misma estructura y cambian solo el `pais_slug`.

- `nicovita.py` → `run(pais_slug)`; usa `nicovita_scraper.py` (listado `?pais=<slug>`, PDFs en `data/raw/nicovita/`, caché de PDF por corrida) y `nicovita_parser.py` (ficha PDF + HTML). El slug de producto acepta los sufijos `-ecuador/-honduras/-mexico/-peru` (y `-2`).
- `aquaxcel.py` → `run(pais_slug)`; `aquaxcel_parser.py` reconoce dos layouts: bloques "Portafolio {LÍNEA}" (Ecuador) y secciones `container-*` con tarjetas (México, sin empaque).

**No agregar aquí lógica propia de un solo país**: va en `paises/<pais>/<empresa>.py`.

## Nicovita: pausa, caché y páginas guardadas a mano

- Pausa de 2 s entre peticiones; HTML cacheado 24 h en `data/raw/nicovita_html/`; los PDF ya descargados en `data/raw/nicovita/` no se piden de nuevo.
- Si nicovita.com bloquea con captcha (`netutil.BlockedError`), el scraper usa la copia guardada de cada página, aunque sea vieja. **No se evade el captcha.**
- **Para probar con páginas guardadas desde tu navegador** (si hay captcha): abre cada página de producto de Nicovita, Ctrl+S → "Página web, solo HTML", y guárdala en `data/manual/nicovita/<pais>/` (por ejemplo `data/manual/nicovita/honduras/`) con **cualquier nombre**. El scraper las reconoce por su URL real (canonical), así que no hace falta el listado ni renombrar. Solo se usan cuando el sitio bloquea. Los PDF ya están en `data/raw/nicovita/`.
