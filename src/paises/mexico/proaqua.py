"""ProAqua México: formulados Biogrow/Epicore (R7.9) y microalgas Reed (R11.3)."""
from __future__ import annotations

from paises.mexico import proaqua_parser, proaqua_scraper


def run() -> list[dict]:
    return [r for item in proaqua_scraper.scrape_all()
            for r in (proaqua_parser.parse_reed if item.get("reed") else proaqua_parser.parse_producto)(
                item["url"], item["html"])]
