"""Megasupply Ecuador (R11.2): dietas liquidas Megalikuid via el distribuidor
Agrizon. Compiten con Skretting InVita."""
from __future__ import annotations

from paises.ecuador import agrizon_hatchery


def run() -> list[dict]:
    return agrizon_hatchery.megalikuid(agrizon_hatchery.productos())
