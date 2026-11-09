# R7.9 — ProAqua (distribuidor, México): alimentos formulados

> Roadmap: [R7.9](../../roadmap.md) · Estado: se marca solo en el roadmap

## Contexto
ProAqua (`proaqua.mx`, tienda BigCommerce) vende 34 productos en la categoría Camarón (3 páginas). El usuario eligió solo los alimentos formulados (2026-11-09): Biogrow Formula 1–4, Biogrow XT Ultra, Epicore Epifeed MBF y LHF, y Epibal. Cada ficha tiene una descripción y tablas de composición; algunas tablas tienen una columna por variante.

## Requisitos
- **REQ-1:** Del listado de la categoría (todas las páginas) entran solo los productos cuyo nombre es Biogrow Formula, Biogrow XT, Epifeed o Epibal. `empresa` = fabricante (`Epicore` o `Biogrow`), igual que Prilabsa.
- **REQ-2:** Variantes: una tabla con una columna por variante da una fila por columna (Epifeed LHF → LHF1 y LHF2). Si el producto nombra una de las columnas, solo entra esa (Epibal-300 → solo la columna EPIBAL-300). Biogrow XT ultra da una fila por cada ficha técnica enlazada (0.3, 0.6 y 0.8 mm). La proteína de una tabla de un solo valor vale para todas las variantes del mismo producto.
- **REQ-3:** Tamaño: micras de la tabla ("Tamaño Partícula (microns)") o del texto ("de 40-150 micras"), pasadas a mm (`0.04-0.15`); en XT, el mm de la ficha. Empaque del corchete del nombre (`Saco 25 kilos` → 25; `Lata 1 libra` → 0.45). Un `litro` o un corchete sin número dejan el empaque vacío.
- **REQ-4:** Etapas con `schema.detectar_etapas` sobre el paréntesis del nombre ("(40-150 Micras Mysis)") y la oración que define el producto ("… es un/una …"), no sobre los beneficios (que mencionan PL como resultado). Presentación: fila "Forma" de la tabla (Granular → Granulado, Líquida → Líquido) o "tecnología de microencapsulación/extrusión" en el texto. Sin dato → vacío.
- **REQ-5:** `('mexico', 'proaqua')` está registrado y sus módulos están en `ScraperCompetencia.spec`.

## Fuera de alcance
- Congelados, microalgas, artemia, krill, aditivos y enriquecedores.
- EPIBAL-700: figura en la tabla pero ProAqua no lo vende.
- Las fichas PDF de Google Drive (repiten la tabla de la página).
