"""Motor de Nicovita: el sitio es el mismo para todos los paises y cambia solo el
`pais_slug` (?pais=...). Cada pais lo invoca desde paises/<pais>/nicovita.py."""
from __future__ import annotations

from paises._compartido import nicovita_parser as parser
from paises._compartido import nicovita_scraper as scraper


def run(pais_slug: str) -> list[dict]:
    records = []
    for item in scraper.scrape_all(pais_slug=pais_slug):
        records.extend(parser.parse_product(item["url"], item["html"], item["pdf_bytes"]))
    return records
