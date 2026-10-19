"""GET con reintentos para los scrapers: los sitios fallan de forma transitoria
(timeouts, 5xx, 429). Reintenta con espera creciente y devuelve la ultima
respuesta; el caller sigue llamando raise_for_status()."""
from __future__ import annotations

import time

import requests

RETRY_STATUS = {429, 502, 503, 504}
# Servicios anti-bot que responden con un captcha/redireccion en vez del sitio.
_BLOCK_MARKERS = ("perfdrive.com", "captcha")


class BlockedError(RuntimeError):
    """El sitio nos bloqueo (captcha / bot manager). No se intenta evadirlo."""


def get(session, url: str, retries: int = 4, **kwargs) -> requests.Response:
    for intento in range(retries + 1):
        try:
            r = session.get(url, **kwargs)
        except (requests.Timeout, requests.ConnectionError):
            if intento == retries:
                raise
            time.sleep(min(5 * 2**intento, 60))
            continue
        if any(m in r.url.lower() for m in _BLOCK_MARKERS):
            raise BlockedError(f"Bloqueado por anti-bot al pedir {url} (redirigido a {r.url[:60]}...)")
        if r.status_code not in RETRY_STATUS or intento == retries:
            return r
        retry_after = r.headers.get("Retry-After", "")
        espera = int(retry_after) if retry_after.isdigit() else 5 * 2**intento
        time.sleep(min(espera, 60))
    return r
