# R7.6 — AQUATEC (México) vía nutrimentos.com.mx

> Roadmap: [R7.6](../../roadmap.md) · Estado: se marca solo en el roadmap

## Contexto
AQUATEC (Nueva Tecnología en Alimentación, 15 registros en SENASICA) no tiene catálogo propio. Su distribuidor Nutrimentos de la Cruz publica una sola página (`nutrimentos.com.mx/acuicultura_1`) con dos partes. Arriba hay 3 fichas completas (Línea Performance, HD y Estándar): análisis garantizado, indicaciones y saco. Abajo hay 3 columnas por línea con 10 variantes (nombre con % y mm), cuyo texto es la plantilla del editor web ("Describa sus productos…"). El certificado SSL del dominio es inválido; el usuario decidió aceptarlo (2026-11-09).

## Requisitos
- **REQ-1:** Cuando se parsea la página, entonces sale una fila por SKU `(línea, nombre)`: las 10 variantes de las columnas, más las fichas que no figuran en su columna (Estándar 40% migaja). Son 11 filas, sin duplicados. `nombre_producto` = nombre publicado + `(Línea X)`, porque el mismo nombre aparece en varias líneas.
- **REQ-2:** Una SKU con ficha toma la proteína del análisis garantizado (contrastada con el % del nombre mediante `schema.reglas_titulo_vs_analisis`) y el empaque del saco (`25`).
- **REQ-3:** Una variante sin ficha (solo texto de plantilla) **no hereda** nada de otra: empaque y etapas vacíos. Solo lleva lo que dice su propio nombre: proteína del `NN%` y tamaño del `N.N mm`.
- **REQ-4:** El tamaño sale del `mm` del nombre (`PELLET 1.8 mm` → `1.8`; `MIGAJA` sin mm → vacío). `tipo_presentacion` = `Pellet` si el nombre dice PELLET; migaja queda vacía, porque no tiene grafía oficial (igual que El Pedregal).
- **REQ-5:** El scraper usa `verify=False` solo para `nutrimentos.com.mx` y un User-Agent de navegador.
- **REQ-6:** `('mexico', 'aquatec')` está registrado y activo en `fuentes`, y sus módulos están en `ScraperCompetencia.spec`.

## Fuera de alcance
- Otros productos de Nutrimentos (NUTRIAQUA, BBIG CAMARON: se nombran sin ficha).
- Inferir etapas de "juveniles hasta 5 g" si `detectar_etapas` no las reconoce.

## Restricciones de la constitución que más pesan acá
Vacío antes que inferir; sin heredar campos entre variantes (decisión del usuario); normalizar con `schema.py`.
