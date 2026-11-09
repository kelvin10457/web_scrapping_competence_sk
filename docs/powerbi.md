# Power BI: cómo unir los Excel de competencia

Los archivos están en `data/powerbi/<pais>/<empresa>.xlsx` (uno por país y empresa). Todos tienen las mismas 16 columnas, en el mismo orden y con los mismos tipos (ver `specs/tech-stack.md`). Se regeneran con `pipeline.py`.

## 1. Unir la carpeta completa

En Power BI Desktop: **Obtener datos → Carpeta** y apuntar a `data/powerbi`. Después, en Power Query, pegar esta consulta (reemplazar la ruta). Toma solo los archivos `.xlsx` de los subfolders y une sus hojas:

```m
let
    Origen = Folder.Files("C:\ruta\a\web_scrapping_competence_sk\data\powerbi"),
    XLSX = Table.SelectRows(Origen, each Text.EndsWith([Name], ".xlsx")),
    ConHoja = Table.AddColumn(XLSX, "Datos",
        each Excel.Workbook([Content], true){[Item="datos", Kind="Sheet"]}[Data]),
    Unido = Table.Combine(ConHoja[Datos]),
    Tipado = Table.TransformColumnTypes(Unido, {
        {"es_producto_de_salud", type logical},
        {"etapa_reproductores", type logical}, {"etapa_larva", type logical},
        {"etapa_post_larva", type logical}, {"etapa_precria", type logical},
        {"etapa_post_transferencia", type logical}, {"etapa_engorde", type logical},
        {"particula_min_mm", type number}, {"particula_max_mm", type number},
        {"proteina_pct", type number}
    })
in
    Tipado
```

Si Power BI no encuentra la hoja `datos`, es un Excel de otra versión del pipeline: regenerarlo.

## 2. Graficar por etapa (despivotar las `etapa_*`)

Las 5 columnas de etapa son booleanas: un producto puede estar en más de una. Para graficar por etapa, despivotar las columnas `etapa_*` (`etapa_reproductores` … `etapa_engorde`) y filtrar solo las filas `true`:

1. Seleccionar `pais`, `empresa`, `nombre_producto` y las `etapa_*`.
2. **Transformar → Anular dinámica de otras columnas** (dejar `pais`, `empresa`, `nombre_producto` como fijas).
3. Filtrar `Valor` = `true` y renombrar `Atributo` a `etapa`.

**Advertencia:** un producto con varias etapas se cuenta una vez en cada una. Sumar por etapa no da el total de productos; para contar productos usar `nombre_producto` distinct sobre la tabla sin despivotar.

## 3. Notas

- Vacío significa que la fuente no lo dice. No es `false`.
- `etapa_skt` (`Hatchery`, `Nursery`, `Pre Grower`, `Grower`) es una sola columna y no se despivota.
