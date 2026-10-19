"""GET para los scrapers, en un solo lugar:

- Ritmo cortes y irregular (solo para PACED_HOSTS, hoy nicovita.com, el unico que
  mostro captcha): pausa aleatoria de 1.5-4 s entre consultas y una pausa
  larga aleatoria de 20-30 s cada 3-5 consultas nuevas (no cuentan las paginas
  que salen de la cache). Es para no cargar al sitio; NO desbloquea un bloqueo
  que ya existe ni resuelve captchas.
- Reintentos con espera creciente en fallos transitorios (timeouts, 429, 5xx).
- Deteccion de bloqueo anti-bot (captcha): se detiene, guarda la pagina que vio el
  script en data/bloqueos/ y levanta BlockedError. No se intenta evadir.
"""
from __future__ import annotations

import random
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import requests

RETRY_STATUS = {429, 502, 503, 504}
# Servicios anti-bot que responden con un captcha/redireccion en vez del sitio.
_BLOCK_MARKERS = ("perfdrive.com", "captcha")

# Solo los sitios que SI mostraron captcha se piden con pausas; el resto va sin
# pausas (decision del usuario). Para agregar un sitio que empiece a bloquear,
# basta sumar su dominio aqui.
PACED_HOSTS = {"nicovita.com"}

# Ritmo (se desactiva en tests con ENABLED = False o SCRAPER_NO_PAUSE=1).
ENABLED = True
SHORT_PAUSE = (1.5, 4.0)
LONG_PAUSE = (20.0, 30.0)
LONG_EVERY = (3, 5)

if getattr(sys, "frozen", False):
    _ROOT = Path(sys.executable).resolve().parent
else:
    _ROOT = Path(__file__).resolve().parent.parent
BLOQUEOS_DIR = _ROOT / "data" / "bloqueos"

_state = {"n": 0, "next_long": random.randint(*LONG_EVERY)}
_blocked: list[dict] = []


class BlockedError(RuntimeError):
    """El sitio nos bloqueo (captcha / bot manager). No se intenta evadirlo."""

    def __init__(self, url: str, captcha_url: str, saved: Path | None):
        self.url, self.captcha_url, self.saved = url, captcha_url, saved
        super().__init__(
            f"BLOQUEADO por anti-bot (captcha) al pedir {url}. "
            f"La pagina que vio el script esta guardada en {saved}; abrela en tu navegador para ver el captcha."
        )


def blocked_events() -> list[dict]:
    """Bloqueos detectados en esta corrida: [{url, captcha_url, archivo}]."""
    return list(_blocked)


def reset_blocked() -> None:
    _blocked.clear()


def pause(url: str | None = None) -> None:
    """Pausa aleatoria antes de una consulta nueva a la red, solo para los
    dominios de PACED_HOSTS."""
    import os

    if url is not None:
        host = (urlparse(url).hostname or "").lower().removeprefix("www.")
        if host not in PACED_HOSTS:
            return
    if not ENABLED or os.environ.get("SCRAPER_NO_PAUSE") == "1":
        return
    _state["n"] += 1
    if _state["n"] >= _state["next_long"]:
        espera = random.uniform(*LONG_PAUSE)
        print(f"  [pausa larga de {espera:.0f}s tras {_state['n']} consultas]", flush=True)
        _state["n"] = 0
        _state["next_long"] = random.randint(*LONG_EVERY)
    else:
        espera = random.uniform(*SHORT_PAUSE)
    time.sleep(espera)


def _save_block_page(url: str, response: requests.Response) -> Path | None:
    try:
        BLOQUEOS_DIR.mkdir(parents=True, exist_ok=True)
        host = re.sub(r"[^a-z0-9]+", "_", (urlparse(url).hostname or "sitio").lower())
        path = BLOQUEOS_DIR / f"{host}_{datetime.now():%Y%m%d_%H%M%S}.html"
        path.write_text(response.text, encoding="utf-8", errors="replace")
        return path
    except OSError:
        return None


def get(session, url: str, retries: int = 4, **kwargs) -> requests.Response:
    pause(url)
    for intento in range(retries + 1):
        try:
            r = session.get(url, **kwargs)
        except (requests.Timeout, requests.ConnectionError):
            if intento == retries:
                raise
            time.sleep(min(5 * 2**intento, 60))
            continue
        if any(m in r.url.lower() for m in _BLOCK_MARKERS):
            saved = _save_block_page(url, r)
            _blocked.append({"url": url, "captcha_url": r.url, "archivo": str(saved) if saved else ""})
            raise BlockedError(url, r.url, saved)
        if r.status_code not in RETRY_STATUS or intento == retries:
            return r
        retry_after = r.headers.get("Retry-After", "")
        espera = int(retry_after) if retry_after.isdigit() else 5 * 2**intento
        time.sleep(min(espera, 60))
    return r
