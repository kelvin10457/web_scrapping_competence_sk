# R10.1 — Validación

## Requisito → test
| REQ | Test | Estado |
|---|---|---|
| REQ-1 | `tests/test_ocr.py::test_req1_exe_usa_tesseract_empaquetado` | ✅ |
| REQ-2 | `tests/test_ocr.py::test_req2_sin_empaquetado_usa_instalacion_de_windows` | ✅ |
| REQ-3 | `tests/test_ocr.py::test_req3_sin_nada_queda_el_del_path` | ✅ |
| REQ-4 | `tests/test_ocr.py::test_req4_scrapers_no_repiten_rutas_de_tesseract` | ✅ |
| REQ-5 | `tests/test_ocr.py::test_req5_spec_empaqueta_tesseract_y_ocr` | ✅ |

## Validación con fuentes reales
No es una fase de scraping. Se corrieron las fuentes con OCR (Linux, Tesseract del PATH) y salen idénticas a las anteriores: El Pedregal 36 filas, HAID 16 (Nutrimar usa `haid_scraper.ocr_image`).

**Sin verificar:** la compilación del `.exe` (necesita Windows). Al compilar, revisar que una corrida de El Pedregal desde el `.exe`, en una PC sin Tesseract instalado, devuelva 36 filas.

## Colaboración
Hecho por Claude con el usuario presente (sin Codex).

## Resultado
`pytest -q`: 336 pasan.
