"""Motor de Aquaxcel (Cargill): mismo sitio, `/productos/{pais_slug}/`. El parser
soporta los dos layouts conocidos (Ecuador: bloques "Portafolio"; Mexico:
tarjetas). Cada pais lo invoca desde paises/<pais>/aquaxcel.py."""
from __future__ import annotations

from paises._compartido import aquaxcel_parser as parser
from paises._compartido import aquaxcel_scraper as scraper


def run(pais_slug: str) -> list[dict]:
    return parser.parse_listing(scraper.scrape_all(pais_slug=pais_slug))
