# R7.5 — El Pedregal (México)

> Roadmap: [R7.5](../../roadmap.md) · Estado: se marca solo en el roadmap

## Contexto
El Pedregal Silver Cup publica su catálogo de crustáceos en `el-pedregal.com/alimento/crustaceos`. El catálogo actual está en 5 imágenes (modales de la página principal: larvas, larvas y postlarvas, preengorda, engorda); las tablas HTML (`?t=ep`, `?t=mp`, `?t=p`, `?t=e`) usan nombres viejos. Decisión del usuario (2026-11-09): imágenes por OCR + solo la tabla `?t=mp` (migajas post-larva, que no aparecen en las imágenes). `?t=p` y `?t=e` (título "(NO)", sin enlace en el sitio) y `?t=ep` (reemplazada por las imágenes) no entran.

## Requisitos
- **REQ-1:** El scraper toma de la página principal las URL de las imágenes de los modales (`img/crustaceos-info-N.png`), en el orden del HTML, y la URL `?t=mp`. No pide `?t=ep`, `?t=p` ni `?t=e`.
- **REQ-2:** Del texto OCR, cada título con `(PP-GG)` es un producto. Se genera **una fila por tamaño** publicado: `Micropartículas` en µm → mm y `Microparticulado`; `Micropelets` de Microtek → `Extruido` (el PDF `Alimentos-Extruidos-Crustaceos.pdf` del fabricante dice "micropelets extruidos de 0.6, 0.8, 1 y 1.4mm"); `Minipelets` → sin tipo; `Pelets` de "ENGORDA EXTRUIDO" → `Extruido`. Microtek BD = 3 + 4 = 7 filas.
- **REQ-3:** `proteina_pct` sale de la línea `PROTEINA: NN% Mínimo`. En `Pelets: 2.1 x 3 mm` el tamaño es el diámetro (2.1). Si el OCR perdió el punto ("21x 3") y el título dice "2.1 mm", vale el título.
- **REQ-4:** Las etapas salen del encabezado de sección + la línea `Uso:`. `detectar_etapas` reconoce "engorda" → `engorde` y "preengorda"/"pre-engorda" → `post_transferencia` (decisión del usuario 2026-11-09), sin que "engorda" dentro de "preengorda" marque engorde.
- **REQ-5:** La tabla `?t=mp` da 8 filas "Migajas # N Peletizado (PP-GG)" con rango de tamaño ("0.6-0.85"), proteína de la columna "Proteína (mín)", `Pellet` y `post_larva`.
- **REQ-6:** `mexico/elpedregal` está registrada en `paises.mexico.FUENTES` (empresa "El Pedregal") y en el `.spec` de PyInstaller.

## Fuera de alcance
- Grasa, fibra, ceniza, humedad (no están en el esquema). Empaque (no se publica).
- `?t=ep`, `?t=p`, `?t=e` y el PDF de tabla de alimentación (imagen).

## Restricciones de la constitución que más pesan acá
- Vacío antes que inferir (Minipelets sin tipo; sin empaque).
- OCR local (Tesseract), sin APIs pagas. Normalizar en el parser.
