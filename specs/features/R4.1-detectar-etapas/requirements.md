# R4.1 — `schema.detectar_etapas` y columna `etapa_post_larva`

> Roadmap: [R4.1](../../roadmap.md) · Estado: se marca solo en el roadmap

## Contexto
Hoy los parsers dejan una sola etapa (`normalize_etapa`: gana la primera regla) y vacío cuando la fuente declara varias (Térap: "post larva hasta tamaño de mercado"). Esta fase agrega la función compartida que detecta **todas** las etapas de un texto, para que R4.2–R4.9 la usen en cada parser. Además se suma la columna `etapa_post_larva`: la post larva es una fase intermedia entre larva y precría (decisiones del 2026-10-29).

## Requisitos
- **REQ-1:** `SCHEMA_COLUMNS` y `ETAPA_COLUMNS` incluyen `etapa_post_larva` entre `etapa_larva` y `etapa_precria`. El puente R3.5 (`etapas_desde_competidor`) la deja en `False` cuando hay `etapa_competidor` y vacía cuando no hay. `etapa_competidor` no cambia.
- **REQ-2:** `schema.detectar_etapas(texto) -> set` devuelve todas las etapas explícitas del texto, con valores de `ETAPAS` (`reproductores`, `larva`, `post_larva`, `precria`, `post_transferencia`, `engorde`). Con un texto vacío o `None`, devuelve `set()`.
- **REQ-3:** "post larva", "post-larva", "postlarva", "postlarval" y "PL" → `post_larva`, **no** `larva`. `larva` queda para larva, larvicultura, hatchery, mysis, zoea y nauplio.
- **REQ-4:** Las palabras genéricas no marcan etapa: "crecimiento" ("promueve el crecimiento") e "inicio".
- **REQ-5:** Un rango entre dos etapas ("X hasta Y", "X hacia Y", "X a Y") marca los extremos **y las intermedias** del ciclo larva → post_larva → precria → post_transferencia → engorde. "tamaño de mercado", "talla comercial" y "a mercado" cuentan como engorde. `reproductores` queda fuera del ciclo y nunca se rellena.
- **REQ-6:** `schema.columnas_etapa(etapas)` convierte el set en las 6 columnas: las detectadas en `True` y las demás en `False`. Con un set vacío, las 6 quedan vacías.
- **REQ-7:** El respaldo de `etapa_skt` sin tamaño mapea `post_larva` → `Nursery`.

## Fuera de alcance
- Usar `detectar_etapas` en los parsers (R4.2–R4.9).
- `normalize_etapa`, `etapa_matches` y `etapa_competidor` no cambian; se quitan o se reemplazan en R4.5 y R4.10.
- La GUI y `manual_store` (congelados).

## Restricciones de la constitución que más pesan acá
- Vacío antes que inventar: sin término de etapa explícito no se marca nada, y una palabra genérica no cuenta como etapa.
- Cambia el esquema: `tech-stack.md` y `decisiones.md` se actualizan en el mismo commit.
