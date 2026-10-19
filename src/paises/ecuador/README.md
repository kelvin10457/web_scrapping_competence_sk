# Ecuador

Fuentes (`__init__.FUENTES`): nicovita, haid, aquaxcel, biomar, agripac. Salida: `data/processed/ecuador/`.

| Empresa | Módulo | Fuente | Notas |
|---|---|---|---|
| Nicovita | `nicovita.py` → `_compartido` | nicovita.com `?pais=ecuador` + fichas PDF | 57 filas; ver el bloqueo anti-bot en `PROGRESO_REGIONAL.md` |
| HAID | `haid.py`, `haid_scraper/parser` | haid.com.ec + fichas PDF (3 son imagen → OCR con Tesseract) | Sitio rediseñado (Next.js): enlaces `/media/...` relativos; `og:title` trae sufijo " - Haid Ecuador" |
| Aquaxcel (Cargill) | `aquaxcel.py` → `_compartido` | aquaxcel.com/productos/ecuador | 37 filas |
| BioMar | `biomar.py`, `agrizon_scraper/parser` | Distribuidor Agrizon (Shopify `products.json`) | `biomar_scraper/parser.py` (biomar.com) quedan **sin usar** a propósito. Agrizon da 429: hay reintento con pausa |
| Agripac | `agripac.py`, `agripac_scraper/parser` | agripac.com.ec | 38 filas |

El master de Ecuador debe coincidir con `tests/fixtures/master_ecuador_baseline.csv` (`tests/test_ecuador_identity.py`).
