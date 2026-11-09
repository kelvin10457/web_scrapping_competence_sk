# Honduras

Fuente: **Nicovita** (`nicovita.py`, motor `_compartido`), nicovita.com `?pais=honduras`, 8 páginas únicas / 35 filas. Las fichas PDF se comparten con Ecuador.

- `nicovita-classic-honduras` se deduplica como alias de otra página con el mismo PDF.
- `nicovita-classic-organic-engorde-honduras` enlaza por error la ficha de Origin Orgánico: el scraper usa la de Classic Orgánico (`_PDF_CORREGIDO`, R4.2b) y la página queda como alias de `nicovita-classic-organic-honduras`.
- Aquaxcel/Cargill y BioMar: sin catálogo ni distribuidor público (`/productos/honduras/` = 404) → carga manual.
- Nicovita atiende **Nicaragua y Panamá desde Honduras**: no se copian filas a esos países (decisión del usuario 2026-10-20, ver `specs/decisiones.md`).


## Descubrimiento R8.1 (2026-11-09)

Buscado: registro público de alimentos para animales (SENASA) y catálogos de competidores de camarón.

| Fuente | URL | Qué trae | Formato | Login / captcha | Utilidad |
|---|---|---|---|---|---|
| Marco legal SENASA (acuerdos de registro de piensos, inscripción de establecimientos) | https://www.tsc.gob.hn/web/leyes/Acuerdo_SENASA-05-2018.pdf · https://www.tsc.gob.hn/web/leyes/Acuerdo-SENASA-001-2020.pdf | Reglas de registro y vigencia (2 años). **No es un listado de productos.** | PDF | No | Baja |
| Fichas Nicovita Honduras | https://nicovita.com/productos/nicovita-classic-honduras/ · https://nicovita.com/productos/nicovita-classic-organic-engorde-honduras/ | Producto, proteína mínima, grasa, formatos, enlace a ficha PDF | HTML + PDF | No | Alta (ya implementada, R2/R4) |
| Directorio de exportadores 2021 (SDE) | https://sde.gob.hn/wp-content/uploads/2021/08/Directorio-Exportadores-2021-final-1.pdf | Exportadores; Cargill aparece como exportador de harina de camarón, no como distribuidor | PDF | No | Baja |

**Resultado:** no aparece un registro público de SENASA con productos de alimento para camarón. Se buscó en búsqueda web (estándar y extendida) con términos de SENASA, registro de piensos y listado de productos. Competidores sin fuente pública: Skretting, BioMar y Cargill (Aquaxcel). **Nada que implementar en R8.2.** Nicovita Honduras ya está cubierta.

**Pendiente de verificar a mano:** un listado de piensos registrados en SENASA (portal) si existe; las fichas de Nicovita Honduras tienen unos 5–6 años (metadatos), conviene confirmarlas vigentes.

## Competidores nuevos R7.4 (2026-11-09)

Sin fuente técnica nueva. ALCON es marca de Cargill (cargill.com.hn), ya cubierto.

## Hatchery / competencia de Ignis e InVita, R11.1 (2026-11-09)

No apareció ningún distribuidor de alimentos de hatchery con ficha pública. Detalle en `specs/features/R11.1-hatchery/hallazgos.md`.
