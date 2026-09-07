"""Scraper de Agripac Ecuador (linea Feedpac): descubre los productos de la
categoria de alimento balanceado para acuacultura. Sitio HTML estatico
(WordPress + WooCommerce, confirmado 2026-09-03), sin ficha tecnica PDF -- a
diferencia de Nicovita/HAID, los datos tecnicos (tipo, tamano de pellet,
empaque) viven directamente en las pestanas de la propia pagina de producto
(ver src/parsers/agripac.py), no en un PDF aparte.
"""
from __future__ import annotations

import re

import requests

BASE_URL = "https://agripac.com.ec"
LISTING_URL = f"{BASE_URL}/division/alimento-balanceado-acuacultura/"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; competence-scraper/1.0)"}

# Division Larvicultura (agregada 2026-09-07): el usuario encontro que su
# reporte manual traia productos de post-larva/hatchery (Artemia Cysts,
# Larfeed, MeM, Mpex...) que LISTING_URL nunca scrapea -- viven en 3
# subdivisiones aparte, confirmadas contra el sitio en vivo el mismo dia:
# Dieta seca (12 productos: Larfeed, MeM, MeM 300-500, Mpex x4, Royal
# Oyster/Caviar/Seafood), Dieta viva (1: Artemia Cysts) y Dieta liquida (1:
# Royal Pepper Protein). Mismas plantilla y regex de descubrimiento que
# LISTING_URL -- es el mismo sitio WooCommerce, solo otra categoria.
LARVICULTURA_URLS = [
    f"{BASE_URL}/division/dieta-seca-larvicultura/",
    f"{BASE_URL}/division/dieta-viva-larvicultura/",
    f"{BASE_URL}/division/dieta-liquida-larvicultura/",
]

_PRODUCT_URL_RE = re.compile(r'href="(https://agripac\.com\.ec/productos/[a-z0-9\-]+/)"')


def fetch(url: str, session: requests.Session | None = None) -> str:
    s = session or requests
    r = s.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.text


def discover_product_urls(listing_url: str = LISTING_URL, session: requests.Session | None = None) -> list[str]:
    """El listado pagina via "/page/N/" (20 productos en 2 paginas para
    LISTING_URL, confirmado 2026-09-03; las 3 URLs de Larvicultura no
    paginan -- caben en 1 pagina cada una, pero se recorren igual por si
    algun dia crecen). Se recorre hasta que una pagina no aporte URLs
    nuevas -- mismo criterio que src/scrapers/biomar.py -- en vez de asumir
    un numero fijo de paginas, porque pedir una pagina fuera de rango no da
    404 (WordPress responde 200 igual), asi que no hay forma de detectar el
    final salvo por contenido repetido."""
    s = session or requests.Session()
    seen: dict[str, None] = {}
    page = 1
    while True:
        url = listing_url if page == 1 else f"{listing_url}page/{page}/"
        html = fetch(url, session=s)
        found = _PRODUCT_URL_RE.findall(html)
        new = [f for f in found if f not in seen]
        if not new and page > 1:
            break
        for f in new:
            seen[f] = None
        page += 1
    return sorted(seen)


def scrape_all() -> list[dict]:
    session = requests.Session()
    results = []
    for url in discover_product_urls(LISTING_URL, session):
        html = fetch(url, session=session)
        results.append({"url": url, "html": html, "es_larvicultura": False})
    for larvi_url in LARVICULTURA_URLS:
        for url in discover_product_urls(larvi_url, session):
            html = fetch(url, session=session)
            results.append({"url": url, "html": html, "es_larvicultura": True})
    return results
