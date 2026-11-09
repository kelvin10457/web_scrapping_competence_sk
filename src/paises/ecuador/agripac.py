"""Agripac Ecuador: agripac.com.ec."""
from __future__ import annotations

from paises.ecuador import agripac_parser, agripac_scraper, agrizon_hatchery


def run() -> list[dict]:
    # R11.2: la proteina vacia de los Bernaqua se completa con Agrizon.
    records = agripac_parser.parse_listing(agripac_scraper.scrape_all())
    return agrizon_hatchery.completar_proteina(records, agrizon_hatchery.productos())
