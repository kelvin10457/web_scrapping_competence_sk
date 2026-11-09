# R2.2 — Vimifos: una celda con varias proteínas

> Roadmap: [R2.2](../../roadmap.md) · Estado: se marca solo en el roadmap
> Migrada al formato SDD desde `docs/historico/RONDA2_REGIONAL.md` como ejemplo.

## Contexto
En vimifos.com algunas líneas (Bumper Crop, Natural Force, Total Range) publican varias proteínas en una sola celda (`30%, 35%, 40%`). El parser dejaba `proteina_pct = null`: 3 de 15 filas de Vimifos México quedaban sin proteína.

## Requisitos
- **REQ-1:** Las proteínas de la celda se extraen con `(\d+(?:[.,]\d+)?)\s*%`, en el orden en que aparecen.
- **REQ-2:** Si la fila trae `M` calibres y `N` proteínas con `M == N`, se generan `N` filas emparejadas 1 a 1 en el orden publicado.
- **REQ-3:** Si `M` es 0 o 1, se generan `N` filas, cada una con una proteína y el mismo calibre.
- **REQ-4:** Si `M ≠ N` y los dos son mayores que 1, se generan `N` filas con `tamano_pellet_mm` igual al texto original completo, y el caso se registra en `_conflictos.csv` con la regla `calibre_no_emparejable`.
- **REQ-5:** Si la página asocia de forma explícita cada proteína a un calibre (por ejemplo, `"35% (2.0 mm)"`), esa asociación manda sobre el orden.

## Fuera de alcance
- Otras empresas con celdas parecidas: se resuelven con `schema.resolver_campo` en su propio ítem.

## Restricciones de la constitución que más pesan acá
- No inventar el emparejamiento: si no se puede emparejar, el texto queda tal cual y el caso se registra (REQ-4).
