# R4.4 — Aquaxcel marca todas sus etapas

> Roadmap: [R4.4](../../roadmap.md) · Estado: se marca solo en el roadmap

## Contexto
Hoy las `etapa_*` de Aquaxcel (Ecuador y México, parser compartido) salen del puente R3.5: una sola etapa, la de `etapa_competidor`. En México eso deja vacía a Transition, porque `normalize_etapa` no reconoce "transition", aunque la descripción de la línea dice "etapa de transición hacia la fase de engorde". Esta fase hace que el parser marque todas las etapas que declara la fuente con `schema.detectar_etapas`, igual que Nicovita y HAID.

## Requisitos
- **REQ-1 (Ecuador, bloques "Portafolio"):** las `etapa_*` salen de la columna "ETAPA DE USO" de cada SKU. Las descripciones de marketing de la línea no nombran etapas, así que no se usan. `INICIO` en esa columna cuenta como `precria` (decisión del usuario del 2026-10-29): es una columna de etapa explícita, no prosa. `ENGORDE` → `engorde`. Todas las filas marcan `_etapas_detectadas`.
- **REQ-2 (México, tarjetas):** las `etapa_*` salen de `detectar_etapas` sobre la línea de la tarjeta (`nursery`, `pre-starter`, ...) más la descripción de marketing de esa línea. Ejemplos: Transition → post_transferencia + engorde, Advance/Active ("hasta peso de cosecha") → engorde.
- **REQ-3:** sin término de etapa, las `etapa_*` quedan vacías. Es el caso de Adapt Shock en México: la línea "adapt" y su descripción de salud no nombran ninguna etapa.

## Fuera de alcance
- `etapa_competidor` no cambia (se quita en R4.10). `etapa_skt` no cambia.
- La tabla "Recomendación de plan de alimentación" (gramos por producto) no se usa: los gramos no se traducen a etapa.

## Restricciones de la constitución que más pesan acá
- Vacío antes que inventar.
- Normalizar en el parser con funciones de `schema.py`.
