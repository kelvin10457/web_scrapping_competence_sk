"""Vimifos Mexico: vimifos.com (lineas de camaron)."""
from __future__ import annotations

from paises.mexico import vimifos_parser, vimifos_scraper


def run() -> list[dict]:
    return vimifos_parser.parse_listing(vimifos_scraper.scrape_all())
