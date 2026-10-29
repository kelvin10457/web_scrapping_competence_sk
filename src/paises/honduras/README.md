# Honduras

Fuente: **Nicovita** (`nicovita.py`, motor `_compartido`), nicovita.com `?pais=honduras`, 8 páginas únicas / 35 filas. Las fichas PDF se comparten con Ecuador.

- `nicovita-classic-honduras` se deduplica como alias de otra página con el mismo PDF.
- `nicovita-classic-organic-engorde-honduras` enlaza por error la ficha de Origin Orgánico: el scraper usa la de Classic Orgánico (`_PDF_CORREGIDO`, R4.2b) y la página queda como alias de `nicovita-classic-organic-honduras`.
- Aquaxcel/Cargill y BioMar: sin catálogo ni distribuidor público (`/productos/honduras/` = 404) → carga manual.
- Nicovita atiende **Nicaragua y Panamá desde Honduras**: no se copian filas a esos países (decisión del usuario 2026-10-20, ver `specs/decisiones.md`).
