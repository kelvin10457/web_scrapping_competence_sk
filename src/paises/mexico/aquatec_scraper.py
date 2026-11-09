"""Scraper de AQUATEC (Mexico): una sola pagina del distribuidor Nutrimentos de
la Cruz. Verificado 2026-11-09 (R7.6). El certificado SSL de nutrimentos.com.mx
es invalido: por decision del usuario (2026-11-09) se acepta, **solo** para ese
dominio (verify=False acotado en `_verify`)."""
from __future__ import annotations

import warnings
from urllib.parse import urljoin, urlparse

import requests
from urllib3.exceptions import InsecureRequestWarning

import netutil

PAGE_URL = "https://nutrimentos.com.mx/acuicultura_1"
HOSTS_SSL_INVALIDO = {"nutrimentos.com.mx", "www.nutrimentos.com.mx"}
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                         "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"}


def _verify(url: str) -> bool:
    return urlparse(url).hostname not in HOSTS_SSL_INVALIDO


def _get(url: str, session, max_redirects: int = 5) -> requests.Response:
    """Las redirecciones se siguen a mano: `verify=False` nunca viaja a otro
    dominio (requests lo mantendria en un 302 hacia otro host)."""
    for _ in range(max_redirects + 1):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", InsecureRequestWarning)
            r = netutil.get(session, url, headers=HEADERS, timeout=60,
                            verify=_verify(url), allow_redirects=False)
        if not r.is_redirect:
            r.raise_for_status()
            return r
        url = urljoin(url, r.headers["Location"])
    raise requests.TooManyRedirects(url)


def scrape_all() -> list[dict]:
    """[{url, html}] de la pagina de acuicultura."""
    session = requests.Session()
    return [{"url": PAGE_URL, "html": _get(PAGE_URL, session).text}]
