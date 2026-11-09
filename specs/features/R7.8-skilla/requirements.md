# R7.8 — Skilla (BioBlue / Grupo NU3, México)

> Roadmap: [R7.8](../../roadmap.md) · Estado: se marca solo en el roadmap

## Contexto
`bioblue.com/skilla/` publica el portafolio de alimento extruido SKILLA en tres etapas: Inicio (4008), Pre-engorda (4008 y 3505) y Engorda (3505). El tamaño solo está en el pie de la foto de cada etapa ("1 x 1.5 mm"); la proteína no se publica. Fuente nueva (decisión del usuario 2026-11-09).

## Requisitos
- **REQ-1:** Una fila por (código, diámetro): SKILLA 4008 en 1 y 1.5 mm, y SKILLA 3505 en 1.5 y 2.5 mm. Son 4 filas, `empresa = Skilla`, `nombre_producto = SKILLA <código>`.
- **REQ-2:** `tamano_pellet_mm` es el diámetro del pie de la foto ("diámetro x largo mm", leído por OCR). La foto se asigna a su código por el orden del título de la etapa ("4008 – 3505"). Sin pie legible, el tamaño queda vacío.
- **REQ-3:** Las etapas salen del rótulo de la etapa con `schema.detectar_etapas`: Pre-engorda → `post_transferencia`, Engorda → `engorde`, Inicio → ninguna (es una palabra genérica). `tipo_presentacion = Extruido` (la página dice "alimento extruido"). Proteína y empaque quedan vacíos.
- **REQ-4:** `('mexico', 'skilla')` está registrado y sus módulos están en `ScraperCompetencia.spec`.

## Fuera de alcance
- Deducir la proteína del código (4008 ≠ 40 % publicado).
- El empaque de 25 kg: está solo en la foto de la bolsa y el OCR no lo lee.
