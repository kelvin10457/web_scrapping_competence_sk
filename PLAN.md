# PLAN.md — Análisis de competencia: balanceado de camarón (Ecuador)

> Documento vivo. Se actualiza cada vez que cambia el alcance, el diseño técnico o el estado de una empresa. Para el historial de avance y hallazgos, ver `MEMORY.md`.

## 0. Objetivo de la fase actual (Fase 1 — pipeline de las 4 empresas, con profundidad de datos distinta por empresa)

> Este es el texto que se usa como prompt de `/loop` (sin intervalo, modo auto-ritmo).

Construir y validar el pipeline de scraping para las **4 empresas** (Nicovita, HAID, Aquaxcel, BioMar), respetando la profundidad de datos real de cada una, confirmada en `MEMORY.md`. *(Nota 2026-09-02: el esquema §3 se redujo después de completarse esta fase — este objetivo original hablaba de más columnas de las que existen hoy; ver `MEMORY.md` para el detalle del recorte.)*
- **Nicovita y HAID**: pipeline completo — descargar las fichas técnicas PDF reales, extraer todos los atributos del esquema unificado vigente (§3: identificación + composición nutricional).
- **Aquaxcel**: pipeline parcial — identificación (empresa, nombre_producto, etapa, tamaño_pellet_mm, tipo_presentacion, empaque_kg) más `proteina_pct`/`grasa_pct` por SKU, publicados en los bloques "Portafolio {LÍNEA}" del listado (ver `MEMORY.md`, corrección 2026-09-01).
- **BioMar**: pipeline parcial — scrapear únicamente los campos de identificación que sí están públicos (empresa, nombre_producto, etapa). El resto de columnas del esquema queda explícitamente `null` — no hay que inventar ni inferir esos valores.

Entregables de esta fase: `schema.py` (esquema unificado + normalización de "etapa"), un scraper+parser por empresa (4 módulos), `processed/{empresa}.csv` para las 4, y `master.csv` que las une (append) con el esquema idéntico.

Validación obligatoria: probar contra al menos 3 productos reales por empresa (o el total disponible si hay menos) y verificar que los valores extraídos coincidan con lo que dice la ficha/página real — no basta con que el código corra sin error.

Actualizar `MEMORY.md` con el avance conforme se completa cada empresa.

Detenerse y preguntar si: (a) el layout de una ficha no coincide con lo ya mapeado en `MEMORY.md`, (b) hace falta una decisión de negocio, o (c) ya se completó todo lo anterior para las 4 empresas.

**Explícitamente fuera de esta fase** (decisiones del usuario, no del loop): snapshot vs histórico (§5), formato del entregable final para gerencia (§5), conseguir datos nutricionales de Aquaxcel/BioMar por vías manuales (§5).

## 1. Objetivo

Construir un pipeline que scrapee y estructure, a nivel de **atributos por producto**, la oferta de balanceado de camarón de 4 competidores en Ecuador, para producir un dataset comparable y un entregable no técnico para gerencia.

## 2. Empresas objetivo y estado de disponibilidad de datos

| Empresa | Ficha técnica pública | Formato | Estrategia de extracción |
|---|---|---|---|
| **Nicovita** | ✅ Sí | PDF (texto seleccionable) | Parser PDF |
| **HAID** | ✅ Sí | PDF (texto seleccionable) | Parser PDF |
| **Aquaxcel** (Cargill Ecuador) | ⚠️ Parcial | HTML directo por SKU (línea/etapa/calibre/proteína/grasa) — sin fibra/ceniza/humedad/energía | Scraping HTML directo (sin PDF) |
| **BioMar** | ❌ No (biomar.com) | Ninguno en biomar.com — data técnica detrás de formulario de contacto/ventas | Solo JSON de Agrizon (distribuidor Ecuador) para tamaño/tipo/empaque/proteína/etapa — biomar.com deshabilitado en `pipeline.py` desde 2026-09-03 (decisión del usuario: solo interesan filas con datos técnicos reales; deja fuera productos sin match en Agrizon como Blue Impact/INICIO/SmartCare/EXIA Focus; ver `MEMORY.md`) |

Ver `MEMORY.md` § Hallazgos por empresa para el detalle de URLs y patrones confirmados.

## 3. Esquema de datos unificado

Un CSV por empresa con este esquema exacto; campos no disponibles quedan `null`. Ver `MEMORY.md` para el estado de completitud real por empresa.

**Identificación**: `empresa`, `nombre_producto` (incluye marca/submarca como texto libre, ej. "Nicovita Katal Proterra" — no hay columna separada de marca/submarca, ver decisión 2026-09-02 en `MEMORY.md`), `etapa` (valores normalizados: `larva`, `precria`, `post_transferencia`, `engorde`, `reproductores` — ya NO incluye `salud`, ver `producto_salud`), `producto_salud` (booleano — ¿tiene función terapéutica, ej. anti-Vibrio? Independiente de la etapa: un producto de salud puede cubrir cualquier rango de tamaño, ver `MEMORY.md` 2026-09-02), `etapa_camaron` (las 4 etapas propias del negocio — `Hatchery`, `Nursery`, `Pre Grower`, `Grower` —, derivadas de tamaño/proteína/tipo_presentacion; columna aparte de `etapa` porque no comparten vocabulario, ver `MEMORY.md` 2026-09-02), `tamano_pellet_mm` (texto tal cual lo publica la fuente, a veces un rango), `particula_min_mm`/`particula_max_mm` (derivadas numéricas de `tamano_pellet_mm` para poder promediar/filtrar/graficar por tamaño entre empresas — mismo valor en ambas si no hay rango que partir, ver `MEMORY.md` 2026-09-03), `tipo_presentacion`, `empaque_kg`

**Composición nutricional**: `proteina_pct`, `grasa_pct`

**Metadata**: `fuente_url`, `fecha_extraccion`

*(Reducido 2026-09-02 a pedido del usuario: se sacaron `fibra_pct`/`ceniza_pct`/`humedad_pct`, `estabilidad_agua_min` y los 4 booleanos cualitativos + `claims_texto_libre`. Ver `MEMORY.md` para el detalle y las columnas equivalentes en el código ya eliminado.)*

## 4. Arquitectura técnica

**Stack**: Python — `requests` + `BeautifulSoup` (no se necesita Playwright, los 4 sitios son HTML estático) + `pdfplumber`/`PyMuPDF` para PDFs + `pandas` para consolidar. Empaquetable como `.exe` con PyInstaller al no depender de navegador headless.

**Sin costo de API**: extracción por regex/keywords sobre texto ya extraído del PDF o del HTML. Sin LLM.

**Estructura de carpetas propuesta**:
```
data/
  raw/{empresa}/*.pdf          <- PDFs descargados (Nicovita, HAID)
  processed/{empresa}.csv      <- un CSV por empresa, mismo esquema
  processed/{empresa}.xlsx     <- espejo del CSV con columnas numericas en tipo real (evita que Excel corrompa decimales, ver MEMORY.md 2026-09-03)
  master.csv                   <- append de los 4, regenerado en cada corrida
  master.xlsx                  <- espejo de master.csv, mismo motivo
src/
  scrapers/{empresa}.py        <- 1 módulo por empresa (descubre productos + descarga fichas o extrae HTML)
  parsers/{empresa}.py         <- 1 parser por empresa (PDF o HTML -> dict de atributos)
  schema.py                    <- definición del esquema unificado + normalización de "etapa"
  pipeline.py                  <- orquesta: scrape -> parse -> normaliza -> CSV por empresa -> master.csv
```

**Flujo por empresa**:
1. Nicovita/HAID: listar productos → descargar PDF de ficha técnica → extraer texto/tablas → regex por atributo → normalizar.
2. Aquaxcel: scrapear los bloques "Portafolio {LÍNEA}" de la página de productos → extraer producto/etapa/calibre/tecnología/empaque/proteína/grasa por SKU.
3. BioMar: scrapear listado de productos → extraer producto/etapa (resto del esquema queda null; proteína/grasa se consiguen manualmente si se obtienen).

## 5. Decisiones pendientes

- [ ] **Histórico vs snapshot**: ¿se corre una sola vez o periódicamente? Define si `master.csv` se sobrescribe o acumula por `fecha_extraccion`. *(no confirmado aún)*
- [ ] **Entregable para gerencia**: Excel/Sheets con tabla filtrable vs dashboard interactivo vs resumen ejecutivo — pendiente de definir según cómo consume información el equipo directivo.
- [x] **Datos nutricionales de BioMar**: resuelto parcialmente 2026-09-03 — `proteina_pct`/`tamano_pellet_mm`/`tipo_presentacion`/`empaque_kg`/`etapa` ahora se completan automáticamente via Agrizon (distribuidor), ver `MEMORY.md` "BioMar — fuente complementaria Agrizon". `grasa_pct` sigue sin ninguna fuente pública conocida (ni biomar.com ni Agrizon) — ese hueco especifico sigue abierto, pendiente de vía manual si se necesita.

## 6. Fuera de alcance (por ahora)

- Extracción vía LLM/API de pago para estructurar fichas (descartado explícitamente por costo).
- Playwright/navegador headless (no requerido, los 4 sitios son estáticos).
- Atributos cualitativos de marketing más allá de keyword-matching simple.
