"""AQUATEC (Nueva Tecnologia en Alimentacion) Mexico via su distribuidor
nutrimentos.com.mx/acuicultura_1 (R7.6)."""
from __future__ import annotations

from paises.mexico import aquatec_parser, aquatec_scraper


def run() -> list[dict]:
    return [r for item in aquatec_scraper.scrape_all()
            for r in aquatec_parser.parse_page(item["url"], item["html"])]
