"""Descarga del catalogo de Prilabsa (verificado 2026-11-09: 200, PDF con
texto, 72 paginas). Cache en data/raw/prilabsa/ de MAX_DIAS_CACHE."""
from __future__ import annotations

import time
from pathlib import Path

import requests

import netutil

PDF_URL = "https://prilabsa.com/assets/pdfs/CATALOGO%20PRODUCTOS%20JULIO%20PRILABSA.pdf"
RAW_DIR = netutil.DATA_DIR / "raw" / "prilabsa"
MAX_DIAS_CACHE = 30
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                         "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"}


def descargar(max_dias: int = MAX_DIAS_CACHE, session=None) -> Path:
    destino = RAW_DIR / "catalogo.pdf"
    if destino.exists() and time.time() - destino.stat().st_mtime < max_dias * 86400:
        return destino
    r = netutil.get(session or requests.Session(), PDF_URL, headers=HEADERS, timeout=180)
    r.raise_for_status()
    if not r.content.startswith(b"%PDF"):
        raise ValueError("Prilabsa: la respuesta no es un PDF")
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(r.content)
    return destino
