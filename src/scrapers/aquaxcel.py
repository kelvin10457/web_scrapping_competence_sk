"""Scraper de Aquaxcel (Cargill Ecuador). No existen fichas tecnicas por
producto ni paginas de producto individuales (confirmado via sitemap.xml en
MEMORY.md), pero la pagina de listado si publica composicion nutricional y
datos fisicos por SKU en bloques "Portafolio {LINEA}" (ver
src/parsers/aquaxcel.py) -- HTML estatico, sin JS necesario.
"""
from __future__ import annotations

import requests

LISTING_URL = "https://aquaxcel.com/productos/ecuador/"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; competence-scraper/1.0)"}


def fetch_listing(session: requests.Session | None = None) -> str:
    s = session or requests
    r = s.get(LISTING_URL, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.text
