# R4.5 — Agrizon (BioMar) marca todas sus etapas

> Roadmap: [R4.5](../../roadmap.md) · Estado: se marca solo en el roadmap

## Contexto
Hoy las `etapa_*` de BioMar (Ecuador, vía el distribuidor Agrizon) salen del puente R3.5: una sola etapa, la de `etapa_competidor`. Esa etapa sale de los tags. Si los tags nombran más de una etapa, o ninguna, se usa el tamaño de pellet (`etapa_from_tamano`). `body_html` viene vacío en los 17 productos y además no se usa (decisión 2026-09-03), así que las únicas fuentes son el título y los tags.

## Requisitos
- **REQ-1:** las `etapa_*` salen de `detectar_etapas` sobre el título más los tags. Se marcan todas las etapas que nombran (decisión del usuario del 2026-10-29): Exia Prime 1.2 mm y 1.6 mm (tags "engorde" + "Iniciadores") → precria + engorde. Larviva ("larvas", "Post-larva") → larva + post_larva. Todas las filas marcan `_etapas_detectadas`.
- **REQ-2:** sin término de etapa en el título o los tags, se usa la banda de tamaño de pellet (`etapa_from_tamano`), porque nada la contradice (decisión del usuario del 2026-10-29). Exia Pro 35% Pelletized 2.0 mm → engorde. Si la banda tampoco resuelve (por ejemplo 1.6 mm), las `etapa_*` quedan vacías.
- **REQ-3:** el slug no se usa. "exia-start-38-0-9-1-2-mm-10-kg-dieta-para-larvas" dice larvas, pero sus tags dicen Precrías: queda solo precria.

## Fuera de alcance
- `etapa_competidor` no cambia (se quita en R4.10). `etapa_skt` no cambia.
- `biomar_parser.py` (biomar.com) sigue sin usarse.

## Restricciones de la constitución que más pesan acá
- Vacío antes que inventar o inferir.
- Normalizar en el parser con funciones de `schema.py`.
