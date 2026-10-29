# R4.3 — HAID marca todas sus etapas

> Roadmap: [R4.3](../../roadmap.md) · Estado: se marca solo en el roadmap

## Contexto
Hoy las `etapa_*` de HAID salen del puente R3.5 (una sola etapa, la de `etapa_competidor`, que infiere `_infer_etapa` con marcadores propios y un fallback por slug para Starter). Esta fase hace que el parser marque todas las etapas que declara la fuente con `schema.detectar_etapas`, con el mismo criterio que Nicovita (decisión del usuario del 2026-10-29).

## Requisitos
- **REQ-1:** El parser de HAID marca las `etapa_*` con `schema.columnas_etapa(schema.detectar_etapas(texto))`, donde el texto es el slug de la URL más la descripción del producto y las recomendaciones de uso del PDF. Todas las filas (tamaños) del producto llevan las mismas etapas y marcan `_etapas_detectadas`.
- **REQ-2:** Sin término de etapa en el slug ni en el PDF, las `etapa_*` quedan vacías: los rangos en gramos ("de 1 g hasta 3 g") no se traducen a etapa.

## Fuera de alcance
- `etapa_competidor` y `_infer_etapa` no cambian (se quitan en R4.10).
- `etapa_skt` no cambia.

## Restricciones de la constitución que más pesan acá
- Vacío antes que inventar: si la fuente no nombra una etapa, las `etapa_*` quedan vacías.
- Normalizar en el parser con funciones de `schema.py`.
