"""Aquaxcel (Cargill) Mexico: aquaxcel.com/productos/mexico/."""
from __future__ import annotations

from paises._compartido import aquaxcel

PAIS = "mexico"


def run() -> list[dict]:
    return aquaxcel.run(pais_slug=PAIS)
