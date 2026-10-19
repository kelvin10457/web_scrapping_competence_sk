"""Nicovita Ecuador: catalogo de nicovita.com/?pais=ecuador."""
from __future__ import annotations

from paises._compartido import nicovita

PAIS = "ecuador"


def run() -> list[dict]:
    return nicovita.run(pais_slug=PAIS)
