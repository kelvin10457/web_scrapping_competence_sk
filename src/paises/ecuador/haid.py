"""HAID Ecuador: fichas tecnicas PDF de haid.com.ec."""
from __future__ import annotations

from paises.ecuador import haid_parser, haid_scraper


def run() -> list[dict]:
    records = []
    for item in haid_scraper.scrape_all():
        records.extend(haid_parser.parse_product(item["url"], item["html"], item["pdf_bytes"]))
    return records
