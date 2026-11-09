"""NasaFeed Aquanasa (Panama): ficha PDF Linea Premium (R8.10)."""
from __future__ import annotations

from paises.panama import nasafeed_parser, nasafeed_scraper


def run() -> list[dict]:
    url, pdf = nasafeed_scraper.descargar()
    return nasafeed_parser.parse_pdf(url, pdf)
