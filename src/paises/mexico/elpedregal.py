"""El Pedregal Silver Cup Mexico: el-pedregal.com/alimento/crustaceos (R7.5)."""
from __future__ import annotations

from paises.mexico import elpedregal_parser, elpedregal_scraper


def run() -> list[dict]:
    return elpedregal_parser.parse_listing(elpedregal_scraper.scrape_all())
