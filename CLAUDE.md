# CLAUDE.md

Scraping de competencia de alimento para camarón (5 países). El resultado son Excel por país y empresa para Power BI. Se trabaja con **spec-driven development**.

## La constitución (`specs/`)
- `specs/mission.md`: para qué existe y principios innegociables
- `specs/tech-stack.md`: stack, patrones y **esquema** (columnas del Excel de Power BI)
- `specs/roadmap.md`: orden de implementación en fases chicas. **Es el único lugar donde se marca el estado**
- `specs/decisiones.md`: decisiones del usuario con fecha
- `README.md`: mapa del código, comandos y qué hacer ante un captcha. `src/paises/<pais>/README.md`: fuentes de cada país

`docs/historico/` está congelado: solo se consulta para buscar evidencia puntual con `grep`, y no se edita.

## Flujo de trabajo
1. Se trabaja **la siguiente fase pendiente del roadmap**, una por vez. Si hace falta algo que no está en el roadmap, se propone primero.
2. Se crea `specs/features/<ID>-<slug>/` copiando `_plantilla/`. Si un requisito no está claro, se pregunta con AskUserQuestion **antes** de escribir código.
3. Primero los tests (uno por REQ, con fixture real), después la implementación.
4. Si la realidad contradice la spec, **se corrige la spec primero** y se avisa.
5. Cierre: `validation.md` → `pytest -q` en verde → `[x]` en el roadmap → commit `<ID>: <resumen>`.
6. Si cambian el esquema o los patrones, se actualiza `tech-stack.md` en el mismo commit. Las decisiones del usuario van a `specs/decisiones.md`.

## Reglas que no se rompen
- Vacío antes que inventar o inferir un valor. Los conflictos se resuelven con `schema.resolver_campo` y quedan en `_conflictos.csv`.
- Normalizar en el parser, con funciones de `schema.py`. Nunca con un parche al exportar.
- Nada de LLM ni APIs pagas. Nada de Playwright ni Selenium.
- Si un sitio bloquea, no se evade (ver `README.md` § Bloqueos).
- Validar ≥3 productos contra la fuente real antes de cerrar una fase de scraping.

## Uso inteligente del plan (Pro de $20, Opus 5.5 en effort medio)
El límite real es el uso por ventana de tiempo, y cada mensaje vuelve a enviar todo el contexto acumulado. Por eso:
- **Una fase por conversación.** Al cerrarla (commit), conviene que el usuario haga `/clear` antes de la siguiente. Si una fase se alarga, `/compact`.
- **Leer lo justo.** Primero `Grep`, después `Read` con `offset`/`limit` sobre la parte relevante. No releer archivos que ya están en el contexto.
- **Nunca volcar HTML ni texto de PDF a la consola.** Guardar en `tests/fixtures/` o `data/raw/` e inspeccionar con `grep` o `head -c`.
- **Correr solo lo tocado:** `pytest -q -x tests/test_<x>.py` y `pipeline.py --pais <p> --empresa <e>`. La suite completa y el pipeline completo, solo al cerrar.
- **Sin subagentes** salvo pedido explícito: cada uno arranca de cero y repite la lectura.
- **Elegir el modelo según la tarea:** las fases mecánicas (renombres, mover columnas) pueden ir con Sonnet (`/model`). Opus se reserva para specs, parsers difíciles y bugs.
- Respuestas cortas: lo que cambió, el resultado de los tests y qué sigue.

Python del proyecto:
- Windows: `.venv/Scripts/python`
- Linux/macOS: `.venv/bin/python`
