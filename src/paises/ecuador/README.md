# Ecuador

Fuentes (`__init__.FUENTES`): nicovita, haid, aquaxcel, biomar, agripac. Salida: `data/processed/ecuador/`.

| Empresa | Módulo | Fuente | Notas |
|---|---|---|---|
| Nicovita | `nicovita.py` → `_compartido` | nicovita.com `?pais=ecuador` + fichas PDF | 57 filas. Activa de nuevo desde 2026-10-29 (pausas aleatorias de `netutil`, ~3 min) |
| HAID | `haid.py`, `haid_scraper/parser` | haid.com.ec + fichas PDF (3 son imagen → OCR con Tesseract) | Sitio rediseñado (Next.js): enlaces `/media/...` relativos; `og:title` trae sufijo " - Haid Ecuador" |
| Aquaxcel (Cargill) | `aquaxcel.py` → `_compartido` | aquaxcel.com/productos/ecuador | 37 filas |
| BioMar | `biomar.py`, `agrizon_scraper/parser` | Distribuidor Agrizon (Shopify `products.json`) | `biomar_scraper/parser.py` (biomar.com) quedan **sin usar** a propósito. Agrizon da 429: hay reintento con pausa |
| Agripac | `agripac.py`, `agripac_scraper/parser` | agripac.com.ec | 38 filas |

El master de Ecuador debe coincidir con `tests/fixtures/master_ecuador_baseline.csv` (`tests/test_ecuador_identity.py`).

## Competidores nuevos R7.4 (2026-11-09)

Research con Codex; acceso comprobado con `requests` solo donde dice "verificado". Implementar cada uno es una fase aparte.

| Empresa | Marca | Fuente | Datos | Acceso | Utilidad |
|---|---|---|---|---|---|
| Prilabsa (distribuidor) | Zeigler (págs. 5–15), Mackay Marine (16–21), Higashimaru (22–23) | **Implementado (R7.7)**: `prilabsa.py`, catálogo `prilabsa.com/assets/pdfs/CATALOGO%20PRODUCTOS%20JULIO%20PRILABSA.pdf` (caché 30 días en `data/raw/prilabsa/`) | 19 fichas → 47 SKU (una por tamaño en micras). Proteína, empaque, tipo y etapas de la ficha | Verificado 2026-11-09: 200 con UA de navegador | **Alta** (Hatchery) |
| Balnova | Clásico Camarón, Élite Camarón | agroshow.info/productos/alimentos-balanceados-para-camaron (y `-1`, Élite) | Granulado #4 (2.0–1.7 mm), engorde 22/28/35 % | Verificado: 200 (portal externo, no el sitio de Balnova) | Media |
| Molinos Champion | Aquachampion, HD, Starter, Classicfeed | molinoschampion.com/aquachampion/ | Familias; sin mm ni proteína verificados | Sin verificar | Baja |
| Naltech (Perú) | AQUATECH | aquatech.pe/camarones-langostinos/ | Imágenes; RSU Ecuador "AQUATECH Camarón 28 %" | Sin verificar | Baja |
| INVE | FRiPPAK, LANSY, EPAC | inveaquaculture.com | Etapas larvales; sin ficha cuantitativa | Sin verificar | Baja |
| Bioalimentar | — | bioalimentar.com | Sitio sin sección de camarón | — | Baja |

- **Alimentsa es de BioMar.** Ya cubierto.

## Hatchery / competencia de Ignis e InVita, R11.1 (2026-11-09)

Agrizon `products.json` trae hatchery que hoy no se extrae: Prilabsa Biomasa de Artemia Congelada, Bernaqua (Royal Caviar, Royal Seafood, MPEX), Zeigler Larval AP y Z-Plus, latas de Artemia Mackay. Cargill LiquaLife, INVE y Epicore no tienen fuente por país. Ver `specs/features/R11.1-hatchery/hallazgos.md`.
