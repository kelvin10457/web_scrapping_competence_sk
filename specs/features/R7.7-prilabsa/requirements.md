# R7.7 — Prilabsa (Ecuador, distribuidor): catálogo PDF

> Roadmap: [R7.7](../../roadmap.md) · Estado: se marca solo en el roadmap

## Contexto
Prilabsa distribuye en Ecuador alimentos de laboratorio (Hatchery) de Zeigler, Mackay Marine y Higashimaru. Su catálogo `CATALOGO PRODUCTOS JULIO PRILABSA.pdf` (72 págs.) tiene una ficha por página en la sección "Alimentos" del índice: Zeigler págs. 5–15, Mackay 16–21 e Higashimaru 22–23. Cada ficha trae análisis garantizado, presentación y, en la mayoría, una tabla de tamaños en micras. En Ecuador no hay ninguna de estas marcas en el master. Zeigler solo está en México, vía Nutrimar, así que en Ecuador **no está cubierto** y se incluye.

## Requisitos
- **REQ-1:** La empresa de cada ficha sale del índice del catálogo (rango de páginas por fabricante), mediante el número impreso en la página: `Zeigler`, `Mackay Marine`, `Higashimaru`. Se leen las 19 fichas de alimentos; nada fuera de esa sección.
- **REQ-2:** Una fila por tamaño publicado: la etiqueta encima de cada "MICRAS" o, en Higashimaru, `#N a-b micras`. Se pasa a mm (`<50` → `<0.05`, `50 - 200` → `0.05-0.2`). Una ficha sin tabla de tamaños da una fila con tamaño vacío.
- **REQ-3:** Proteína: si la ficha tiene un único valor de "Proteína Cruda (mínima)", se toma. Si publica dos distintos (peso seco/líquido, dos productos en una ficha) o un rango, queda vacía.
- **REQ-4:** Empaque: los pesos que acompañan a un envase (latas, baldes, fundas, sacos, envases, bolsas), en kg y separados por coma si hay varios (precedente Nicovita Origin). La dosis (`3,5 kg / día`, `8g × 4-6`) no cuenta.
- **REQ-5:** `tipo_presentacion` sale del paréntesis del título o de la palabra MICROPARTICULADO de la ficha, normalizado con `schema.normalize_presentacion`. Cistos de artemia → `Quistes de artemia`. Sin palabra explícita, vacío. Etapas: `detectar_etapas` sobre el texto de la ficha.
- **REQ-6:** Un tamaño `<X` no inventa un mínimo: `schema.parse_particula_range('<0.05')` → `(None, 0.05)`.
- **REQ-7:** `('ecuador', 'prilabsa')` está registrado y activo, y sus módulos están en `ScraperCompetencia.spec`. El scraper baja el PDF con UA de navegador y caché en `data/raw/prilabsa/`.

## Fuera de alcance
- Probióticos, congelados, aditivos y químicos del catálogo.
- Etapa por tamaño (se usa la etapa de la ficha completa, como El Pedregal).

## Restricciones de la constitución que más pesan acá
Vacío antes que inferir; normalizar con `schema.py`.
