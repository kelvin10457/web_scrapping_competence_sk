# México

Salida: `data/processed/mexico/`.

| Empresa | Módulo | Fuente | Estado |
|---|---|---|---|
| Nicovita | `nicovita.py` → `_compartido` | nicovita.com `?pais=mexico` + PDF | 26 filas |
| Aquaxcel (Cargill) | `aquaxcel.py` → `_compartido` | aquaxcel.com/productos/mexico | ok (14 filas, sin empaque; el sitio repite "Advance 35%" bajo `active`) |
| Vimifos | `vimifos.py` | vimifos.com/categoria/camaron → `/producto/<slug>` (tabla por línea) | ok (21 filas). Micras→mm; una celda con varias proteínas se separa en una fila por SKU (R2.2) |
| Api-Aba | `apiaba.py` | acuacultura.com.mx/productos-especies/camarones/ | ok (3 filas). Dorado 35%: título 35 vs análisis 40 → 35 con la regla `coincidencia`, registrado en `_conflictos.csv` (R2.3) |
| Nutrimar | `nutrimar.py` | nutrimar.mx (listado en grupoacuicolamexicano.com.mx/nutrimar) | ok (19 filas: `empresa` = Zeigler 13 / Nutrimar 6). Fichas PDF (pdfplumber) e imagen (OCR de HAID). Intensivo sin ficha → proteína `null` (R2.4) |

Descartadas: **Purina** (nutrimentospurina.com solo tilapia/bagre/trucha), **Azteca** (aztecamexico.mx es avícola), **ADM** (sin catálogo público).

## Competidores nuevos R7.4 (2026-11-09)

Research con Codex; acceso comprobado con `requests` solo donde dice "verificado". Implementar cada uno es una fase aparte.

| Empresa | Marca | Fuente | Datos | Acceso | Utilidad |
|---|---|---|---|---|---|
| Alimentos de Alta Calidad El Pedregal | Silver Cup | **Implementado (R7.5)**: `elpedregal.py`. Catálogo actual en 5 imágenes de los modales de `el-pedregal.com/alimento/crustaceos` (OCR) + tabla HTML `?t=mp` (migajas post-larva). `?t=ep` tiene nombres viejos; `?t=p` y `?t=e` dicen "(NO)" y no se enlazan: no se usan | Microtek (micropartículas µm y micropelets extruidos), Minipelet, Engorda Extruido 2.1 mm; proteína y uso por producto. 36 SKU | Verificado 2026-11-09: 200 con UA de navegador | **Alta** |
| Nueva Tecnología en Alimentación (Grupo Nutec) | AQUATEC | **Implementado (R7.6)**: `aquatec.py`, vía el distribuidor `nutrimentos.com.mx/acuicultura_1` (una página). 3 fichas completas (Performance, HD, Estándar) + 10 variantes con texto de plantilla | 11 SKU. Ficha: proteína del análisis, saco 25 kg. Variante: solo % y mm del nombre (no hereda) | Certificado SSL inválido: se acepta solo para ese dominio (decisión del usuario 2026-11-09); 200 con UA de navegador | **Alta** |
| BioBlue / Grupo NU3 (Multiservicios 2001 sin confirmar) | SKILLA 4008, 3505 | **Implementado (R7.8)**: `skilla.py`, bioblue.com/skilla/ | 4 filas (código × diámetro). Tamaño por OCR del pie de cada foto; etapa del rótulo (Inicio/Pre-engorda/Engorda); proteína no publicada | 200 con UA de navegador | Media |
| ProAqua (distribuidor): Epicore y Biogrow | Epifeed MBF/LHF, Epibal, Biogrow Formula 1–4, Biogrow XT ultra | **Implementado (R7.9)**: `proaqua.py`, categoría proaqua.mx/camaron/ (3 páginas) filtrada a alimentos formulados | 12 filas: proteína, micras→mm, empaque del corchete, etapas de la oración que define el producto | 200 con UA de navegador | Media |
| Alimentos Oromar | — | Sin sitio encontrado | — | — | Baja |

- **Nutrición Marina = Nutrimar** (grupoacuicolamexicano.com.mx/nutrimar). Ya cubierto.
- **Malta Texo = Apicamarón/Api-Aba (ADM).** Ya cubierto; su sitio ADM da 403.
