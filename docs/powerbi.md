# Power BI: cómo unir los Excel de competencia

Los archivos están en `data/powerbi/<pais>/<empresa>.xlsx` (uno por país y empresa). Todos tienen las mismas 16 columnas, en el mismo orden y con los mismos tipos (ver `specs/tech-stack.md`). Se regeneran con `pipeline.py`.

## 1. Unir la carpeta completa

En Power BI Desktop: **Obtener datos → Carpeta**, apuntar a `data/powerbi` y **Combinar** usando la hoja `datos`. Si Power BI no encuentra la hoja `datos`, es un Excel de otra versión del pipeline: regenerarlo.

## 2. Graficar por etapa (despivotar las `etapa_*`)

Las 5 columnas de etapa son booleanas: un producto puede estar en más de una. Para graficar por etapa, despivotar las columnas `etapa_*` (`etapa_reproductores` … `etapa_engorde`) y filtrar solo las filas `true`:

1. Seleccionar `pais`, `empresa`, `nombre_producto` y las `etapa_*`.
2. **Transformar → Anular dinámica de otras columnas** (dejar `pais`, `empresa`, `nombre_producto` como fijas).
3. Filtrar `Valor` = `true` y renombrar `Atributo` a `etapa`.

**Advertencia:** un producto con varias etapas se cuenta una vez en cada una. Sumar por etapa no da el total de productos; para contar productos usar `nombre_producto` distinct sobre la tabla sin despivotar.

## 3. Notas

- Vacío significa que la fuente no lo dice. No es `false`.
- `etapa_skt` (`Hatchery`, `Nursery`, `Pre Grower`, `Grower`) es una sola columna y no se despivota.
