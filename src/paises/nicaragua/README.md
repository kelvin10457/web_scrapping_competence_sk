# Nicaragua

**Sin fuente pública automatizable** (verificado 2026-10-19). Nicovita lo atiende desde Honduras pero no publica catálogo propio (`?pais=nicaragua` no devuelve productos); Aquaxcel/Cargill y BioMar no tienen página ni distribuidor público.

Los productos se cargan a mano desde la GUI (campo `pais` = `nicaragua`) o en `data/competencia_human.xlsx`. **No se duplican filas de otros países.**


## Descubrimiento R8.3 (2026-11-09)

Buscado: registro público de alimentos para animales (IPSA) y catálogos de competidores de camarón.

| Fuente | URL | Qué trae | Formato | Login / captcha | Utilidad |
|---|---|---|---|---|---|
| Presentación IPSA sobre regulación de alimentos para animales | https://ipsa.gob.ni/Portals/0/Noticias/Congreso%20bovino/REGULACION%20DE%20ALIMENTOS%20PARA%20ANIMALES.pdf | Marco de registro sanitario de IPSA. **No es un listado de productos.** | PDF | No | Baja |
| Procedimiento de registro sanitario de productos de alimentación animal (2013) | https://nicaragua.justia.com/nacionales/resoluciones/procedimiento-para-el-reconocimiento-de-registro-sanitario-de-productos-utilizados-en-alimentacion-animal-sep-17-2013/gdoc | Requisitos y renovación (3 meses antes del vencimiento) | Web | No | Baja |
| Nicovita camarón (ficha técnica Finalis) | https://nicovita.com/wp-content/uploads/2020/07/FT-NICOVITA-FINALIS-CAMARON.pdf | Producto de la marca, sin distribución específica en Nicaragua | PDF | No | Media (ya cubierta por Nicovita Honduras, no duplicar) |
| Cargill (Purina) en Nicaragua | https://panoramaacuicola.com/2017/11/29/cargill-invierte-en-planta-procesadora-de-alimentos-para-camarones/ | Planta de alimento para camarón (noticia de 2017) | Web | No | Baja, dato antiguo |

**Resultado:** IPSA no publica un listado de piensos registrados que se pueda consultar. **Nada que implementar en R8.4.** Se carga a mano (R8.7).

## Competidores nuevos R7.4 (2026-11-09)

Sin fuente técnica nueva (research con Codex).
