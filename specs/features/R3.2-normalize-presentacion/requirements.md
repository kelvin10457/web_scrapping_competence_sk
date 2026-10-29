# R3.2 — `schema.normalize_presentacion`

> Roadmap: [R3.2](../../roadmap.md) · Estado: se marca solo en el roadmap

## Contexto
`tech-stack.md` fija la lista oficial de `tipo_presentacion` y la decisión del 2026-10-28 cambia `Pelletizado` → `Pellet`. Hoy el CSV maestro trae `Pelletizado` (459 filas), `Extruido` (219), `Polvo` (24), `Microparticulado` (21) y `Líquido` (3). Esta fase solo agrega la función; los parsers la usan en R3.3.

## Requisitos
- **REQ-1:** `schema.TIPO_PRESENTACION_OFICIAL` es exactamente la lista de `tech-stack.md` (12 valores).
- **REQ-2:** Un valor de la lista oficial se devuelve con la grafía oficial, sin importar mayúsculas, tildes ni espacios en los extremos (`"líquido "` → `"Líquido"`, `"LIQUIDO"` → `"Líquido"`).
- **REQ-3:** `Pelletizado` (y `Pelletizada`, `Peletizado`) → `Pellet`, con la misma tolerancia de REQ-2.
- **REQ-4:** Un valor desconocido se devuelve tal cual (solo sin espacios en los extremos), sin error.
- **REQ-5:** `None`, `""` o solo espacios → `None`.

## Fuera de alcance
- Cambiar `detect_tecnologia`, los parsers o `TIPO_PRESENTACION_VALUES` (GUI / merge_human): R3.3.
- El aviso de valores desconocidos: R3.4.

## Restricciones de la constitución que más pesan acá
- Vacío antes que inventar: lo desconocido no se fuerza a `Otro`.
- Avisar lo desconocido, no esconderlo: se conserva el valor.
