"""Scraper de NasaFeed (Nutricion Animal S.A., Panama), R8.10: ficha PDF de la
Linea Premium de Aquanasa. nasafeed.com no responde (timeout 2026-11-09); se
intenta primero y, si falla la conexion, se usa la copia de Wayback (decision
del usuario 2026-11-09). El sufijo `id_` devuelve el archivo original."""
from __future__ import annotations

import requests

import netutil

PDF_URL = "https://nasafeed.com/files/Ficha-Tecnica-Linea-Premium-Aquanasa.pdf"
WAYBACK_URL = ("https://web.archive.org/web/20240830070946id_/"
               "https://nasafeed.com/files/Ficha-Tecnica-Linea-Premium-Aquanasa.pdf")
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                         "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"}


class NoEsPDF(ValueError):
    pass


def _pdf(session, url: str, **kw) -> bytes:
    r = netutil.get(session, url, headers=HEADERS, **kw)
    r.raise_for_status()
    if not r.content.startswith(b"%PDF"):
        raise NoEsPDF(url)  # p. ej. un 200 con HTML (revision Codex)
    return r.content


def descargar() -> tuple[str, bytes]:
    """(url usada, bytes del PDF). Cualquier falla del sitio original (red,
    HTTP, captcha, respuesta que no es PDF) pasa a la copia de Wayback."""
    session = requests.Session()
    try:
        return PDF_URL, _pdf(session, PDF_URL, timeout=20, retries=1)
    except (requests.RequestException, netutil.BlockedError, NoEsPDF):
        return WAYBACK_URL, _pdf(session, WAYBACK_URL, timeout=60)
