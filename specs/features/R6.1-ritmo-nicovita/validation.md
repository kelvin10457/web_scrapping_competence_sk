# R6.1 + R6.2 — Validación

## Requisito → test
| REQ | Test | Estado |
|---|---|---|
| REQ-1 | `tests/test_netutil.py::test_pausas_cortas_y_larga_cada_6_a_10`, `test_pagina_en_cache_no_pausa`, `tests/test_pipeline.py::test_netutil_pause_schedule_is_random_and_long_every_6_to_10` | ✅ |
| REQ-2 | Medición real (abajo) | ✅ |
| REQ-3 | `test_captcha_frena_solo_ese_dominio` | ✅ |
| REQ-4 | `test_tras_dos_captchas_no_vuelve_a_la_red` | ✅ |
| REQ-5 | `test_reset_limpia_ritmo_lento_y_contador` | ✅ |

## Validación contra la fuente real
Corrida en frío de Nicovita Honduras (2026-11-09) con cachés de HTML y PDF en un directorio temporal (script en el scratchpad; `data/` no se tocó):

| Corrida | Productos | Tiempo | Bloqueos |
|---|---|---|---|
| Frío | 35 | **61 s** (presupuesto ≤180 s) | ninguno |
| Con caché | 35 | **1 s** | ninguno |
| `pipeline.py --pais honduras --empresa nicovita` (caché del día) | 35 | 2.8 s | ninguno |

Antes de R6.1, la pausa media era de ~3 s más 15–40 s cada 3–6 consultas. Con ~35 consultas, solo en pausas eran ~4–5 min.

## Colaboración
- **Claude:** spec, tests, implementación y medición.
- **Codex (revisión de solo lectura):** 1 hallazgo, **aplicado**. *P2:* después de 2 captchas, el `BlockedError` sin red llevaba `saved=None` y el pipeline pedía abrir un archivo `None`. Ahora reusa la URL y la página guardada del último captcha de ese dominio (test ampliado). Codex no encontró problemas con `www.`, subdominios, estado global ni pérdida de copias guardadas.
- **Descartado:** nada.

## Resultado
`pytest -q`: 331 pasan · commit: `R6.1+R6.2`
