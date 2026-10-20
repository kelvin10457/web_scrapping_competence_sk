"""Scraper de BioMar Ecuador: pipeline PARCIAL por diseno (PLAN.md § 0/§ 2).
No hay fichas tecnicas ni composicion nutricional publicada -- la pagina de
producto termina en un formulario de contacto de ventas (MEMORY.md). Solo
se extrae identificacion: empresa, nombre_producto, etapa.
"""
from __future__ import annotations

import re

import requests

BASE_URL = "https://www.biomar.com"
LISTING_URL = f"{BASE_URL}/es-ec/alimentos-y-servicios/especies/camaron"
LIST_WIDGET_ID = "product-list-d2b6e458"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; competence-scraper/1.0)"}

_PRODUCT_HREF_RE = re.compile(
    r'href="(/es-ec/alimentos-y-servicios/todos-nuestros-alimentos/[a-z0-9\-]+)"'
)


def fetch(url: str, session: requests.Session | None = None) -> str:
    s = session or requests
    r = s.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.text


def discover_product_urls(session: requests.Session | None = None) -> list[str]:
    """El listado pagina de a 12 via querystring GET (HTMX, sin JS
    necesario): `?{widget}-skip=N&{widget}-take=12`. Se recorre hasta que
    una pagina no aporte URLs nuevas."""
    session = session or requests.Session()
    seen: dict[str, None] = {}
    skip = 0
    take = 12
    while True:
        url = f"{LISTING_URL}?{LIST_WIDGET_ID}-skip={skip}&{LIST_WIDGET_ID}-take={take}"
        html = fetch(url, session=session)
        found = _PRODUCT_HREF_RE.findall(html)
        new = [f for f in found if f not in seen]
        if not new:
            break
        for f in new:
            seen[f] = None
        skip += take
    return [BASE_URL + path for path in seen]


def scrape_all() -> list[dict]:
    session = requests.Session()
    results = []
    for url in discover_product_urls(session):
        html = fetch(url, session=session)
        results.append({"url": url, "html": html})
    return results
