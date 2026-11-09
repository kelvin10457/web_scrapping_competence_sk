"""Diagnostico de una URL: pide UNA pagina con los mismos headers que usan los
scrapers y muestra exactamente que contesta el sitio (codigo, redirecciones,
pagina final, cabeceras relevantes). Guarda el cuerpo en data/bloqueos/ para
abrirlo en el navegador. No reintenta, no pausa y no intenta evadir nada.

Uso:
    python src/diagnostico.py "https://nicovita.com/categoria/camarones/?pais=honduras"
"""
from __future__ import annotations

import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
import netutil  # noqa: E402

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; competence-scraper/1.0)"}
CABECERAS = ("server", "content-type", "location", "set-cookie", "retry-after", "x-cache", "cf-ray")


def main(url: str) -> int:
    print(f"Pidiendo: {url}")
    print(f"User-Agent: {HEADERS['User-Agent']}\n")
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
    except requests.RequestException as exc:
        print(f"SIN RESPUESTA: {type(exc).__name__}: {exc}")
        print("-> el sitio no contesta (caido, lento o cortando la conexion).")
        return 2

    print("Redirecciones:")
    for h in r.history:
        print(f"  {h.status_code}  {h.url}\n      -> {h.headers.get('location', '')[:120]}")
    print(f"Respuesta final: {r.status_code}  {r.url[:150]}")
    print("\nCabeceras:")
    for k in CABECERAS:
        if k in r.headers:
            v = r.headers[k]
            print(f"  {k}: {v[:120]}")

    titulo = re.search(r"<title>(.*?)</title>", r.text, re.S | re.I)
    print(f"\nTitulo de la pagina: {titulo.group(1).strip()[:100] if titulo else '(sin titulo)'}")
    print(f"Tamano: {len(r.text)} caracteres")

    bloqueado = any(m in r.url.lower() for m in netutil._BLOCK_MARKERS)
    netutil.BLOQUEOS_DIR.mkdir(parents=True, exist_ok=True)
    host = re.sub(r"[^a-z0-9]+", "_", (urlparse(url).hostname or "sitio").lower())
    ruta = netutil.BLOQUEOS_DIR / f"diag_{host}_{datetime.now():%Y%m%d_%H%M%S}.html"
    ruta.write_text(r.text, encoding="utf-8", errors="replace")
    print(f"Cuerpo guardado en: {ruta}")

    print()
    if bloqueado:
        print("DIAGNOSTICO: BLOQUEADO por anti-bot (te mandaron a una pagina de verificacion).")
        print("Para verlo: 1) abre el .html guardado (doble clic); 2) abre la 'Respuesta final' o la")
        print("URL original en tu navegador: si ahi entras normal, el sitio solo bloquea al script.")
        return 1
    if r.status_code == 200:
        print("DIAGNOSTICO: OK, el sitio contesto la pagina normal.")
        return 0
    print(f"DIAGNOSTICO: el sitio contesto {r.status_code} (no parece captcha; revisa el cuerpo guardado).")
    return 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
