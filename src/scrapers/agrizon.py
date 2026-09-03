"""Scraper de Agrizon (distribuidor en Ecuador): fuente complementaria para
completar los campos tecnicos de BioMar que biomar.com no publica -- ver
src/parsers/biomar.py y PLAN.md § 5 ("Datos nutricionales de BioMar... via
distribuidores locales").

Usa el endpoint JSON publico de Shopify de la coleccion completa
(`/collections/<handle>/products.json`), NO el HTML con el querystring
`?filter.p.vendor=BioMar` -- ese filtro solo afecta el HTML renderizado por
JS del listado, no tiene efecto sobre products.json. El endpoint trae TODOS
los productos de la coleccion (181 al confirmar esto, 2026-09-03) con
`vendor` incluido por producto, asi que se filtra por vendor == "BioMar" del
lado del cliente. Confirmado con requests+PowerShell que `tags` viene como
array real (no string separado por comas, a diferencia del endpoint
`/products/<handle>.json` de un producto individual).
"""
from __future__ import annotations

import requests

BASE_URL = "https://agrizon.com"
COLLECTION_URL = f"{BASE_URL}/en/collections/nutricion-animal"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; competence-scraper/1.0)"}
VENDOR = "BioMar"
PAGE_LIMIT = 250  # maximo permitido por Shopify en products.json


def fetch_collection_products(session: requests.Session | None = None) -> list[dict]:
    """Pagina products.json (250 por pagina) hasta que una pagina vuelva
    vacia. Con 181 productos totales en la coleccion (2026-09-03) alcanza
    con 1 pagina, pero se pagina igual por si la coleccion crece."""
    s = session or requests
    products: list[dict] = []
    page = 1
    while True:
        url = f"{COLLECTION_URL}/products.json?limit={PAGE_LIMIT}&page={page}"
        r = s.get(url, headers=HEADERS, timeout=30)
        r.raise_for_status()
        batch = r.json().get("products", [])
        if not batch:
            break
        products.extend(batch)
        page += 1
    return products


def scrape_all(session: requests.Session | None = None) -> list[dict]:
    session = session or requests.Session()
    products = fetch_collection_products(session)
    return [p for p in products if p.get("vendor") == VENDOR]
