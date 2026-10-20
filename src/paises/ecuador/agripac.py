"""Agripac Ecuador: agripac.com.ec."""
from __future__ import annotations

from paises.ecuador import agripac_parser, agripac_scraper


def run() -> list[dict]:
    return agripac_parser.parse_listing(agripac_scraper.scrape_all())
