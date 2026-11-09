# R3.3 — Los parsers usan `normalize_presentacion`

> Roadmap: [R3.3](../../roadmap.md) · Estado: se marca solo en el roadmap

## Contexto
Hoy `tipo_presentacion` sale con la grafía vieja (`Pelletizado`, 102 filas en Ecuador) y Agripac colapsa `Microextruido` (MeM, 2 filas) en `Extruido` porque pasa la pestaña "Tipo" por `detect_tecnologia`. Esta fase lleva los valores a la lista oficial desde el parser.

## Requisitos
- **REQ-1:** `detect_tecnologia` devuelve valores de la lista oficial: `Pellet` (antes `Pelletizado`), `Extruido`, `Polvo`, `Microparticulado`, `Líquido`.
- **REQ-2:** `etapa_from_tamano` y `etapa_skt_from_row` aplican el umbral de Grower de pellet (≥1.8 mm) con `Pellet` (y siguen aceptando `Pelletizado`).
- **REQ-3:** Agripac toma el texto de la pestaña "Tipo" (sin el rótulo "Tipo") y lo pasa por `normalize_presentacion`: MeM → `Microextruido`. Alias nuevos en schema: `Micro particulado` → `Microparticulado`, `Líquidos` → `Líquido`.
- **REQ-4:** Agrizon: si título y tags no dicen la tecnología pero hay un tag `Microgranulado`, se guarda `Microgranulado` tal cual (valor desconocido, lo avisará R3.4). Si hay otro tag de tecnología (ej. `Pelletizado`), ese gana como hoy.
- **REQ-5:** Aquaxcel pasa su columna "Tecnología" por `normalize_presentacion` (`Pelletizado` → `Pellet`).
- **REQ-6:** Ecuador regenerado difiere del baseline solo en `tipo_presentacion` (cambios esperados de REQ-1..5); ninguna otra columna cambia. El baseline se actualiza.

## Fuera de alcance
- `merge_human.py` y la GUI (`TIPO_PRESENTACION_VALUES` queda como está): el usuario planea reemplazar merge_human por archivos aislados por país y empresa.
- El aviso de valores desconocidos: R3.4.

## Restricciones de la constitución que más pesan acá
- Normalizar en el parser, con funciones de `schema.py`.
- Vacío antes que inventar: `Microgranulado` no se fuerza a `Granulado`.
