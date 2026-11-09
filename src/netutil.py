"""GET para los scrapers, en un solo lugar:

- Ritmo cortes e irregular (solo para PACED_HOSTS: nicovita.com, que mostro captcha,
  y agrizon.com, que respondio 429): pausa aleatoria de 0.5-2.5 s entre consultas
  (sesgada a ~1 s) y una pausa larga aleatoria de 5-12 s cada 6-10 consultas
  nuevas (no cuentan las paginas que salen de la cache). Presupuesto acordado
  (R6.1): <=3 min por pais en frio. Es para no cargar al sitio; NO desbloquea un
  bloqueo que ya existe ni resuelve captchas.
- Tras un captcha (R6.2), SOLO ese dominio pasa a ritmo lento (6-15 s); tras
  MAX_BLOQUEOS_POR_HOST captchas en la corrida, ese dominio ya no se consulta
  (BlockedError sin red): el scraper usa su copia guardada y el resto sigue.
- Reintentos con espera creciente y al azar en fallos transitorios (timeouts, 429,
  5xx); con Retry-After se espera al menos eso.
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

# Solo los sitios que SI mostraron captcha o 429 se piden con pausas; el resto va sin
# pausas (decision del usuario). Para agregar un sitio que empiece a bloquear,
# basta sumar su dominio aqui.
PACED_HOSTS = {"nicovita.com", "agrizon.com"}

# Ritmo (se desactiva en tests con ENABLED = False o SCRAPER_NO_PAUSE=1).
ENABLED = True
SHORT_PAUSE = (0.5, 2.5, 1.0)  # min, max, moda (random.triangular)
LONG_PAUSE = (5.0, 12.0)
LONG_EVERY = (6, 10)
SLOW_PAUSE = (6.0, 15.0)  # dominio que ya mostro captcha en esta corrida
MAX_BLOQUEOS_POR_HOST = 2

if getattr(sys, "frozen", False):
    _ROOT = Path(sys.executable).resolve().parent
else:
    _ROOT = Path(__file__).resolve().parent.parent
# data/ junto al .exe (o del repo): los scrapers guardan aqui su cache en data/raw/.
DATA_DIR = _ROOT / "data"
BLOQUEOS_DIR = DATA_DIR / "bloqueos"

_state = {"n": 0, "next_long": random.randint(*LONG_EVERY)}
_blocked: list[dict] = []
_lentos: set[str] = set()
_bloqueos_por_host: dict[str, int] = {}
_ultimo_bloqueo: dict[str, tuple[str, Path | None]] = {}  # host -> (captcha_url, pagina guardada)


def _host(url: str) -> str:
    return (urlparse(url).hostname or "").lower().removeprefix("www.")


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
    _lentos.clear()
    _bloqueos_por_host.clear()
    _ultimo_bloqueo.clear()


def pause(url: str | None = None) -> None:
    """Pausa aleatoria antes de una consulta nueva a la red, solo para los
    dominios de PACED_HOSTS."""
    import os

    host = _host(url) if url is not None else None
    if host is not None and host not in PACED_HOSTS and host not in _lentos:
        return
    if not ENABLED or os.environ.get("SCRAPER_NO_PAUSE") == "1":
        return
    if host in _lentos:
        time.sleep(random.uniform(*SLOW_PAUSE))
        return
    _state["n"] += 1
    if _state["n"] >= _state["next_long"]:
        espera = random.uniform(*LONG_PAUSE)
        print(f"  [pausa larga de {espera:.0f}s tras {_state['n']} consultas]", flush=True)
        _state["n"] = 0
        _state["next_long"] = random.randint(*LONG_EVERY)
    else:
        espera = random.triangular(*SHORT_PAUSE)
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


def _backoff(intento: int, minimo: int = 0) -> float:
    """Espera antes de reintentar: crece con el intento (5, 10, 20... s, tope
    90 s), con +0-50 % al azar, y nunca menos que el Retry-After del sitio."""
    base = max(min(5 * 2**intento, 60), minimo)
    return min(base * random.uniform(1.0, 1.5), max(90.0, minimo))


def get(session, url: str, retries: int = 4, **kwargs) -> requests.Response:
    host = _host(url)
    if _bloqueos_por_host.get(host, 0) >= MAX_BLOQUEOS_POR_HOST:
        captcha_url, saved = _ultimo_bloqueo.get(host, ("", None))
        raise BlockedError(url, captcha_url, saved)  # sin red: reusa el ultimo captcha del dominio
    pause(url)
    for intento in range(retries + 1):
        try:
            r = session.get(url, **kwargs)
        except (requests.Timeout, requests.ConnectionError):
            if intento == retries:
                raise
            time.sleep(_backoff(intento))
            continue
        if any(m in r.url.lower() for m in _BLOCK_MARKERS):
            saved = _save_block_page(url, r)
            _lentos.add(host)
            _bloqueos_por_host[host] = _bloqueos_por_host.get(host, 0) + 1
            _ultimo_bloqueo[host] = (r.url, saved)
            _blocked.append({"url": url, "captcha_url": r.url, "archivo": str(saved) if saved else ""})
            raise BlockedError(url, r.url, saved)
        if r.status_code not in RETRY_STATUS or intento == retries:
            return r
        retry_after = r.headers.get("Retry-After", "")
        time.sleep(_backoff(intento, int(retry_after) if retry_after.isdigit() else 0))
    return r
