# R8.10 — NasaFeed Aquanasa (Panamá)

> Roadmap: [R8.10](../../roadmap.md) · Estado: se marca solo en el roadmap

## Contexto
Nutrición Animal S.A. (NasaFeed, Chiriquí) publica la ficha PDF "Línea Premium" de Aquanasa. `nasafeed.com` no responde (timeout el 2026-11-09, también en R7.4). Hay una copia en Wayback (2024-08-30) y el usuario aprobó usarla (2026-11-09). La ficha da 3 proteínas (25/30/35 %) y 2 diámetros (1.4 y 2.4 mm) sin decir qué diámetro corresponde a cada proteína.

## Requisitos
- **REQ-1:** 3 filas, una por proteína: `AQUANASA 25`, `AQUANASA 30` y `AQUANASA 35` (nombre del registro MIDA, para que el cruce coincida; decisión 2026-11-09), con `empresa = NasaFeed`, `proteina_pct` de la fila "Proteína Cruda (mínima)" y `tamano_pellet_mm` vacío (decisión del usuario).
- **REQ-2:** `empaque_kg = 45.36` (sale de "100 lbs (45.36 Kg)"). `tipo_presentacion = Pellet` ("Alimento peletizado"). Etapas de "desde post larva hasta la cosecha": post_larva, precria, post_transferencia y engorde.
- **REQ-3:** El scraper intenta primero el sitio original y, si falla la conexión, baja la copia de Wayback (`id_`, el archivo sin la barra de Wayback). `fuente_url` es la URL que se usó realmente.
- **REQ-4:** `('panama', 'nasafeed')` está registrado y sus módulos están en `ScraperCompetencia.spec`.

## Fuera de alcance
- Repartir 1.4/2.4 mm entre las proteínas.
