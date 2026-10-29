# R3.4 — Aviso de presentaciones desconocidas

> Roadmap: [R3.4](../../roadmap.md) · Estado: se marca solo en el roadmap

## Contexto
Desde R3.3 un `tipo_presentacion` fuera de la lista oficial se conserva tal cual (hoy: `Microgranulado` en Ecuador, y `Pelletizado` en México/Honduras porque todavía no se regeneraron). Nadie se entera salvo que revise el master a mano.

## Requisitos
- **REQ-1:** `schema.presentaciones_nuevas(df)` devuelve las filas cuyo `tipo_presentacion` no está en `TIPO_PRESENTACION_OFICIAL`, con columnas `pais, empresa, producto, valor, url`. Los vacíos no se avisan.
- **REQ-2:** `build_master` escribe `data/presentaciones_nuevas.csv` con esas filas, tomadas del master completo (snapshot de todos los países, como `conflictos.csv`). Si no hay ninguna, el archivo queda solo con el encabezado.
- **REQ-3:** Al final del CLI se imprime un resumen: cantidad por valor y la ruta del CSV. Sin valores nuevos no se imprime nada.

## Fuera de alcance
- La GUI (congelada, decisión 2026-10-29).
- Agregar valores a la lista oficial: lo decide el usuario al ver el aviso.

## Restricciones de la constitución que más pesan acá
- Un valor desconocido no es error: se conserva y se avisa, no se fuerza a `Otro`.
