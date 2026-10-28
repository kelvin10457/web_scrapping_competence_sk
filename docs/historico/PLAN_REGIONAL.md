# PLAN_REGIONAL.md — Expansión del scraping de competencia a Honduras, Nicaragua, Panamá y México

> Plan para Claude Code. Complementa a `PLAN.md` (Ecuador, Fase 1 ya cerrada) y a `MEMORY.md`.
> **Leer ambos antes de empezar.** Todas las reglas de `PLAN.md` siguen vigentes: no inventar ni inferir valores, `null` cuando no hay dato, nada de LLM/APIs pagas, validar contra productos reales.
> Registrar en `MEMORY.md` el avance y los hallazgos de cada país (sección nueva "Expansión regional").

---

## 0. Objetivo

Que el pipeline actual (pensado solo para Ecuador) funcione **por país**, sin duplicar código, y sumar los competidores de Honduras, Nicaragua, Panamá y México. Al terminar:

- `master.csv` / `master.xlsx` con una columna `pais` y todas las filas de los 5 países.
- Un CSV por país y empresa: `data/processed/{pais}/{empresa}.csv`.
- La GUI y `merge_human.py` siguen funcionando y entienden `pais`.

**Fuera de alcance de este plan:** histórico vs snapshot (sigue pendiente en `PLAN.md` §5), entregable para gerencia, y fuentes de pago (ImportGenius, Volza, etc.).

---

## 1. Hallazgos previos (verificados el 2026-10-19, hay que reconfirmarlos en la Fase 1)

| Empresa | Sitio | ¿Tiene catálogo por país? | Nota |
|---|---|---|---|
| Nicovita (Vitapro) | nicovita.com | **Sí.** El selector tiene Ecuador, Honduras, México y Perú. `/categoria/camarones/?pais=honduras` devuelve URLs `nicovita-*-honduras/` | **No hay Nicaragua ni Panamá.** Se atienden desde la planta de Honduras. Los PDF **se comparten entre países**: `nicovita-katal-honduras/` enlaza al mismo `FT-NICOVITA-KATAL-CAMARON.pdf` que usa Ecuador. |
| Aquaxcel (Cargill) | aquaxcel.com | **Parcial.** Solo existen `/productos/ecuador/` y México en el selector | No hay página para Centroamérica. Cargill opera en HN/NI con plantas propias, pero no apareció ningún catálogo web. |
| BioMar | biomar.com | No (igual que en Ecuador: la info técnica está detrás de un formulario) | Abastece Centroamérica desde su planta de Costa Rica. Hay que buscar distribuidores locales, como en Ecuador se hizo con Agrizon. |
| Vimifos | vimifos.com | México. Línea acuícola: `https://vimifos.com/producto/xtrudix` | La home no enlaza fichas PDF. Revisar la página de producto. |
| Purina (Nutrimentos Purina / Cargill MX) | nutrimentospurina.com | México. Línea "Nutripec"; marca histórica "Camaronina" | Confirmar si publica proteína y calibre. |
| Api-Aba | acuacultura.com.mx | México. Línea APICAMARÓN® Dorado 35% / 40% (sacos de 20 kg) | Páginas de producto con nombre y proteína. |
| Nutrimentos Acuícolas Azteca | aztecamexico.mx | México. AZTECA 35% / 40% | Revisar si hay ficha técnica. |
| Nutrimar (Grupo Acuícola Mexicano) | grupoacuicolamexicano.com.mx | México. Alimento larvario y de engorde | Probablemente solo lista nombres (sin proteína). |
| ADM | — | México | Sin catálogo público conocido. Solo se investiga; no se construye nada si no aparece una fuente. |
| HAID, Agripac | — | — | Hasta ahora solo Ecuador. Revisar si venden en algún país objetivo; si no, se quedan fuera. |
| Skretting | — | — | **Excluir.** Es la propia empresa. |

**Panamá** es el país con menos información: no hay fabricante local identificado. Lo más probable es que los productos lleguen importados de Nicovita (HN), BioMar (CR) y marcas ecuatorianas.

---

## 2. Decisiones de diseño (aplicar tal cual, salvo que algo choque con el código existente)

### 2.1 Esquema
Agregar a `schema.SCHEMA_COLUMNS`, al inicio, la columna **`pais`**, con estos valores válidos: `ecuador`, `honduras`, `nicaragua`, `panama`, `mexico`. Debe quedar como constante `schema.PAIS_VALUES`.

- `pais` es el **país donde se vende/publica** el producto, no donde se fabrica.
- Si un catálogo de un país se usa como aproximación para otro (por ejemplo, el catálogo de Nicovita Honduras para Nicaragua), **no se duplican filas**. Esto se deja como **decisión pendiente del usuario** (ver §6). Por defecto, solo se cargan filas para los países que tienen catálogo propio.
- No se toca ninguna otra columna. `etapa_competidor`, `etapa_skt`, `tipo_presentacion`, etc. siguen con la misma normalización.

### 2.2 Registro de fuentes (reemplaza los `if empresa == ...` de `pipeline.run_empresa`)
Crear `src/fuentes.py` con un registro declarativo. Cada entrada es una tupla `(pais, empresa)`:

```python
FUENTES = {
    ("ecuador", "nicovita"):  {"scraper": "nicovita", "parser": "nicovita", "params": {"pais_slug": "ecuador"}},
    ("honduras", "nicovita"): {"scraper": "nicovita", "parser": "nicovita", "params": {"pais_slug": "honduras"}},
    ("mexico", "nicovita"):   {"scraper": "nicovita", "parser": "nicovita", "params": {"pais_slug": "mexico"}},
    ("ecuador", "aquaxcel"):  {"scraper": "aquaxcel", "parser": "aquaxcel", "params": {"pais_slug": "ecuador"}},
    ("mexico", "aquaxcel"):   {"scraper": "aquaxcel", "parser": "aquaxcel", "params": {"pais_slug": "mexico"}},
    ("ecuador", "biomar"):    {"scraper": "agrizon",  "parser": "agrizon",  "params": {}},
    # ... haid, agripac (ecuador) y las nuevas de mexico
}
```

- Si el sitio es el mismo y solo cambia el país (Nicovita, Aquaxcel), se **parametriza el scraper existente** con `pais_slug`. No se copia el módulo.
- Las empresas nuevas tienen su propio par `scrapers/{empresa}.py` y `parsers/{empresa}.py`, igual que ahora.
- El contrato de cada scraper es `scrape_all(**params)`, y el del parser devuelve `list[dict]`. El pipeline agrega `pais` a cada registro; los parsers no lo hacen.

### 2.3 Archivos
```
data/
  raw/{empresa}/*.pdf                 <- se comparte entre países (los PDFs de Nicovita se repiten); el nombre de archivo es la clave
  processed/{pais}/{empresa}.csv|xlsx
  master.csv|xlsx                     <- todos los países, con la columna pais
```
- Migración: los `data/processed/{empresa}.csv` actuales se mueven a `data/processed/ecuador/`. Se regeneran corriendo el pipeline; no se mueven a mano.
- `build_master()` recorre `processed/*/*.csv`.

### 2.4 CLI del pipeline
```
python src/pipeline.py                         # todo
python src/pipeline.py --pais honduras         # todas las empresas de un país
python src/pipeline.py --pais mexico --empresa nicovita
python src/pipeline.py --empresa nicovita      # nicovita en todos sus países
```
Hay que mantener el aislamiento actual: si falla un (pais, empresa), no se cae el resto.

### 2.5 Fusión manual (`merge_human.py`, `manual_store.py`, `gui.py`)
- Agregar `pais` a la regla de matching: `pais + empresa + nombre_producto + atributos rellenos`.
- Las filas de `competencia_human.xlsx` y del `.db` que no traen `pais` se toman como `ecuador` (compatibilidad hacia atrás). Si se agrega la columna al `.db`, hacer la migración con `ALTER TABLE` y default `'ecuador'`.
- GUI: agregar un selector de país (o agrupar las tarjetas por país). El formulario manual pide `pais` como campo obligatorio y valida contra `PAIS_VALUES`.

### 2.6 Duplicados entre países
Un mismo PDF de Nicovita en Ecuador y en Honduras genera **dos filas legítimas** (una por país). No se deduplican, porque `pais` forma parte de la identidad. Lo que sí se evita es **descargar dos veces**: si `data/raw/nicovita/<archivo>.pdf` ya existe en la misma corrida, se reutiliza.

---

## 3. Fases (en orden, cada una con su criterio de "hecho")

### Fase 0 — Refactor sin cambios funcionales (solo Ecuador)
1. Agregar `pais` al esquema, crear `fuentes.py` y el CLI con `--pais` y `--empresa`.
2. Parametrizar `scrapers/nicovita.py` (hoy `LIST_URL` está fijo en `?pais=ecuador` y se priorizan las URLs `-ecuador`; hay que generalizarlo a `-{pais_slug}`) y `scrapers/aquaxcel.py` (`/productos/{pais_slug}/`).
3. Migrar la salida a `processed/ecuador/` y adaptar `merge_human`, `manual_store` y `gui`.

**Hecho cuando:** `pytest` pasa completo y el nuevo `master.csv` de Ecuador tiene **las mismas filas** que el actual (comparar ignorando `pais` y `fecha_extraccion`). Agregar un test que lo verifique.

### Fase 1 — Descubrimiento de fuentes (sin construir scrapers)
Por cada país y por cada empresa candidata de §1, confirmar en el sitio real:
- Si hay catálogo para ese país y cuál es la URL exacta.
- Formato: HTML estático, PDF con texto, PDF de imagen (OCR) o JS dinámico.
- Qué campos del esquema publica (proteína, calibre, presentación, empaque, etapa).
- Si existe un distribuidor local con datos técnicos (como Agrizon en Ecuador), sobre todo para BioMar y Cargill en Centroamérica.

Entregable: la tabla **"Fuentes por país"** en `MEMORY.md`, con columnas `pais | empresa | url | formato | campos_disponibles | decision (construir / parcial / descartar)`.

La tabla va en `PROGRESO_REGIONAL.md` (ver §7). Al terminar, se aplican los defaults de §6 y se continúa sin preguntar.

### Fase 2 — Reutilizar lo existente (bajo costo)
- `honduras/nicovita` y `mexico/nicovita`, con el mismo parser de PDF.
- `mexico/aquaxcel`, con el mismo parser HTML. Si la estructura del listado mexicano no coincide con los bloques "Portafolio {LÍNEA}", se aplica §5.1.

**Hecho cuando:** se validan al menos 3 productos reales por (pais, empresa) contra la ficha o página real. Anotar en `MEMORY.md` cuáles se validaron.

### Fase 3 — Empresas nuevas de México
Una por una, en este orden de prioridad (por participación de mercado): **Vimifos → Purina → Api-Aba → Azteca → Nutrimar**.
Para cada una: scraper + parser + fixture HTML/PDF en `tests/fixtures/` + test en `tests/test_{empresa}_parser.py`, siguiendo el mismo patrón que los tests actuales.
La profundidad de datos depende de lo que publique cada empresa. Si solo hay nombre, esa empresa queda en pipeline parcial y todo lo demás en `null` (mismo criterio que BioMar en `PLAN.md`).

### Fase 4 — Centroamérica sin catálogo propio (Nicaragua, Panamá, Cargill HN, BioMar CA)
Solo si en la Fase 1 apareció alguna fuente (distribuidor, ficha pública). Si no apareció ninguna, estas combinaciones quedan **documentadas como "sin fuente pública"** en `MEMORY.md`, y se cargan a mano por la GUI (vía `competencia_human`) con la información que traiga el equipo comercial. **No se scrapea nada que no exista.**

### Fase 5 (opcional, preguntar antes) — Registros oficiales
- **México / SENASICA:** existe un dataset abierto de productos acuícolas registrados (empresa, nombre, fórmula, número de registro). En datamx.io solo está la versión de 2019; hay que buscar la vigente en gob.mx/senasica. Si se usa, va como **fuente aparte** (`scrapers/senasica.py`) y se cruza con los productos ya scrapeados para completar nulos. Nunca crea filas sin revisión.
- **eaduana.com** (dictámenes de clasificación del SENAE de Ecuador): trae calibres y proteína declarados de marcas que también se venden en la región. Mismo criterio: es una fuente complementaria para llenar nulos y se registra en `fuente_url`.

---

## 4. Reglas de trabajo (además de las de `PLAN.md`)
- Usar `requests` + `BeautifulSoup`, igual que ahora. **No** agregar Playwright, porque rompe el empaquetado `.exe` (ver `PLAN.md` §4). Si un sitio necesita JS, se aplica §5.2.
- Ser cortés con los servidores: un `User-Agent` identificable, pausa entre requests y respeto a `robots.txt`.
- Si un sitio bloquea (403, captcha), el código **no resuelve ni falsifica** la verificación (sin proxies, sin suplantar el navegador). Procedimiento, en este orden:
  1. El pipeline marca la fuente `BLOQUEADO`, conserva el CSV anterior y escribe `data/bloqueos.md` con la página del captcha (`data/bloqueos/*.html`) para verla.
  2. **Páginas guardadas desde el navegador del usuario** (que sí puede entrar): Ctrl+S "solo HTML" en `data/manual/<empresa>/<pais>/`; el scraper las reconoce por su URL canónica (hoy implementado para Nicovita).
  3. Reducir el ritmo: pausas aleatorias solo en los dominios que ya mostraron captcha (`netutil.PACED_HOSTS`), caché de HTML y PDF, y no repetir corridas tras un bloqueo.
  4. Pedir a la empresa autorización o lista permitida para el acceso automatizado.
  5. Si nada funciona, la fuente queda `bloqueado` en la tabla y se carga a mano por la GUI.
- No borrar módulos viejos (mismo criterio que con `scrapers/biomar.py`).
- Actualizar `ScraperCompetencia.spec` si cambian los imports dinámicos (por ejemplo, el registro en `fuentes.py` con `importlib`). Hay que agregar los `hiddenimports`, o el `.exe` no va a encontrar los módulos.

## 5. Bloqueos (modo autónomo: NO detenerse, registrar y seguir)
El usuario no está mirando. Cuando aparece un bloqueo, **no se pregunta**: se anota en `PROGRESO_REGIONAL.md` → "Bloqueos" y se pasa al siguiente ítem.
1. El layout de otro país no coincide con lo mapeado para Ecuador → si el ajuste del parser es chico, se hace; si no, ese (pais, empresa) se marca `bloqueado`.
2. El sitio necesita JS/headless → se marca `sin_fuente_publica` (no se agrega Playwright: rompe el `.exe`). Si devuelve 403 o captcha → se aplica el procedimiento de §4 (páginas guardadas a mano / autorización) y, mientras no se resuelva, se marca `bloqueado`.
3. Hace falta una decisión de negocio → se aplica el default de §6.

**Única excepción que detiene todo:** si la Fase 0 no logra que Ecuador dé las mismas filas que antes, no se avanza a la Fase 2. Se deja el detalle en "Bloqueos" y se termina el loop.

## 6. Decisiones de negocio — defaults ya tomados (el usuario puede cambiarlos después)
- **Nicaragua y Panamá sin catálogo propio:** **no** se duplican filas de Honduras. Quedan para carga manual. En `MEMORY.md` se anota que Nicovita los atiende desde Honduras.
- **HAID y Agripac fuera de Ecuador:** solo se revisa en la Fase 1. No se construye nada.
- **Fase 5 (SENASICA / eaduana):** **no** se ejecuta. Solo se deja en `MEMORY.md` la URL vigente del dataset de SENASICA, si se encuentra.
- **ADM México:** si no tiene fuente pública, se descarta.

## 7. Ejecución autónoma y eficiencia de tokens

### 7.1 Archivo de estado: `PROGRESO_REGIONAL.md` (lo crea la primera iteración)
Es la **única memoria entre iteraciones** y tiene que ser corto: menos de 80 líneas. Formato:
```
## Checklist
- [x] F0.1 pais en schema + PAIS_VALUES
- [ ] F0.2 fuentes.py + CLI
...
- [ ] F2 honduras/nicovita  (validados: 0/3)
...
## Fuentes por país (tabla de Fase 1, 1 línea por pais/empresa)
## Bloqueos
## Última iteración: <qué se hizo en 1 línea>
```
`MEMORY.md` (~57 KB) **no se vuelve a leer completo**: se lee una sola vez en la primera iteración. Después solo se busca con `grep` la sección necesaria. Al final se le agrega un resumen.

### 7.2 Reglas para gastar pocos tokens
- Al empezar cada iteración: leer **solo** `PROGRESO_REGIONAL.md` y, cuando haga falta, el archivo concreto que se va a tocar. No releer `PLAN.md` ni este plan completo (buscar con `grep` la fase correspondiente).
- Nunca imprimir HTML ni texto de PDF completo en la consola. Guardarlo en `tests/fixtures/` o `data/raw/` e inspeccionarlo con `grep`, `head -c 2000` o un script corto que extraiga solo lo necesario.
- Tests: correr `pytest -q -x tests/test_<lo_tocado>.py` en cada cambio, y la suite completa (`pytest -q`) solo al cerrar cada fase.
- El pipeline se corre por (pais, empresa) con `--pais/--empresa`, nunca todo junto mientras se desarrolla.
- La validación se hace con un script que compara 3 filas contra la fuente y muestra solo las diferencias.
- No lanzar subagentes.
- Una iteración = un ítem del checklist. Al cerrar el ítem: actualizar `PROGRESO_REGIONAL.md` y hacer `git commit` (así si algo se rompe, se puede volver atrás).

### 7.3 Criterio de terminado (cuando se cumple, se termina el loop)
Se cumplen **todas** estas condiciones:
1. Fase 0 completa y Ecuador idéntico al de antes.
2. Cada (pais, empresa) de la tabla de Fase 1 está en uno de tres estados: `ok` (≥3 productos validados contra la fuente real), `parcial` (validado, con campos en `null` justificados) o `sin_fuente_publica`/`bloqueado` (con el motivo escrito).
3. `pytest -q` pasa completo.
4. `python src/pipeline.py` regenera `master.csv` sin errores, y la columna `pais` tiene al menos `ecuador`, `honduras` y `mexico`.
5. `MEMORY.md` tiene la sección "Expansión regional" con el resumen y `PROGRESO_REGIONAL.md` tiene un cierre que dice: qué quedó, qué falta y qué decisiones de §6 conviene revisar.

**Freno de seguridad:** si 3 iteraciones seguidas no completan ningún ítem del checklist, se anota el motivo en "Bloqueos" y se termina el loop.
