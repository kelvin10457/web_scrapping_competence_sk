"""Registro declarativo de fuentes: (pais, empresa) -> scraper + parser.

PLAN_REGIONAL.md 2.2. Reemplaza los `if empresa == ...` de pipeline.run_empresa.
Los modulos se importan con importlib, por eso ScraperCompetencia.spec los lista
en `hiddenimports`: sin eso el .exe no los encuentra.

`kind` dice como se conectan scraper y parser:
- "items":   scrape_all(**params) -> [{url, html, pdf_bytes}]; parser.parse_product
             se llama por item (Nicovita, HAID).
- "listing": parser.parse_listing(scrape_all(**params)) (Aquaxcel, Agripac, Agrizon).
Los parsers no agregan `pais`; lo agrega pipeline.
"""
from __future__ import annotations

import importlib

FUENTES: dict[tuple[str, str], dict] = {
    ("ecuador", "nicovita"): {"scraper": "nicovita", "parser": "nicovita", "kind": "items", "params": {"pais_slug": "ecuador"}},
    ("ecuador", "haid"): {"scraper": "haid", "parser": "haid", "kind": "items", "params": {}},
    ("ecuador", "aquaxcel"): {"scraper": "aquaxcel", "parser": "aquaxcel", "kind": "listing", "params": {"pais_slug": "ecuador"}},
    # biomar.com deshabilitado a proposito (ver MEMORY.md "BioMar -- fuente
    # complementaria Agrizon"): BioMar aparece solo via Agrizon.
    ("ecuador", "biomar"): {"scraper": "agrizon", "parser": "agrizon", "kind": "listing", "params": {}},
    ("ecuador", "agripac"): {"scraper": "agripac", "parser": "agripac", "kind": "listing", "params": {}},
}

# Orden estable de empresas (el de pipeline.ALL_EMPRESAS historico).
EMPRESA_ORDER = ["nicovita", "haid", "aquaxcel", "biomar", "agripac"]


def listar(pais: str | None = None, empresa: str | None = None) -> list[tuple[str, str]]:
    """Pares (pais, empresa) registrados, filtrados, en orden estable."""
    def key(par):
        pais_, empresa_ = par
        orden = EMPRESA_ORDER.index(empresa_) if empresa_ in EMPRESA_ORDER else len(EMPRESA_ORDER)
        return (pais_ != "ecuador", pais_, orden, empresa_)

    pares = [
        par for par in FUENTES
        if (pais is None or par[0] == pais) and (empresa is None or par[1] == empresa)
    ]
    return sorted(pares, key=key)


def empresas() -> list[str]:
    """Empresas distintas registradas (orden estable)."""
    vistas = {e for _, e in FUENTES}
    return sorted(vistas, key=lambda e: (EMPRESA_ORDER.index(e) if e in EMPRESA_ORDER else 99, e))


def run_fuente(pais: str, empresa: str) -> list[dict]:
    """Scrapea y parsea un (pais, empresa). Agrega `pais` a cada registro."""
    try:
        fuente = FUENTES[(pais, empresa)]
    except KeyError:
        raise ValueError(f"Fuente desconocida: {pais}/{empresa}") from None
    sc = importlib.import_module(f"scrapers.{fuente['scraper']}")
    pr = importlib.import_module(f"parsers.{fuente['parser']}")
    params = fuente["params"]
    if fuente["kind"] == "items":
        records = []
        for item in sc.scrape_all(**params):
            records.extend(pr.parse_product(item["url"], item["html"], item["pdf_bytes"]))
    else:
        records = pr.parse_listing(sc.scrape_all(**params))
    for record in records:
        record["pais"] = pais
    return records
