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
- [x] F4 Centroamerica sin fuente documentada en MEMORY.md "Expansión regional"
- [x] F5 cierre (2026-10-20): captcha levantado, honduras/mexico nicovita regenerados, pytest -q 190 ok, pipeline.py completo sin errores (ver "Cierre ronda 2")

- [x] R2.0 Nicovita pausada (usuario): fuentes.INACTIVAS; `pipeline.py` sin args la salta, `--empresa nicovita` la corre. ecuador/honduras/mexico nicovita = pausado (usuario)
- [x] R2.1 registro de conflictos: schema.resolver_campo(candidatos, reglas) + regla_coincidencia/regla_preferir; record['_conflictos'] -> pipeline.write_conflictos -> data/processed/{pais}/_conflictos.csv; build_master ignora '_*' y consolida data/conflictos.csv
- [x] R2.2 vimifos: celda con varias proteinas -> una fila por SKU ("Bumper Crop 30%"...). Bumper Crop/Natural Force/Total Range: M=1 calibre (2-6) -> 3 filas c/u. Nulos proteina: antes 3/15, despues 0/21
- [x] R2.3 apiaba: schema.reglas_titulo_vs_analisis (coincidencia > analisis_copiado_de > nombre_comercial) + resolver_y_registrar (reutilizable). Dorado 35%: titulo 35 + texto 35 x2 vs analisis 40 -> 35 (coincidencia). Nulos proteina: antes 1/3, despues 0/3
- [x] R2.4 nutrimar (ok): 19 filas (Zeigler 13 / Nutrimar 6). Fichas PDF /_files/ugd/*.pdf (pdfplumber via haid_scraper.extract_pdf_text) + imagen 'Tabla de Analisis' de Extensivo (haid_scraper.ocr_image, preproceso umbral 160). Validados vs ficha real: PL Raceway 40-9 (40%, 0.4-1.2 mm, 20 kg), Semi-intensivo (35/30% -> 2 SKUs, 1.6-2.5 mm, 25 kg), Extensivo (OCR 35%). Intensivo sin ficha publicada. Super growth usa el mismo PDF que Semi-intensivo
- [x] R2.5 Nicaragua/Panama: candidatos reconfirmados 2026-10-19 (1 request c/u, tabla abajo). NI y PA siguen con carga manual via GUI
- [x] R2.6 (2026-10-20) aquaxcel.com bajo un nivel sus encabezados (h1->h2, h2->h3): mexico/aquaxcel daba 0 filas y ecuador/aquaxcel perdia producto_salud (22/37 nulos). Parser acepta ambos niveles; fixture aquaxcel_mexico_listing_2026-10-20.html + test (mismas 14 filas que el 19/10). Ecuador vuelve a coincidir con el baseline
- [x] R2.8 (2026-10-20, decisión del usuario) Fase 5: src/registros_oficiales.py (SENASICA + eaduana). Solo completa vacíos con coincidencia exacta de nombre; todo queda en data/registros_oficiales.xlsx con estado. 162 registros: 16 coinciden, 1 difiere, 0 completados, 144 pistas sin match. NI/PA: no se duplica Honduras (usuario). HAID/Agripac: sin registros fuera de Ecuador
- [x] R2.9 (2026-10-20) GUI usaba run_empresa+write_csv: sin guarda de 0 filas ni _conflictos.csv. Ahora GUI y CLI usan pipeline.procesar(); la GUI también actualiza registros oficiales
- [x] R2.7 (2026-10-20) test_build_master_also_writes_one_master_per_pais no redirigia CONFLICTOS_PATH: cada `pytest` vaciaba data/conflictos.csv real. Arreglado (master.csv y conflictos.csv quedan identicos antes/despues de pytest)

- [x] R1 (pedido del usuario) reorganizar por pais: src/paises/<pais>/<empresa>.py con run(), _compartido/ para motores, master por pais, README por pais + ARQUITECTURA.md (169 tests ok)

## Fuentes por país
(pais | empresa | url | formato | campos | decision/estado) — verificado 2026-10-19
ecuador | nicovita | - | - | - | pausado (usuario) (R2.0; CSV actual se conserva)
honduras | nicovita | nicovita.com/categoria/camarones/?pais=honduras (11 productos -honduras) | HTML + PDF texto (PDFs compartidos con Ecuador) | todos los del parser PDF | pausado (usuario) (R2.0)
mexico | nicovita | ?pais=mexico (7 productos -mexico/-mexico-2) | HTML + PDF | idem | pausado (usuario) (R2.0)
nicaragua, panama | nicovita | ?pais=nicaragua/panama: 0 productos | - | - | sin_fuente_publica (Nicovita los atiende desde Honduras; carga manual)
mexico | aquaxcel | aquaxcel.com/productos/mexico/ | HTML estatico; parser Ecuador da 0 filas (layout distinto) | proteina, calibre, tecnologia, grasa, fibra | construir (ajuste de parser) -> pendiente
honduras/nicaragua/panama | aquaxcel | /productos/{honduras,centroamerica,nicaragua}/ = 404 | - | - | sin_fuente_publica
mexico | vimifos | vimifos.com/categoria/camaron -> /producto/xtrudix (+otras lineas /producto/*) | HTML estatico | presentacion, empaque, proteina, particula, peso especimen | construir -> pendiente
mexico | purina | nutrimentospurina.com/peces | HTML | solo tilapia/bagre/trucha, sin camaron | sin_fuente_publica (sin linea de camaron)
mexico | apiaba | acuacultura.com.mx/productos-marcas/api-camaron/ (productos en /productos/<slug>/; sitemap product-sitemap.xml) | HTML estatico, robots permite | nombre, empaque kg, proteina, humedad, fibra, micropellet | construir -> pendiente
mexico | azteca | aztecamexico.mx es sitio avicola/frizado, sin catalogo acuicola; busqueda web sin resultados | - | - | sin_fuente_publica
mexico | nutrimar | grupoacuicolamexicano.com.mx/nutrimar -> nutrimar.mx/<slug> | HTML SSR (Wix) + fichas PDF/imagen | nombre, proteina, calibre, empaque; empresa Zeigler/Nutrimar | ok (R2.4)
mexico | adm | sin catalogo publico encontrado | - | - | descartado (§6)
honduras/nicaragua/panama | biomar, cargill, haid, agripac | sin catalogo ni distribuidor publico encontrado (busqueda 2026-10-19) | - | - | sin_fuente_publica (carga manual via GUI; HAID/Agripac fuera por §6)

## R2.5 — Candidatos Nicaragua / Panamá (reconfirmado 2026-10-19)
pais | candidato | request | resultado | estado
nicaragua | Vitali Alimentos | vitalialimentos.com -> 200 (www) | home sin menciones de camaron/balanceado ni catalogo | sin_fuente_publica
nicaragua | Disagro (AQUAPLUS) | disagro.com/linea-acuicola/ -> 200 (redirige a disagro.com.gt) | solo insumos, ninguna mencion de "balanceado" | descartado (no fabrica balanceado)
panama | INASA / Larro (Grupo Calesa) | grupocalesa.com/inasa/ -> 307 a si misma (sin contenido) | sin productos de camaron publicados | sin_fuente_publica (carga manual: info@grupocalesa.com)
panama | Rivoflavia Inc., Nutricion Animal S.A. | sin sitio (solo registros FAO) | - | sin_fuente_publica
panama | Agromarina del Pacifico | sin sitio (importador/distribuidor) | - | sin_fuente_publica (carga manual: marca "Optiline")
- | Agro La Hacienda (Camaronina) | no reconsultado (Colombia, +57) | - | fuera_de_alcance (pais no objetivo)
- | Balnova | balnova.com -> 200 tras redirigir a www.adm.com | la marca no tiene sitio propio | descartado (sitio inexistente)

## Bloqueos
- RESUELTO 2026-10-20: captcha levantado; `pipeline.py --empresa nicovita` regenero honduras (38 filas, desde paginas guardadas en data/raw/nicovita_html/) y mexico (26 filas, en vivo, con pausas).
- 2026-10-19: nicovita.com redirige a validate.perfdrive.com (captcha Radware) tras muchas pruebas del dia. NO se evade (§4). Afecta ecuador/honduras/mexico nicovita: ecuador/nicovita.csv restaurado desde el baseline; honduras y mexico nicovita.csv quedaron vacios (los datos validados en F2 se regeneran con `python src/pipeline.py --empresa nicovita` cuando el bloqueo se levante). Guardas nuevas: netutil.BlockedError y no sobrescribir CSV con 0 filas.
- Falta para cerrar §7.3: regenerar honduras/mexico nicovita, correr `python src/pipeline.py` sin errores y escribir el cierre.

## Última iteración: F4 hecho; reintentos (netutil) y guardas; nicovita.com bloquea con captcha, esperando para regenerar.
Notas: sitio HAID rediseñado (Next.js, hrefs relativos): arreglado en scrapers/parsers haid. Agrizon da 429: reintento + pausa. Ecuador regenerado = baseline (test_ecuador_identity). aquaxcel parser usa LISTING_URL fijo (ecuador) en fuente_url: ajustar en F2.

## Cierre (2026-10-19) — DETENIDO POR FRENO DE SEGURIDAD, §7.3 NO CUMPLIDO
**Qué quedó:** Fase 0 completa (Ecuador idéntico al baseline), Fase 1 (tabla de fuentes), código reorganizado por país (`src/paises/<pais>/`, ver ARQUITECTURA.md), master por país, F2 (nicovita HN/MX, aquaxcel MX) y F3 (vimifos, apiaba, nutrimar parcial) construidos y validados; purina/azteca/adm descartados; Nicaragua/Panamá/Cargill-HN/BioMar-CA sin fuente pública. `pytest -q`: 169 pasan.
**Qué falta (condición 7.3.4 y parte de 7.3.5):** (1) nicovita.com bloquea con captcha Radware (no se evade): honduras/mexico nicovita.csv están vacíos y master.csv no tiene `honduras`. (2) agripac.com.ec no responde (timeout) hoy. (3) Una corrida completa de `python src/pipeline.py` sin errores.
**Cómo cerrarlo:** cuando nicovita.com y agripac.com.ec respondan (o con las páginas de Nicovita guardadas a mano, ver src/paises/_compartido/README.md): `python src/pipeline.py --empresa nicovita`, luego `python src/pipeline.py` completo y `pytest -q`; anotar aquí el resultado.
**Decisiones de §6 a revisar:** no duplicar Honduras en Nicaragua/Panamá; Fase 5 (SENASICA/eaduana) no ejecutada; HAID/Agripac solo Ecuador; Nutrimar solo con nombres (¿vale mantenerlo?); Api-Aba Dorado 35% resuelto en R2.3 (35, regla coincidencia).

## Cierre ronda 2 (2026-10-20) — §7.3 CUMPLIDO
**Verificación:** `python src/pipeline.py` sin argumentos → exit 0, 8/8 fuentes activas OK (Nicovita pausada, se corre aparte con `--empresa nicovita`). `pytest -q` → 190 pasan. `data/conflictos.csv` generado.

**Master (286 filas):**
pais | empresa | filas | proteina nula
ecuador | Agripac / BioMar / Cargill / HAID / Nicovita | 38 / 17 / 37 / 16 / 57 | 18 / 0 / 0 / 0 / 1 (= baseline, sin cambios)
honduras | Nicovita | 38 | 0
mexico | Nicovita / Cargill (Aquaxcel) / Vimifos / Api-Aba / Zeigler / Nutrimar | 26 / 14 / 21 / 3 / 13 / 6 | 0 / 0 / 0 / 0 / 0 / 1 (Intensivo, sin ficha publicada)
nicaragua, panama | - | 0 | carga manual via GUI

**Nulos de proteína antes → después:** Vimifos 3/15 → 0/21 (R2.2, celdas con varias proteínas separadas por SKU). Api-Aba 1/3 → 0/3 (R2.3). Nutrimar 17/17 → 1/19 (R2.4).

**Conflictos resueltos:** 1 — Api-Aba "APICAMARÓN Dorado 35% 20Kg", proteina_pct = 35 con regla `coincidencia` (título 35 + texto 35 ×2 vs análisis 40). Ninguno con `calibre_no_emparejable` (Vimifos emparejó todo con M=1) ni `ocr_fuera_de_rango` (Nutrimar).

**Decisiones de §6 cerradas (usuario, 2026-10-20):** NI/PA sin duplicar Honduras (carga manual); Fase 5 ejecutada (R2.8); HAID/Agripac solo Ecuador. **Queda:** Agripac Ecuador 18/38 proteínas nulas (son artemia/larvicultura, la fuente no las publica); revisar las 144 pistas de data/registros_oficiales.xlsx.
