# R6.1 + R6.2 — Ritmo de Nicovita: presupuesto de tiempo y captcha por dominio

> Roadmap: [R6.1, R6.2](../../roadmap.md) · Estado: se marca solo en el roadmap

## Contexto
`netutil.pause()` espera de 1.5 a 7 s (moda 2.5) antes de cada consulta nueva a `nicovita.com`/`agrizon.com`, más una pausa de 15 a 40 s cada 3–6 consultas. Con ~60 consultas por país, eso supera el presupuesto acordado (≤3 min por país en frío). Ante un captcha, `get` lanza `BlockedError` y `nicovita_scraper.fetch` usa la copia guardada si existe. Pero las consultas siguientes al mismo dominio no se frenan y cada una vuelve a chocar con el captcha.

## Requisitos
- **REQ-1 (R6.1):** Pausas más cortas para `PACED_HOSTS`: corta `triangular(0.5, 2.5, 1.0)` s y larga `uniform(5, 12)` s cada 6–10 consultas **nuevas**. Una página que sale de la caché no espera ni suma al contador.
- **REQ-2 (R6.1):** Una corrida en frío (caché de HTML y PDF vacía) de Nicovita en un país tarda ≤3 min, y con caché, segundos. Se mide y se anota en `validation.md`.
- **REQ-3 (R6.2):** Después de un captcha, **solo ese dominio** pasa a ritmo lento (corta `uniform(6, 15)` s). Los demás dominios no cambian.
- **REQ-4 (R6.2):** Después de `MAX_BLOQUEOS_POR_HOST` (2) captchas del mismo dominio en una corrida, `get` ya no consulta ese dominio: lanza `BlockedError` sin ir a la red. El scraper usa la copia guardada si existe y, si no, el pipeline conserva el CSV anterior y sigue con las demás empresas. Sin esperas indefinidas.
- **REQ-5:** `reset_blocked()` (inicio de corrida) limpia también el ritmo lento y el contador de bloqueos.

## Fuera de alcance
- Resolver captchas o evadir el bot manager de Nicovita (perfdrive).
- Cambiar el TTL de la caché (24 h).

## Restricciones de la constitución que más pesan acá
Sin Playwright/Selenium ni servicios pagos; no reintentar en bucle ante un bloqueo.
