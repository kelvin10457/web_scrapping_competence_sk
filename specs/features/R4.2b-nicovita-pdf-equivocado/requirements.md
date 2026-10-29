# R4.2b — Classic Orgánico Engorde (Honduras) con su ficha real

> Roadmap: [R4.2b](../../roadmap.md) · Estado: se marca solo en el roadmap

## Contexto
La página `nicovita-classic-organic-engorde-honduras` enlaza `FT-NICOVITA-ORIGIN-ORGANIC.pdf` (microesferas, PL4 a 1 g), aunque su propia descripción dice "alimento peletizado… desde 1 g hasta 8 gramos". La página hermana `nicovita-classic-organic-honduras`, con el mismo título, enlaza la ficha correcta (`FT-NICOVITA-CLASSIC-ORGANIC-CAMARON-HO.pdf`). Hoy esas 3 filas de Honduras tienen la proteína, el tamaño, la presentación y las etapas de Origin Orgánico. El usuario eligió corregir el enlace (2026-10-29).

## Requisitos
- **REQ-1:** `nicovita_scraper.find_pdf_url(html, url)` devuelve la ficha de Classic Orgánico para la página Classic Orgánico Engorde (Honduras) **solo** mientras esa página enlace la de Origin Orgánico. Si el sitio cambia el enlace, se usa lo que publique. Las demás páginas no cambian.
- **REQ-2:** Con la ficha corregida, la página tiene el mismo título y el mismo PDF que Classic Orgánico (Honduras), así que `scrape_all` la toma como alias y queda una sola fuente. Es el mismo criterio que ya junta Classic con Classic Engorde (Honduras).

## Fuera de alcance
- Otros errores del sitio que no estén comprobados con su ficha.

## Restricciones de la constitución que más pesan acá
- Vacío antes que inventar: la corrección se apoya en la página hermana (mismo título) y en la descripción de la propia página, y queda acotada a ese enlace exacto.
