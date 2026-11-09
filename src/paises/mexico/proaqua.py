"""ProAqua (distribuidor, Mexico): alimentos formulados de Biogrow y Epicore (R7.9)."""
from __future__ import annotations

from paises.mexico import proaqua_parser, proaqua_scraper


def run() -> list[dict]:
    return [r for item in proaqua_scraper.scrape_all()
            for r in proaqua_parser.parse_producto(item["url"], item["html"])]
