"""Italcol (Colombia) como fuente de Panama: AQUACAMARON 35 (R8.11)."""
from __future__ import annotations

from paises.panama import italcol_parser, italcol_scraper


def run() -> list[dict]:
    return [r for item in italcol_scraper.scrape_all()
            for r in italcol_parser.parse_page(item["url"], item["html"])]
