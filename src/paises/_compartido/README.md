# _compartido/

Motores para sitios que sirven varios países con la misma estructura y cambian solo el `pais_slug`.

- `nicovita.py` → `run(pais_slug)`; usa `nicovita_scraper.py` (listado `?pais=<slug>`, PDFs en `data/raw/nicovita/`, caché de PDF por corrida) y `nicovita_parser.py` (ficha PDF + HTML). El slug de producto acepta los sufijos `-ecuador/-honduras/-mexico/-peru` (y `-2`).
- `aquaxcel.py` → `run(pais_slug)`; `aquaxcel_parser.py` reconoce dos layouts: bloques "Portafolio {LÍNEA}" (Ecuador) y secciones `container-*` con tarjetas (México, sin empaque).

**No agregar aquí lógica propia de un solo país**: va en `paises/<pais>/<empresa>.py`.

## Nicovita: pausa, caché y páginas guardadas a mano

- Pausa de 2 s entre peticiones; HTML cacheado 24 h en `data/raw/nicovita_html/`; los PDF ya descargados en `data/raw/nicovita/` no se piden de nuevo.
- Si nicovita.com bloquea con captcha (`netutil.BlockedError`), el scraper usa la copia guardada de cada página, aunque sea vieja. **No se evade el captcha.**
- Para alimentar el scraper a mano: abrir la página en el navegador, "Guardar como… HTML" en `data/raw/nicovita_html/` con el nombre que da `nicovita_scraper.cache_path(url)` (la URL en minúsculas, con todo lo que no sea letra/número convertido en `_`, p. ej. `https_nicovita_com_categoria_camarones_pais_honduras.html`). Se necesita el listado `https://nicovita.com/categoria/camarones/?pais=<pais>` y cada página de producto; los PDF van en `data/raw/nicovita/`.
