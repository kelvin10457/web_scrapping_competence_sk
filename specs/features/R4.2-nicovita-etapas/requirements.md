# R4.2 — Nicovita marca todas sus etapas

> Roadmap: [R4.2](../../roadmap.md) · Estado: se marca solo en el roadmap

## Contexto
Hoy las `etapa_*` de Nicovita salen del puente R3.5 (una sola etapa, la de `etapa_competidor`), y cuando la ficha declara un rango ("desde post larva hasta tamaño de mercado": Classic, Katal, Térap), esa etapa sale del tamaño del pellet, no de la fuente. Esta fase hace que el parser marque todas las etapas que declara la fuente, con `schema.detectar_etapas` (decisiones del usuario del 2026-10-29).

## Requisitos
- **REQ-1:** El parser de Nicovita marca las `etapa_*` con `schema.columnas_etapa(schema.detectar_etapas(texto))`, donde el texto es el slug de la URL más la descripción del PDF. La descripción de la web solo se usa si no hay descripción del PDF (Katal Precría), y sin la etiqueta de categoría del sitio ("Iniciadores", "Pre engorde", "Engorde", "Salud"). Todas las filas (SKU) del producto llevan las mismas etapas.
- **REQ-2:** `pipeline.write_csv` respeta las `etapa_*` de un parser que ya las marcó (`_etapas_detectadas`), aunque queden vacías. El puente R3.5 (`etapas_desde_competidor`) sigue solo para los parsers que todavía no migraron.
- **REQ-3:** En `detectar_etapas`, "tamaño/peso/talla de cosecha" y "hasta (la) cosecha" cuentan como engorde.
- **REQ-4:** En `detectar_etapas`, "transferencia" suelta ("en sistemas de transferencia") no marca `post_transferencia`; sí lo marcan "post transferencia", "post-transfer", "transición" y "alevinaje".
- **REQ-5:** En `detectar_etapas`, "PL" seguido de un número ("PL10", "PL 4", "PL20") marca `post_larva`.

## Fuera de alcance
- `etapa_competidor` y `etapa_skt` no cambian (`etapa_competidor` se quita en R4.10).
- La página Classic Orgánico Engorde (Honduras) enlaza por error el PDF de Origin Orgánico: es un error del sitio y no se corrige acá.
- Los parsers de las otras empresas (R4.3–R4.9).

## Restricciones de la constitución que más pesan acá
- Vacío antes que inventar: si la fuente no nombra una etapa, las `etapa_*` quedan vacías; no se completan desde el tamaño del pellet.
- Normalizar en el parser con funciones de `schema.py`.
