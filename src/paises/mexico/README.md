# México

Salida: `data/processed/mexico/`.

| Empresa | Módulo | Fuente | Estado |
|---|---|---|---|
| Nicovita | `nicovita.py` → `_compartido` | nicovita.com `?pais=mexico` + PDF | ok (26 filas) |
| Aquaxcel (Cargill) | `aquaxcel.py` → `_compartido` | aquaxcel.com/productos/mexico | ok (14 filas, sin empaque; el sitio repite "Advance 35%" bajo `active`) |
| Vimifos | `vimifos.py` | vimifos.com/categoria/camaron → `/producto/<slug>` (tabla por línea) | ok (15 filas). Micras→mm; si la celda trae varias proteínas (`30%, 35%, 40%`) queda `None` |
| Api-Aba | `apiaba.py` | acuacultura.com.mx/productos-especies/camarones/ | ok (3 filas). Dorado 35%: la página dice 35 en el título y 40 en el análisis → proteína `None` |
| Nutrimar | `nutrimar.py` | nutrimar.mx (listado en grupoacuicolamexicano.com.mx/nutrimar) | **parcial**: 17 filas solo con nombre (la fuente no publica proteína/calibre/empaque) |

Descartadas: **Purina** (nutrimentospurina.com solo tilapia/bagre/trucha), **Azteca** (aztecamexico.mx es avícola), **ADM** (sin catálogo público).
