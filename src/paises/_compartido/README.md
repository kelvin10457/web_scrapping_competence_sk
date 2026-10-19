# _compartido/

Motores para sitios que sirven varios países con la misma estructura y cambian solo el `pais_slug`.

- `nicovita.py` → `run(pais_slug)`; usa `nicovita_scraper.py` (listado `?pais=<slug>`, PDFs en `data/raw/nicovita/`, caché de PDF por corrida) y `nicovita_parser.py` (ficha PDF + HTML). El slug de producto acepta los sufijos `-ecuador/-honduras/-mexico/-peru` (y `-2`).
- `aquaxcel.py` → `run(pais_slug)`; `aquaxcel_parser.py` reconoce dos layouts: bloques "Portafolio {LÍNEA}" (Ecuador) y secciones `container-*` con tarjetas (México, sin empaque).

**No agregar aquí lógica propia de un solo país**: va en `paises/<pais>/<empresa>.py`.
