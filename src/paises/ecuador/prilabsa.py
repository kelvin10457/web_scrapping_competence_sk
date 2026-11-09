"""Prilabsa (Ecuador, distribuidor): catalogo PDF con Zeigler, Mackay Marine
e Higashimaru (R7.7)."""
from __future__ import annotations

from paises.ecuador import prilabsa_parser, prilabsa_scraper


def run() -> list[dict]:
    return prilabsa_parser.parse_pdf(prilabsa_scraper.descargar())
