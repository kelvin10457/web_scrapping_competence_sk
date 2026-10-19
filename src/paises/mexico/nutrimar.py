"""Nutrimar Mexico: nutrimar.mx (parcial: solo nombres)."""
from __future__ import annotations

from paises.mexico import nutrimar_parser, nutrimar_scraper


def run() -> list[dict]:
    return nutrimar_parser.parse_listing(nutrimar_scraper.scrape_all())
