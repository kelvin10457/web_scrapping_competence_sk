"""Prilabsa (Ecuador, distribuidor): catalogo PDF con Zeigler, Mackay Marine
e Higashimaru (R7.7)."""
from __future__ import annotations

from paises.ecuador import agrizon_hatchery, prilabsa_parser, prilabsa_scraper


def run() -> list[dict]:
    # R11.2: + Biomasa de Artemia Congelada, que el PDF no trae (sale de Agrizon).
    records = prilabsa_parser.parse_pdf(prilabsa_scraper.descargar())
    return records + agrizon_hatchery.biomasa_artemia(agrizon_hatchery.productos())
