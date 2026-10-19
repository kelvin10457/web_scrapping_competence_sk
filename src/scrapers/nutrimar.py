"""Scraper de Nutrimar (Grupo Acuicola Mexicano, Mexico). La pagina
https://www.grupoacuicolamexicano.com.mx/nutrimar enlaza cada producto en
https://www.nutrimar.mx/<slug> (Wix, HTML renderizado en servidor, robots.txt
permite todo; verificado 2026-10-19). Las paginas de producto solo traen nombre
y descripcion: no publican proteina, calibre ni empaque."""
from __future__ import annotations

import re
import time

import requests

import netutil

LISTING_URL = "https://www.grupoacuicolamexicano.com.mx/nutrimar"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; competence-scraper/1.0)"}
_LINK_RE = re.compile(r"https://www\.nutrimar\.mx/([A-Za-z0-9%\-]+)")
PAUSE_SECONDS = 1.0

# Enlaces del listado que NO son alimento formulado para camaron: alimento
# fresco/congelado, aditivos/probioticos y paginas de categoria.
NON_FEED_SLUGS = {
    "alimento-fresco-meggasuply", "biomasa-de-artemia", "calamar-cortado", "copepodos", "krill",
    "poliquetos", "remediate", "rescue", "probioticos-zeigler", "engorda-nutrimar",
    "larvario-zeigler", "maternidad-zeigler",
}


def fetch(url: str, session: requests.Session | None = None) -> str:
    s = session or requests
    r = netutil.get(s, url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.text


def discover_product_urls(listing_html: str) -> list[str]:
    slugs = sorted(set(_LINK_RE.findall(listing_html)))
    return [f"https://www.nutrimar.mx/{s}" for s in slugs if s not in NON_FEED_SLUGS and "%" not in s and not s.endswith("-zeigler")]


def scrape_all() -> list[dict]:
    session = requests.Session()
    items = []
    for url in discover_product_urls(fetch(LISTING_URL, session=session)):
        time.sleep(PAUSE_SECONDS)
        items.append({"url": url, "html": fetch(url, session=session)})
    return items
