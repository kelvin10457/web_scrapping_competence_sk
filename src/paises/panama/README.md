# Panamá

**Fuentes automatizadas desde 2026-11-09:** NasaFeed (R8.10) e Italcol (R8.11). Antes: sin fuente pública automatizable (verificado 2026-10-19). No hay fabricante local identificado; los productos llegan importados (Nicovita desde Honduras, BioMar desde Costa Rica, marcas ecuatorianas) y ninguna de esas empresas publica catálogo para Panamá.

Los productos se cargan a mano desde la GUI (campo `pais` = `panama`) o en `data/competencia_human.xlsx`. **No se duplican filas de otros países.**


## Descubrimiento R8.5 (2026-11-09)

Buscado: registro público de alimentos para animales (MIDA / APA) y catálogos de competidores de camarón.

| Fuente | URL | Qué trae | Formato | Login / captcha | Utilidad |
|---|---|---|---|---|---|
| Resolución APA 2021 sobre registro sanitario de alimentos para animales (Sistema Integrado de Trámite) | https://www.gacetaoficial.gob.pa/pdfTemp/29545/91672.pdf | Procedimiento de registro. **No es un listado de productos.** | PDF | Sí (el trámite va por plataforma) | Baja |
| Nicovita camarones (catálogo de la marca) | https://nicovita.com/categoria/camarones/ | Presentaciones peletizadas, microesferizadas y micro extruidas. Sin distribuidor en Panamá | Web | No | Media (sin Panamá en la página; no duplicar) |
| Italcol (AQUAMARÓN 35, Colombia) | https://italcol.com/producto/camaron-levante/ | Ficha de levante y finalización, 1 a 13 g. Declara presencia en Panamá | Web | No | Baja (fabricante colombiano, sin catálogo de distribución en Panamá) |

**Resultado:** no aparece un listado público de alimentos para camarón registrados en APA ni en MIDA. El único registro que menciona camarón es una lista de exportación de plantas extranjeras, que no sirve de catálogo. **Nada que implementar en R8.6.** Se carga a mano (R8.7).

**Actualización R8.8/R8.9 (2026-11-09):** MIDA/DINASA sí publica dos PDF de alimentos registrados (nacional y PGA; bajan solo con User-Agent de navegador). Desde R8.9 entran a `data/registros_oficiales.csv` como `fuente=mida`: 5 registros de camarón vigentes (AQUANASA 25/30/35 de Nutrición Animal, EXCELLENT CAMARÓN de Avícola Grecia, MATEMAX de Farallon Aquaculture). Sin proteína ni tamaño: no crean filas en el Excel.

## Competidores nuevos R7.4 (2026-11-09)

| Empresa | Marca | Fuente | Datos | Acceso | Utilidad |
|---|---|---|---|---|---|
| Nutrición Animal S.A. (NasaFeed) | Aquanasa Línea Premium | **Implementado (R8.10)**: `nasafeed.py`. Ficha PDF; si nasafeed.com no responde, usa la copia de Wayback (2024-08-30) | 3 filas `AQUANASA 25/30/35` (nombre del registro MIDA), 45.36 kg, Pellet, post larva a cosecha. Tamaño vacío: 1.4 y 2.4 mm sin asignar a cada proteína | El sitio da timeout (2026-11-09); Wayback responde | Alta |
| Avícola Grecia | Excellent Camarón | Solo registro MIDA | — | Sin sitio | Baja |
| Italcol (Colombia) | AQUACAMARON 35 | **Implementado (R8.11)**: `italcol.py`, italcol.com/producto/camaron-levante/ | 1 fila: 35 % de proteína, engorde ("hasta peso de cosecha") | 200 con UA de navegador | Media |
