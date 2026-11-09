# R10.1 — Tesseract dentro del .exe

> Roadmap: [R10.1](../../roadmap.md) · Estado: se marca solo en el roadmap

## Contexto
HAID (3 fichas imagen), Nutrimar (vía `haid_scraper.ocr_image`) y El Pedregal (todo su catálogo) usan OCR. Hoy el `.exe` necesita Tesseract instalado aparte en `C:\Program Files\Tesseract-OCR`; si falta, esas fuentes fallan. Decisión del usuario 2026-11-09: Tesseract va dentro del `.exe`.

## Requisitos
- **REQ-1:** Cuando corre el `.exe` y trae Tesseract empaquetado (`<_MEIPASS>/tesseract/tesseract.exe`), entonces `pytesseract` usa ese binario y `TESSDATA_PREFIX` apunta a `<_MEIPASS>/tesseract/tessdata`.
- **REQ-2:** Cuando no hay Tesseract empaquetado, se usa la primera instalación de Windows que exista (las mismas rutas de antes).
- **REQ-3:** Sin ninguna de las dos, queda `tesseract` del PATH (Linux/macOS, comportamiento de antes).
- **REQ-4:** La configuración vive en un solo módulo (`src/ocr.py`); HAID y El Pedregal la llaman en vez de repetir las rutas.
- **REQ-5:** `ScraperCompetencia.spec` copia `tesseract.exe`, sus DLL y `tessdata` (`spa`, `eng`, `osd`) a `tesseract/` dentro del `.exe`, y falla al compilar si no encuentra Tesseract o `spa.traineddata` (para no entregar un `.exe` sin OCR). Ruta: variable `TESSERACT_DIR` o `C:\Program Files\Tesseract-OCR`.

## Fuera de alcance
- Compilar el `.exe` (se hace en Windows; desde Linux no se puede).

## Restricciones de la constitución que más pesan acá
- OCR local, sin servicios pagos ni APIs.
