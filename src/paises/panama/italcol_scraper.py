"""Scraper de Italcol AQUACAMARON 35 (R8.11): una sola ficha. Verificado 2026-11-09."""
from __future__ import annotations

import requests

import netutil

PAGE_URL = "https://italcol.com/producto/camaron-levante/"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                         "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"}


def scrape_all() -> list[dict]:
    r = netutil.get(requests.Session(), PAGE_URL, headers=HEADERS, timeout=60)
    r.raise_for_status()
    return [{"url": PAGE_URL, "html": r.text}]
