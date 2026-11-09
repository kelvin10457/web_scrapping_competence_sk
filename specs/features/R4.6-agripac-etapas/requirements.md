# R4.6 — Agripac marca todas sus etapas

> Roadmap: [R4.6](../../roadmap.md) · Estado: se marca solo en el roadmap

## Contexto
Hoy las `etapa_*` de Agripac salen del puente R3.5: una sola etapa, la de `etapa_competidor`. Esa etapa sale de `normalize_etapa` sobre el título y, si no hay término, sobre la descripción, el modo de uso y los ingredientes. Si tampoco hay término, se usa la banda de tamaño de pellet. Los 20 Feedpac (alimento balanceado) no nombran etapa en ningún texto ("camarones adultos y juveniles" no es un término). Los 18 de Larvicultura sí la nombran en la descripción, a veces más de una ("larvas y post-larvas").

## Requisitos
- **REQ-1:** las `etapa_*` salen de `detectar_etapas` sobre el título, la descripción, el modo de uso y los ingredientes. Se marcan todas las etapas que nombran, como en R4.5. Larfeed ("larvas y post-larvas") → larva + post_larva. Vitellus Small ("zoea 3 – mysis 3", "larvas y post larvas") → larva + post_larva. Mpex 100-200 ("postlarvas", "PL1 a PL6") → post_larva. New Royal Oyster → reproductores. Todas las filas marcan `_etapas_detectadas`.
- **REQ-2:** sin término de etapa, se usa la banda de tamaño de pellet (`etapa_from_tamano`), como en R4.5. Feedpac 35% Ultra Micropellet 1.2mm → precria. Feedpac 35% Ultra Gregarinas 1,8 Mm → engorde. Si la banda no resuelve (Feedpac 35% Premium no tiene tamaño), las `etapa_*` quedan vacías.
- **REQ-3:** Royal Pepper Protein no nombra etapa ni tiene tamaño: las `etapa_*` quedan vacías. `etapa_skt` sigue en Hatchery por la división Larvicultura.

## Fuera de alcance
- `etapa_competidor` no cambia (se quita en R4.10). `etapa_skt` no cambia.

## Restricciones de la constitución que más pesan acá
- Vacío antes que inventar o inferir.
- Normalizar en el parser con funciones de `schema.py`.
