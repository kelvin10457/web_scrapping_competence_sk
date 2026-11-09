# Panamá

**Sin fuente pública automatizable** (verificado 2026-10-19). No hay fabricante local identificado; los productos llegan importados (Nicovita desde Honduras, BioMar desde Costa Rica, marcas ecuatorianas) y ninguna de esas empresas publica catálogo para Panamá.

Los productos se cargan a mano desde la GUI (campo `pais` = `panama`) o en `data/competencia_human.xlsx`. **No se duplican filas de otros países.**


## Descubrimiento R8.5 (2026-11-09)

Buscado: registro público de alimentos para animales (MIDA / APA) y catálogos de competidores de camarón.

| Fuente | URL | Qué trae | Formato | Login / captcha | Utilidad |
|---|---|---|---|---|---|
| Resolución APA 2021 sobre registro sanitario de alimentos para animales (Sistema Integrado de Trámite) | https://www.gacetaoficial.gob.pa/pdfTemp/29545/91672.pdf | Procedimiento de registro. **No es un listado de productos.** | PDF | Sí (el trámite va por plataforma) | Baja |
| Nicovita camarones (catálogo de la marca) | https://nicovita.com/categoria/camarones/ | Presentaciones peletizadas, microesferizadas y micro extruidas. Sin distribuidor en Panamá | Web | No | Media (sin Panamá en la página; no duplicar) |
| Italcol (AQUAMARÓN 35, Colombia) | https://italcol.com/producto/camaron-levante/ | Ficha de levante y finalización, 1 a 13 g. Declara presencia en Panamá | Web | No | Baja (fabricante colombiano, sin catálogo de distribución en Panamá) |

**Resultado:** no aparece un listado público de alimentos para camarón registrados en APA ni en MIDA. El único registro que menciona camarón es una lista de exportación de plantas extranjeras, que no sirve de catálogo. **Nada que implementar en R8.6.** Se carga a mano (R8.7).
