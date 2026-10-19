"""Registro de fuentes, derivado de las carpetas por pais (src/paises/<pais>/).

Cada pais declara sus empresas en `paises.<pais>.FUENTES` y cada empresa es un
modulo `paises.<pais>.<empresa>` con `run() -> list[dict]` (scrapea + parsea).
Los modulos se importan con importlib, por eso ScraperCompetencia.spec los lista
en `hiddenimports`. El pipeline agrega la columna `pais`; los parsers no.
"""
from __future__ import annotations

import importlib

import schema

# Orden estable de empresas dentro de cada pais en la GUI/CLI.
EMPRESA_ORDER = ["nicovita", "haid", "aquaxcel", "biomar", "agripac", "vimifos", "apiaba", "nutrimar"]


def _fuentes_de(pais: str) -> list[str]:
    return list(importlib.import_module(f"paises.{pais}").FUENTES)


def listar(pais: str | None = None, empresa: str | None = None) -> list[tuple[str, str]]:
    """Pares (pais, empresa) registrados, filtrados, ecuador primero."""
    paises = sorted(schema.PAIS_VALUES, key=lambda p: (p != "ecuador", p))
    pares = [(p, e) for p in paises for e in _fuentes_de(p)]
    pares = [(p, e) for p, e in pares if (pais is None or p == pais) and (empresa is None or e == empresa)]
    return sorted(pares, key=lambda par: (par[0] != "ecuador", par[0], EMPRESA_ORDER.index(par[1])
                                          if par[1] in EMPRESA_ORDER else 99, par[1]))


def empresas() -> list[str]:
    vistas = {e for _, e in listar()}
    return sorted(vistas, key=lambda e: (EMPRESA_ORDER.index(e) if e in EMPRESA_ORDER else 99, e))


def run_fuente(pais: str, empresa: str) -> list[dict]:
    """Scrapea y parsea un (pais, empresa). Agrega `pais` a cada registro."""
    if (pais, empresa) not in listar():
        raise ValueError(f"Fuente desconocida: {pais}/{empresa}")
    modulo = importlib.import_module(f"paises.{pais}.{empresa}")
    records = modulo.run()
    for record in records:
        record["pais"] = pais
    return records
