# R4.9 — Nutrimar: etapas desde fuente local

## Contexto
El parser solo extraía nutrientes y calibres. Las fichas reales publican etapas; el OCR de Extensivo solo tiene análisis nutricional.

## Requisitos
- **REQ-1:** Nombre + ficha completa cuando existe; PL Raceway marca post_larva, precria, post_transferencia y engorde: post larvas, nursery y «hasta el engorde» (rango compartido).
- **REQ-2:** Semi-intensivo marca engorde en ambos SKU: normalizar ENGORDA a engorde y conservar «hasta la cosecha».
- **REQ-3:** Sin ficha, usar nombre + párrafos/encabezados de main: EZ Larva marca larva; Intensivo queda vacío. Excluir navegación, footer, scripts y URL.
- **REQ-4:** Sin términos explícitos en nombre/ficha, vacío aunque haya calibre o categoría. OCR de Extensivo queda vacío. Todos los caminos, incluso rechazo OCR, llevan _etapas_detectadas=True.

## Fuera de alcance
Inferir por talla/adulto/marca/categoría, cambiar nutrientes, campo legado, pipeline, red, roadmap o commits.
