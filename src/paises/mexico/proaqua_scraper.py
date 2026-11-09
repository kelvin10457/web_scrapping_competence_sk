"""Scraper de ProAqua (distribuidor, Mexico): proaqua.mx/camaron/ (BigCommerce).
Verificado 2026-11-09 (R7.9): 3 paginas de listado (?page=N) y una ficha por
producto. R11.3 agrega las cinco microalgas Reed para camarón; ambos listados
se filtran antes de descargar las fichas."""
from __future__ import annotations

import re

import requests

import netutil
from paises.mexico import proaqua_parser

LISTADO_URL = "https://proaqua.mx/camaron/"
REED_URL = "https://proaqua.mx/reed-mariculture/"
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
    """[{url, html, reed}] por ficha de formulado o microalga para camarón."""
    session = requests.Session()
    primera = _get(LISTADO_URL, session).text
    htmls = [primera] + [_get(f"{LISTADO_URL}?page={n}", session).text
                         for n in sorted(paginas(primera)) if 1 < n <= MAX_PAGINAS]
    productos = dict(p for h in htmls for p in proaqua_parser.productos_de_listado(h))
    reed = dict(proaqua_parser.productos_reed_de_listado(_get(REED_URL, session).text))
    return [{"url": url, "html": _get(url, session).text, "reed": url in reed}
            for url in dict.fromkeys([*productos, *reed])]
