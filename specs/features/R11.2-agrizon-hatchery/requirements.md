# R11.2 — Agrizon: hatchery de Prilabsa y proteína de Bernaqua

> Roadmap: [R11.2](../../roadmap.md) · Estado: se marca solo en el roadmap

## Contexto
R11.1 encontró hatchery en Agrizon (`products.json`). Zeigler y Mackay ya los trae Prilabsa (PDF), y los Bernaqua (Royal Caviar, Royal Seafood, MPEX, MeM, Royal Pepper Protein) ya los trae Agripac, pero **sin proteína**. Lo nuevo es Megasupply **Megalikuid B/C** (dieta líquida, rival de InVita) y Prilabsa **Biomasa de Artemia Congelada** (compite con Ignis). Decisión 2026-11-09: agregar esa fila y completar la proteína vacía de los Bernaqua de Agripac con el dato de Agrizon, sin duplicar filas.

## Requisitos
- **REQ-1:** `prilabsa.run()` suma 1 fila "Biomasa de Artemia Congelada" (`empresa` Prilabsa, `fuente_url` agrizon, `empaque_kg` 1, `etapa_post_larva` true por el tag "Post-larva", proteína y tipo_presentacion vacíos porque la fuente no los dice).
- **REQ-2:** La proteína de Bernaqua sale del `body_html` de Agrizon ("Proteína 55%"). Un rango ("55-60%") queda vacío (`normalize_proteina`).
- **REQ-3:** Una fila de Agripac **sin proteína** cuyo nombre coincide con un Bernaqua de Agrizon (sin tener en cuenta mayúsculas, guiones largos, espacios ni el empaque final "400 gr", "5kg" o "1lt") toma la proteína de Agrizon, y queda una fila en `_conflictos.csv` con la regla `completado:agrizon`.
- **REQ-4:** Si Agripac ya trae proteína, no se pisa. Si difiere de la de Agrizon, gana Agripac y queda en `_conflictos.csv` (regla `agripac`).
- **REQ-6:** Fuente nueva `megasupply` (Ecuador): las dietas líquidas **Megalikuid** de Megasupply que vende Agrizon (rivales directos de InVita), una fila por producto. La proteína sale del body ("Proteína 6.5%"), el tamaño de "(50-120μ)" en mm, `tipo_presentacion` Líquido y etapas larva + post_larva. Promegabiotic (probiótico) no entra.
- **REQ-5:** Si Agrizon falla (red), Agripac y Prilabsa siguen saliendo como hoy, con un aviso.

## Fuera de alcance
- Filas de Zeigler y Mackay desde Agrizon (duplicarían a Prilabsa).
- Cambiar `empresa` de los Bernaqua (siguen como Agripac).

## Restricciones de la constitución que más pesan acá
Vacío antes que inferir; los conflictos van con `schema.resolver_campo` a `_conflictos.csv`; Agrizon pide pausas (429).
