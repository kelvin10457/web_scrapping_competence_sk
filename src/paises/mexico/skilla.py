"""Skilla (BioBlue / Grupo NU3) Mexico: bioblue.com/skilla/ (R7.8)."""
from __future__ import annotations

from paises.mexico import skilla_parser, skilla_scraper


def run() -> list[dict]:
    return [r for item in skilla_scraper.scrape_all()
            for r in skilla_parser.parse_page(item["url"], item["html"], item["ocr"])]
