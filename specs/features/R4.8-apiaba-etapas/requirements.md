# R4.8 — Api-Aba: etapas explícitas

## Corrección previa por evidencia
El comentario del parser dice que no hay etapas normalizables. Los fixtures reales lo contradicen: Dorado 40 dice postlarval/postlarva y Dorado 35 dice «iniciación o engorda». Se corrige esa premisa antes de implementar. «Engorda» es la grafía de engorde; «iniciación» no es un término del detector.

## Requisitos
- **REQ-1:** Dorado 40 marca solo post_larva.
- **REQ-2:** Dorado 35 marca solo engorde; normalizar engorda a engorde antes de detectar.
- **REQ-3:** Raceways queda vacío con marcador explícito; no inferir por nombre, crecimiento o calibre ni usar tarjetas relacionadas/navegación.

## Fuera de alcance
Campo legado, proteína, tamaños, red, pipeline, roadmap y commits.
