"""Nicovita Honduras: catalogo de nicovita.com/?pais=honduras."""
from __future__ import annotations

from paises._compartido import nicovita

PAIS = "honduras"


def run() -> list[dict]:
    return nicovita.run(pais_slug=PAIS)
