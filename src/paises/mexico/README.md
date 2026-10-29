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
