## Checklist
- [x] F0.1 pais en schema + PAIS_VALUES (baseline Ecuador en tests/fixtures/master_ecuador_baseline.csv)
- [ ] F0.2 fuentes.py + CLI --pais/--empresa + build_master recorre processed/*/*.csv
- [ ] F0.3 parametrizar scrapers nicovita (pais_slug) y aquaxcel (pais_slug)
- [ ] F0.4 migrar salida a processed/ecuador/; adaptar merge_human, manual_store, gui; test identidad Ecuador
- [ ] F0.5 regenerar Ecuador con pipeline y verificar mismas filas (si falla: STOP, ver §5)
- [ ] F1 descubrimiento de fuentes (tabla abajo)
- [ ] F2 honduras/nicovita  (validados: 0/3)
- [ ] F2 mexico/nicovita  (validados: 0/3)
- [ ] F2 mexico/aquaxcel  (validados: 0/3)
- [ ] F3 mexico/vimifos
- [ ] F3 mexico/purina
- [ ] F3 mexico/apiaba
- [ ] F3 mexico/azteca
- [ ] F3 mexico/nutrimar
- [ ] F4 Centroamerica sin fuente: documentar en MEMORY.md
- [ ] F5 cierre: pytest -q, pipeline.py, MEMORY.md "Expansión regional", cierre aquí

## Fuentes por país
(pais | empresa | url | formato | campos | decision)

## Bloqueos
(ninguno)

## Última iteración: F0.1 pais en schema; merge_human asume ecuador si falta la columna (145+1 tests ok).
