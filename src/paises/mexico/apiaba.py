"""Api-Aba Mexico: acuacultura.com.mx (ApiCamaron/Raceways)."""
from __future__ import annotations

from paises.mexico import apiaba_parser, apiaba_scraper


def run() -> list[dict]:
    return apiaba_parser.parse_listing(apiaba_scraper.scrape_all())
