"""Scraper de Aquaxcel (Cargill Ecuador). No existen fichas tecnicas por
producto ni paginas de producto individuales (confirmado via sitemap.xml en
MEMORY.md), pero la pagina de listado si publica composicion nutricional y
datos fisicos por SKU en bloques "Portafolio {LINEA}" (ver
src/parsers/aquaxcel.py) -- HTML estatico, sin JS necesario.
"""
from __future__ import annotations

import requests

LISTING_URL_TEMPLATE = "https://aquaxcel.com/productos/{pais_slug}/"
LISTING_URL = LISTING_URL_TEMPLATE.format(pais_slug="ecuador")
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; competence-scraper/1.0)"}


def fetch_listing(session: requests.Session | None = None, pais_slug: str = "ecuador") -> str:
    s = session or requests
    r = s.get(LISTING_URL_TEMPLATE.format(pais_slug=pais_slug), headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.text


def scrape_all(pais_slug: str = "ecuador") -> str:
    """Contrato comun de fuentes.py: devuelve el HTML del listado del pais."""
    return fetch_listing(pais_slug=pais_slug)
