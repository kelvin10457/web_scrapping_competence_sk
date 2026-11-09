# R3.5 — Columnas `etapa_*` booleanas (paso puente)

> Roadmap: [R3.5](../../roadmap.md) · Estado: se marca solo en el roadmap

## Contexto
`tech-stack.md` define 5 booleanos de etapa para Power BI, pero hoy el CSV solo tiene `etapa_competidor` (una etapa por fila). Este paso agrega las 5 columnas derivadas de `etapa_competidor`. En R4 cada parser va a marcar todas las etapas que declara la fuente.

## Requisitos
- **REQ-1:** `schema.etapas_desde_competidor(etapa)` devuelve un dict con las 5 columnas `etapa_reproductores`, `etapa_larva`, `etapa_precria`, `etapa_post_transferencia` y `etapa_engorde`. Si `etapa` es uno de `ETAPA_VALUES`, esa columna queda en `True` y las otras 4 en `False`. Si es vacío o desconocido, las 5 quedan vacías (`None`). (Decisión del usuario, 2026-10-29.)
- **REQ-2:** `SCHEMA_COLUMNS` incluye las 5 columnas después de `es_producto_de_salud`. `pipeline.write_csv` las completa en cada fila y en el CSV quedan como `True`/`False`/vacío. `etapa_competidor` se mantiene, porque R3.6 la usa como respaldo.
- **REQ-3:** En `competencia_human.xlsx` las 5 columnas son derivadas: el Excel puede no traerlas (el archivo actual sigue siendo válido) y, si las trae, se ignoran. Se recalculan desde `etapa_competidor` al fusionar.

## Fuera de alcance
- La GUI y `manual_store` (congelados, decisión 2026-10-29).
- Marcar varias etapas por fila (R4).

## Restricciones de la constitución que más pesan acá
- Si `etapa_competidor` está vacío, las 5 quedan vacías: no se infiere ninguna.
