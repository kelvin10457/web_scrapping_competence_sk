# R8.11 — Italcol AQUAMARÓN 35 (Panamá)

> Roadmap: [R8.11](../../roadmap.md) · Estado: se marca solo en el roadmap

## Contexto
Italcol (Colombia) declara presencia en Panamá. Su ficha `italcol.com/producto/camaron-levante/` trae descripción, registro ICA y composición garantizada. El usuario decidió que entre como fuente de Panamá (2026-11-09). El título de la página dice "AQUACAMARON 35" y la descripción dice "AQUAMARON 35".

## Requisitos
- **REQ-1:** 1 fila: `empresa = Italcol`, `nombre_producto` = título de la página (`AQUACAMARON 35`), `proteina_pct = 35` de "PROTEÍNA (MIN) 35.0%".
- **REQ-2:** Etapas con `schema.detectar_etapas` sobre la descripción: "hasta peso de cosecha" → `engorde`. "Levante" y "finalización" no son términos de etapa del esquema y no se mapean. Tamaño, presentación y empaque vacíos (la ficha no los da).
- **REQ-3:** `('panama', 'italcol')` está registrado y sus módulos están en `ScraperCompetencia.spec`.
