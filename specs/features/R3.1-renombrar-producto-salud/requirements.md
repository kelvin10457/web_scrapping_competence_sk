# R3.1 — Renombrar `producto_salud` → `es_producto_de_salud`

> Roadmap: [R3.1](../../roadmap.md) · Estado: se marca solo en el roadmap

## Contexto
`tech-stack.md` ya define la columna como `es_producto_de_salud` (nombre del Excel de Power BI), pero el código usaba `producto_salud`.

## Requisitos
- **REQ-1:** `SCHEMA_COLUMNS` contiene `es_producto_de_salud` y no `producto_salud`.
- **REQ-2:** No queda ninguna aparición de `producto_salud` (sin el prefijo nuevo) en `src/` ni `tests/` (incluido el baseline de Ecuador).
- **REQ-3:** Sin cambios de lógica: la suite existente pasa igual que antes.

## Fuera de alcance
- Migrar archivos de edición humana ya generados en `data/` con el nombre viejo.
- `docs/historico/` y `specs/decisiones.md` (registro histórico).

## Restricciones de la constitución que más pesan acá
- Normalizar en el parser, nunca al exportar: el nombre nuevo sale desde el origen.
