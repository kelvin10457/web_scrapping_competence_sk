"""Scraper de Vimifos (Mexico): lineas de camaron de https://vimifos.com.
Sitio HTML estatico (verificado 2026-10-19; robots.txt sin restricciones).
La categoria /categoria/camaron enlaza cada linea (/producto/<slug>) y cada
pagina trae una tabla con presentacion, % proteina, tamano de particula."""
from __future__ import annotations

import re

import requests

import netutil

BASE_URL = "https://vimifos.com"
CATEGORY_URL = f"{BASE_URL}/categoria/camaron"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; competence-scraper/1.0)"}
_PRODUCT_LINK_RE = re.compile(r'href="(/producto/[a-z0-9\-]+)"')


def fetch(url: str, session: requests.Session | None = None) -> str:
    s = session or requests
    r = netutil.get(s, url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.text


def discover_product_urls(category_html: str) -> list[str]:
    paths = sorted(set(_PRODUCT_LINK_RE.findall(category_html)))
    return [BASE_URL + p for p in paths]


def scrape_all() -> list[dict]:
    """[{url, html}] de cada linea de camaron."""
    session = requests.Session()
    urls = discover_product_urls(fetch(CATEGORY_URL, session=session))
    items = []
    for url in urls:
        items.append({"url": url, "html": fetch(url, session=session)})
    return items
