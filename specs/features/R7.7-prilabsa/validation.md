# R7.7 — Validación

## Requisito → test
| REQ | Test | Estado |
|---|---|---|
| REQ-1 | `tests/test_prilabsa_parser.py::test_empresa_por_indice_y_19_fichas` | ✅ |
| REQ-2 | `test_una_fila_por_tamano_en_mm` | ✅ |
| REQ-3 | `test_proteina_unica_o_vacia` | ✅ |
| REQ-4 | `test_empaque_de_envases_sin_dosis` | ✅ |
| REQ-5 | `test_tipo_y_etapas` | ✅ |
| REQ-6 | `test_tamano_menor_que_no_inventa_minimo` | ✅ |
| REQ-7 | `test_registrada_y_scraper_con_ua` | ✅ |

## Validación contra la fuente real (≥3 productos)
Corrida real `pipeline.py --pais ecuador --empresa prilabsa` (2026-11-09): 48 SKU. Comparado con `pdftotext -layout` del PDF bajado (extracción independiente de pdfplumber).

| Producto | Campo | Fuente dice (pág.) | CSV dice |
|---|---|---|---|
| Z PRO (Zeigler) | proteína / tamaños / empaque | p. 7: "(mínima) 44%"; 150, 250, 350 MICRAS; "150: Latas … 500 gr" y "250, 350: Fundas … 4kg" | 44 · 0.15/0.25/0.35 · 0.5 / 4 / 4 (envase por tamaño) |
| CISTOS DE ARTEMIA (Mackay) | proteína / empaque / tipo | p. 16: "(mínima) 54%"; "Latas de 454g y baldes de 7kg" | 54 · `0.454,7` · Quistes de artemia |
| P. VANNAMEI (Higashimaru) | proteína / tamaños / empaque | p. 22: "(mínima) 52%"; "#0 30-50, #1 80-130, #2 200-300 micras"; "Fundas de 1kg" (la dosis 8g×4-6 no cuenta) | 52 · 0.03-0.05/0.08-0.13/0.2-0.3 · 1 |

## Conteo antes → después
Ecuador: +48 filas en 3 empresas nuevas (`Zeigler` 28, `Mackay Marine` 15, `Higashimaru` 5) y 3 Excel nuevos en `data/powerbi/ecuador/`. `etapa_skt`: Hatchery 39, Nursery 7, vacío 2. Proteína vacía en 10 filas (EZ Artemia, EZ Artemia Ultra, EZ Larva, Espirulina, ZM Feed; ver decisiones). El baseline de Ecuador se actualizó; antes se comprobó que las 165 filas previas siguen idénticas.

## Decisiones (pendientes de confirmar, en `decisiones.md`)
- Zeigler se incluye en Ecuador; `empresa` = fabricante.
- Proteína vacía si la ficha publica dos valores o un rango.
- `<50 µm` → `<0.05`, con `particula_min_mm` vacío (`schema.parse_particula_range`).
- Etapas de la ficha completa en todas sus filas (como El Pedregal). Empaque de la ficha en todas sus filas, salvo que la ficha diga qué envase lleva cada tamaño (Z PRO). Espirulina: `0.5,1` en sus dos tamaños, porque la ficha no dice cuál es la microfina.

## Colaboración
- **Claude:** spec, tests, implementación y validación. Codex no puede escribir ni usar la red en su entorno.
- **Codex (revisión de solo lectura):** 3 hallazgos:
  1. *Media, aplicado:* Z PRO publicaba `0.5,4` en todos los tamaños, pero la ficha dice "150: Latas 500 gr" y "250, 350: Fundas 4kg". Ahora el envase va por tamaño cuando la ficha lo dice (`_envase_por_tamano`). Test nuevo.
  2. *Media, aplicado en parte:* Espirulina perdía sus tamaños (van bajo "Tamaños": "8 a 10 micras", "20 micras"). Ahora sale una fila por tamaño (0.008-0.01 y 0.02). **Descartado:** asignar 500 g a uno y 1 kg al otro. La ficha dice "Microfina en latas de 500g y Regular en funda de 1kg", pero no qué tamaño es la microfina; ambas quedan con `0.5,1` (vacío antes que inferir).
  3. *Media, aplicado:* en Shrimp Meal, el encabezado de tabla "TAMAÑO DE PARTÍCULAS Y ESTADIO LARVAL" marcaba `etapa_larva`. Se quita ese encabezado antes de `detectar_etapas`: Shrimp Meal pasa de Hatchery a Nursery (post_larva + precría, "DIETA PARA RACEWAYS Y PRE-CRÍA"). Test nuevo.

## Resultado
`pytest -q`: 325 pasan · commit: `R7.7`
