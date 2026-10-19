"""Scraper de Api-Aba / Acuacultura (Mexico): linea de camaron de
https://www.acuacultura.com.mx. WordPress con HTML estatico (verificado
2026-10-19; robots.txt permite todo). La pagina de la especie lista los
productos y cada uno tiene su propia pagina con el analisis garantizado."""
from __future__ import annotations

import re
import time

import requests

import netutil

BASE_URL = "https://www.acuacultura.com.mx"
SPECIES_URL = f"{BASE_URL}/productos-especies/camarones/"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; competence-scraper/1.0)"}
_PRODUCT_LINK_RE = re.compile(r'card-product__link"\s+href="(https://www\.acuacultura\.com\.mx/productos/[a-z0-9\-]+/)"')
PAUSE_SECONDS = 1.0


def fetch(url: str, session: requests.Session | None = None) -> str:
    s = session or requests
    r = netutil.get(s, url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.text


def discover_product_urls(species_html: str) -> list[str]:
    seen: list[str] = []
    for url in _PRODUCT_LINK_RE.findall(species_html):
        if url not in seen:
            seen.append(url)
    return seen


def scrape_all() -> list[dict]:
    """[{url, html}] de cada producto de camaron."""
    session = requests.Session()
    items = []
    for url in discover_product_urls(fetch(SPECIES_URL, session=session)):
        time.sleep(PAUSE_SECONDS)
        items.append({"url": url, "html": fetch(url, session=session)})
    return items
