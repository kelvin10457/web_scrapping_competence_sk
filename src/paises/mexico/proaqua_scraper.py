"""Scraper de ProAqua (distribuidor, Mexico): proaqua.mx/camaron/ (BigCommerce).
Verificado 2026-11-09 (R7.9): 3 paginas de listado (?page=N) y una ficha por
producto. Solo se bajan las fichas de alimentos formulados (filtro del parser)."""
from __future__ import annotations

import re

import requests

import netutil
from paises.mexico import proaqua_parser

LISTADO_URL = "https://proaqua.mx/camaron/"
MAX_PAGINAS = 10
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                         "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"}


def _get(url: str, session) -> requests.Response:
    r = netutil.get(session, url, headers=HEADERS, timeout=60)
    r.raise_for_status()
    return r


def paginas(html: str) -> set[int]:
    return {int(n) for n in re.findall(r"[?&]page=(\d+)", html)}


def scrape_all() -> list[dict]:
    """[{url, html}] por ficha de alimento formulado."""
    session = requests.Session()
    primera = _get(LISTADO_URL, session).text
    htmls = [primera] + [_get(f"{LISTADO_URL}?page={n}", session).text
                         for n in sorted(paginas(primera)) if 1 < n <= MAX_PAGINAS]
    productos = dict(p for h in htmls for p in proaqua_parser.productos_de_listado(h))
    return [{"url": url, "html": _get(url, session).text} for url in productos]
