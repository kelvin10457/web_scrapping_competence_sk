## Checklist
- [x] F0.1 pais en schema + PAIS_VALUES (baseline Ecuador en tests/fixtures/master_ecuador_baseline.csv)
- [x] F0.2 fuentes.py + CLI --pais/--empresa + build_master recorre processed/*/*.csv
- [x] F0.3 parametrizar scrapers nicovita (pais_slug) y aquaxcel (pais_slug)
- [x] F0.4 pais en merge_human (matching), manual_store (ALTER TABLE), gui (tarjetas por pais/empresa, campo pais obligatorio)
- [x] F0.5 regenerar Ecuador con pipeline y verificar mismas filas (si falla: STOP, ver §5)
- [x] F1 descubrimiento de fuentes (tabla abajo)
- [x] F2 honduras/nicovita  (ok, validados 3/3: Classic Engorde, Finalis, Terap vs PDF; 38 filas; nota: classic-honduras se deduplica como alias)
- [x] F2 mexico/nicovita  (ok, validados 3/3: Classic, Katal, Terap vs PDF; 26 filas)
- [x] F2 mexico/aquaxcel  (ok, 14 filas verificadas vs HTML; sin empaque; el sitio repite "Advance 35%" bajo active)
- [x] F3 mexico/vimifos (ok, 15 filas, 3+ validadas vs pagina: Xtrudix 00, Race Way 1mm, Strong Breed)
- [x] F3 mexico/purina (sin_fuente_publica)
- [x] F3 mexico/apiaba (ok 3 filas validadas vs paginas; Dorado 35% proteina=None porque la pagina contradice titulo 35 vs analisis 40)
- [x] F3 mexico/azteca (sin_fuente_publica)
- [x] F3 mexico/nutrimar (parcial: 17 filas solo nombre; la fuente no publica proteina/calibre/empaque; validadas 3 vs paginas)
- [ ] F4 Centroamerica sin fuente: documentar en MEMORY.md
- [ ] F5 cierre: pytest -q, pipeline.py, MEMORY.md "Expansión regional", cierre aquí

## Fuentes por país
(pais | empresa | url | formato | campos | decision/estado) — verificado 2026-10-19
honduras | nicovita | nicovita.com/categoria/camarones/?pais=honduras (11 productos -honduras) | HTML + PDF texto (PDFs compartidos con Ecuador) | todos los del parser PDF | construir -> pendiente
mexico | nicovita | ?pais=mexico (7 productos -mexico/-mexico-2) | HTML + PDF | idem | construir -> pendiente
nicaragua, panama | nicovita | ?pais=nicaragua/panama: 0 productos | - | - | sin_fuente_publica (Nicovita los atiende desde Honduras; carga manual)
mexico | aquaxcel | aquaxcel.com/productos/mexico/ | HTML estatico; parser Ecuador da 0 filas (layout distinto) | proteina, calibre, tecnologia, grasa, fibra | construir (ajuste de parser) -> pendiente
honduras/nicaragua/panama | aquaxcel | /productos/{honduras,centroamerica,nicaragua}/ = 404 | - | - | sin_fuente_publica
mexico | vimifos | vimifos.com/categoria/camaron -> /producto/xtrudix (+otras lineas /producto/*) | HTML estatico | presentacion, empaque, proteina, particula, peso especimen | construir -> pendiente
mexico | purina | nutrimentospurina.com/peces | HTML | solo tilapia/bagre/trucha, sin camaron | sin_fuente_publica (sin linea de camaron)
mexico | apiaba | acuacultura.com.mx/productos-marcas/api-camaron/ (productos en /productos/<slug>/; sitemap product-sitemap.xml) | HTML estatico, robots permite | nombre, empaque kg, proteina, humedad, fibra, micropellet | construir -> pendiente
mexico | azteca | aztecamexico.mx es sitio avicola/frizado, sin catalogo acuicola; busqueda web sin resultados | - | - | sin_fuente_publica
mexico | nutrimar | grupoacuicolamexicano.com.mx/productos -> nutrimar.mx/<slug> (~30 productos) | HTML SSR (Wix) | nombre + descripcion; sin proteina | parcial (construir) -> pendiente
mexico | adm | sin catalogo publico encontrado | - | - | descartado (§6)
honduras/nicaragua/panama | biomar, cargill, haid, agripac | sin catalogo ni distribuidor publico encontrado (busqueda 2026-10-19) | - | - | sin_fuente_publica (carga manual via GUI; HAID/Agripac fuera por §6)

## Bloqueos
(ninguno)

## Última iteración: F3 nutrimar hecho (parcial). Siguiente: F4 documentar en MEMORY.md y F5 cierre.
Notas: sitio HAID rediseñado (Next.js, hrefs relativos): arreglado en scrapers/parsers haid. Agrizon da 429: reintento + pausa. Ecuador regenerado = baseline (test_ecuador_identity). aquaxcel parser usa LISTING_URL fijo (ecuador) en fuente_url: ajustar en F2.
