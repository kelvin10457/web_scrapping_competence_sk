# R11.3 — ProAqua México: microalgas Reed Mariculture para camarón

> Roadmap: [R11.3](../../roadmap.md) · Estado: se marca solo en el roadmap

## Contexto
R7.9 dejó fuera las microalgas de ProAqua. La categoría `proaqua.mx/reed-mariculture/` (1 página, 14 productos, verificado 2026-11-09) vende concentrados Instant Algae y LPB Frozen Shellfish Diet de Reed. Compiten con los suplementos de hatchery de Skretting (R11). **Corrección de hallazgos R11.1:** N-Rich PL Plus / High Pro son enriquecedores de rotífero, no se le dan al camarón, y quedan fuera (decisión 2026-11-09).

## Requisitos
- **REQ-1:** Del listado `/reed-mariculture/` entran solo 5 productos: Instant Algae **Isochrysis 1800**, **Tetraselmis 3600**, **TW 1200**, **TP 1800** (los que la tabla "Producto | Peces | Crustáceos | Camarón" de la ficha marca para Camarón) y **LPB** Frozen Shellfish Diet (trae una sección y una tabla de dosis para camarón). Quedan fuera N-Rich, Rotigrow, RotiGreen, Nanno, Rot-Diet, Shelfish Diet 1800 y la tela filtro. Son filas de la misma fuente `('mexico', 'proaqua')`, con `empresa` = `Reed Mariculture`.
- **REQ-2:** Nombre: `Instant Algae Isochrysis 1800`, `Instant Algae Tetraselmis 3600`, `Instant Algae TW 1200`, `Instant Algae TP 1800` (sin el prefijo "Concentrado de microalga", sin el paréntesis de la especie y sin espacios sobrantes) y `LPB Frozen Shellfish Diet` (del encabezado de la descripción "L P B Frozen Shellfish Diet ®", con las letras sueltas unidas).
- **REQ-3:** Tamaño = tamaño de la célula publicado, de µm a mm. Si hay dos dimensiones ("4,5-8 μm x 6-10 μm"), se toma la **primera**. TP 1800 → `0.0045-0.008`, TW 1200 → `0.006-0.02`, LPB ("Tamaño de la célula: 6-15 micrones") → `0.006-0.015`. Isochrysis y Tetraselmis no publican tamaño, así que queda vacío.
- **REQ-4:** Proteína: LPB "Proteína > 52.0%" → `52.0`. Las demás quedan vacías (no la publican). El empaque queda vacío en todas, porque se vende por litro (regla de R7.9).
- **REQ-5:** Etapas: `schema.detectar_etapas` sobre el párrafo propio del producto (el texto que sigue a la introducción genérica de Instant Algae, que termina en "…sistema de cultivo de zooplancton o tanque.") y no sobre la intro ni la tabla de especies. En LPB, solo sobre la sección "Camarón" de Aplicaciones (el título "Larvas, Juveniles y Reproductores" es para bivalvos). Resultado esperado: Tetraselmis, TP, TW y LPB → `larva`; Isochrysis → sin etapa. `tipo_presentacion` = `schema.detect_tecnologia` sobre ese mismo texto, y sin dato queda vacío.
- **REQ-6:** Las 12 filas de R7.9 no cambian (los tests de `tests/test_proaqua.py` siguen en verde) y `ScraperCompetencia.spec` incluye cualquier módulo nuevo.

## Fuera de alcance
- Enriquecedores y alimento de rotífero (N-Rich, Rotigrow, RotiGreen, Nanno 3600), dietas para bivalvos y peces, accesorios.
- Las dosis por estadio (N, Z1–M3) de la tabla de LPB: no se mapean a etapas.

## Restricciones de la constitución que más pesan acá
- Vacío antes que inferir (presentación, proteína y tamaño solo si están publicados).
- Normalizar en el parser con funciones de `schema.py`.
