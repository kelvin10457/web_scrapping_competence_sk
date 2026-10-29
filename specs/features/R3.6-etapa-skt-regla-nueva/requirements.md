# R3.6 — `etapa_skt` con la regla nueva

> Roadmap: [R3.6](../../roadmap.md) · Estado: se marca solo en el roadmap

## Contexto
Hoy `etapa_skt_from_row` deja vacío el hueco entre 1.6 mm y 1.8/1.9 mm, depende de `tipo_presentacion` para decidir si un producto es Grower y, cuando no hay tamaño, deja el campo vacío. La regla nueva (decisiones 2026-10-28) la define el tamaño, sin importar si el pellet es pellet o extruido.

## Requisitos
- **REQ-1:** Cortes por tamaño: menos de 1.6 mm → `Nursery`, 1.6 mm → `Pre Grower` y más de 1.6 mm → `Grower`, sea pellet o extruido. 1.7 mm → `Grower`. La función ya no recibe `tipo_presentacion`.
- **REQ-2:** En un rango (`1.4-2.0`) manda el tamaño mínimo, aunque el texto lo escriba al revés (`2.0-1.4` → 1.4 → `Nursery`).
- **REQ-3:** Sin tamaño, o con un tamaño sin número, se usa la etapa del competidor como respaldo: `larva` → `Hatchery`, `precria` → `Nursery`, `post_transferencia` → `Pre Grower` y `engorde` → `Grower`. `reproductores`, una etapa desconocida o un campo vacío dejan `etapa_skt` vacío. (Decisión del usuario, 2026-10-29.)
- **REQ-4:** `larva`, o la división Larvicultura de Agripac, siempre da `Hatchery`, aunque el producto tenga tamaño (caso Nicovita Origin, 0.3-0.8 mm). (Decisión del usuario, 2026-10-29: se corrige `tech-stack.md`.)

## Fuera de alcance
- `etapa_from_tamano` (respaldo de `etapa_competidor` en los parsers). Mantiene sus bandas viejas porque afectan a otra columna.
- La GUI (congelada).

## Restricciones de la constitución que más pesan acá
- Sin tamaño ni etapa del competidor, `etapa_skt` queda vacío: no se infiere.
