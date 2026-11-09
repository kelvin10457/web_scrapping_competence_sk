"""Configuracion de Tesseract para el OCR local (R10.1).

Orden: 1) el Tesseract empaquetado dentro del .exe (`<_MEIPASS>/tesseract/`,
lo copia ScraperCompetencia.spec), 2) una instalacion de Windows, 3) el
`tesseract` del PATH (Linux/macOS)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytesseract

CANDIDATOS_WINDOWS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    str(Path.home() / "AppData/Local/Programs/Tesseract-OCR/tesseract.exe"),
]

_SIN_ARG = object()


def configurar(meipass=_SIN_ARG, candidatos: list[str] | None = None, environ=None) -> str:
    """Deja `pytesseract` apuntando al binario elegido y lo devuelve."""
    if meipass is _SIN_ARG:
        meipass = getattr(sys, "_MEIPASS", None)
    candidatos = CANDIDATOS_WINDOWS if candidatos is None else candidatos
    environ = os.environ if environ is None else environ
    if meipass:
        empaquetado = Path(meipass) / "tesseract" / "tesseract.exe"
        if empaquetado.exists():
            pytesseract.pytesseract.tesseract_cmd = str(empaquetado)
            environ["TESSDATA_PREFIX"] = str(empaquetado.parent / "tessdata")
            return str(empaquetado)
    for candidato in candidatos:
        if Path(candidato).exists():
            pytesseract.pytesseract.tesseract_cmd = candidato
            return candidato
    return pytesseract.pytesseract.tesseract_cmd
