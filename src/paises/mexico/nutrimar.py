"""Nutrimar Mexico: nutrimar.mx (+ fichas tecnicas PDF o imagen; productos Zeigler con empresa=Zeigler)."""
from __future__ import annotations

from paises.mexico import nutrimar_parser, nutrimar_scraper


def run() -> list[dict]:
    return nutrimar_parser.parse_listing(nutrimar_scraper.scrape_all())
