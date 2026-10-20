"""Aquaxcel (Cargill) Ecuador: aquaxcel.com/productos/ecuador/."""
from __future__ import annotations

from paises._compartido import aquaxcel

PAIS = "ecuador"


def run() -> list[dict]:
    return aquaxcel.run(pais_slug=PAIS)
