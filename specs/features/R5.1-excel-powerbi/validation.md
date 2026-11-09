# R5.1 + R5.2 — Validación

## Tests
- `pytest -q -x tests/test_powerbi.py` → 10 passed (contrato de 16 columnas, tipos de celda, vacíos, escritura por pais/empresa, filas humanas).
- Suite completa: pendiente de correr al cerrar (Codex está editando `src/paises/mexico/vimifos_parser.py`).

## Pipeline (datos reales)
Regenerado desde `data/master.csv` + `data/competencia_human.xlsx` con `powerbi.escribir_todo`. 12 archivos, todos con las mismas 16 columnas en el mismo orden:

| Archivo | Filas |
|---|---|
| ecuador/Agripac.xlsx | 38 |
| ecuador/BioMar.xlsx | 17 |
| ecuador/Cargill.xlsx | 37 |
| ecuador/HAID.xlsx | 17 (16 + 1 humana) |
| ecuador/Nicovita.xlsx | 61 (57 + 4 humanas) |
| honduras/Nicovita.xlsx | 35 |
| mexico/Api-Aba.xlsx | 3 |
| mexico/Cargill.xlsx | 14 |
| mexico/Nicovita.xlsx | 26 |
| mexico/Nutrimar.xlsx | 6 |
| mexico/Vimifos.xlsx | 21 |
| mexico/Zeigler.xlsx | 13 |

## Validación contra la fuente
R5.1 no scrapea: toma el master ya validado en sus fases de parser. Sin fuente nueva que validar.

## Decisiones
- Filas humanas sin `pais` → ecuador (regla existente de `merge_human`). Ver `specs/revision_pendiente.md`.
- Las filas humanas se agregan tal cual; no se deduplican contra el master (ver `revision_pendiente.md`).
