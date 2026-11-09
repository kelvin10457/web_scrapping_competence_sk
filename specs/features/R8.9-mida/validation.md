# R8.9 — Validación

## Requisito → test
| REQ | Test | Estado |
|---|---|---|
| REQ-1 | `tests/test_registros_mida.py::test_req1_nacional_una_fila_por_registro` | ✅ |
| REQ-2 | `tests/test_registros_mida.py::test_req2_pga_celdas_de_varias_lineas` | ✅ |
| REQ-3 | `test_req3_solo_camaron_explicito_o_curado`, `test_req3_filtro_descarta_premezclas_y_poliquetos` | ✅ |
| REQ-4 | `test_req4_vigencia_vencida_fuera_e_ilegible_vacia` | ✅ |
| REQ-5 | `test_req5_campos_tecnicos_vacios_y_fuente` | ✅ |
| REQ-6 | `test_req6_actualizar_mida_falla_sin_copia_y_senasica_sigue`, `test_req6_actualizar_usa_copia_de_mida_sin_red`, `test_req6_descarga_con_ua_de_navegador`, `test_req6_pdf_truncado_no_tumba_senasica_ni_pisa_la_copia` | ✅ |

## Validación contra la fuente real (≥3 registros)
PDF bajados de mida.gob.pa el 2026-11-09 (UA de navegador, HTTP 200) y comparados con `pdftotext -layout` (extracción independiente de pdfplumber).

| Registro | Campo | Fuente dice | CSV dice |
|---|---|---|---|
| RA-2278-25 (nacional) | producto / fabricante / vigencia | AQUANASA 25 · NUTRICIÓN ANIMAL, S.A. · 30 DE MAYO DE 2030. | AQUANASA 25 · NUTRICIÓN ANIMAL, S.A. · 2030-05-30 |
| RA-2447-23 (nacional) | producto / fabricante / vigencia | EXCELLENT CAMARÓN · AVÍCOLA GRECIA, S.A. · 10 DE ABRIL DE 2028. | EXCELLENT CAMARÓN · AVÍCOLA GRECIA, S.A. · 2028-04-10 |
| RA-2550-25 (PGA) | producto / fabricante / vigencia | MATEMAX · FARALLON / AQUACULTURE, (dos líneas) · 09 DE DICIEMBRE DE 2030 | MATEMAX · FARALLON AQUACULTURE, · 2030-12-09 |

## Conteo antes → después
`data/registros_oficiales.csv`: 162 registros (143 SENASICA + 19 eaduana) → 167 (+5 MIDA, todos `sin_match`: Panamá no tiene empresas en el master). Master y Excel de Power BI sin cambios (los registros no crean filas). PDF nacional: 121 registros leídos (1 sin vigencia legible, queda vacía); PGA: 57.

## Limitaciones
- PGA no tiene bordes: las celdas van alineadas abajo (la última línea en la fila del `RA-…`). Algunas celdas vienen truncadas en el propio PDF (p. ej. `FERTILIZANTES` sin `SUPERIORES, S.A.`); se dejan como están.
- AQUANASA entra por el cruce curado `MIDA_CAMARON_CURADO` (roadmap R8.9); el ministerio no dice la especie. Su número (25/30/35) no se toma como proteína.

## Colaboración
- **Claude:** spec, tests, implementación, validación.
- **Codex (revisión de solo lectura, gpt-6.1-sol):** 4 hallazgos, **todos aplicados**:
  1. *P2:* asignar cada línea al registro más cercano mezclaba celdas de 3 líneas (RA-2502/2503). Se probó una partición centrada y no servía. Al mirar la geometría se vio que las celdas van alineadas abajo; la regla final es "primer registro a la altura de la línea o más abajo". Tests con RA-2497, 2502, 2503 y 2548.
  2. *P2:* un PDF truncado que empieza con `%PDF` hacía caer SENASICA/eaduana. Ahora el PDF nuevo se baja a `.nuevo.pdf`, se parsea y recién entonces reemplaza la copia. Cualquier error de lectura se avisa y se omite.
  3. *P2:* el filtro dejaba pasar `PREMEZCLA/POLIQUETOS PARA CAMARON`. Ahora exige "ALIMENTO" en la clasificación oficial y excluye premezclas, aditivos, poliquetos, vitaminas y materia prima.
  4. *P3:* el test del UA solo miraba una constante y el `AssertionError` de "sin red" se tragaba. Ahora se verifican las cabeceras enviadas y que no haya llamadas cuando hay caché.
- **Descartado:** nada.
- Codex no pudo implementar R7.6 en su worktree: su entorno lo monta como solo lectura y no tiene DNS. R7.6 pasa a Claude.

## Resultado
`pytest -q`: 307 pasan · commit: `R8.9`
