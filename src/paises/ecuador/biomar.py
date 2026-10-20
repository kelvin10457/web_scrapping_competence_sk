"""BioMar Ecuador, solo via el distribuidor Agrizon (decision del usuario 2026-09-03;
biomar.com queda deshabilitado, ver biomar_scraper.py/biomar_parser.py sin usar)."""
from __future__ import annotations

from paises.ecuador import agrizon_parser, agrizon_scraper


def run() -> list[dict]:
    return agrizon_parser.parse_listing(agrizon_scraper.scrape_all())
