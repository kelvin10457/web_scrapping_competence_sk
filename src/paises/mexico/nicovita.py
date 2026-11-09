"""Nicovita Mexico: catalogo de nicovita.com/?pais=mexico."""
from __future__ import annotations

from paises._compartido import nicovita

PAIS = "mexico"


def run() -> list[dict]:
    return nicovita.run(pais_slug=PAIS)
