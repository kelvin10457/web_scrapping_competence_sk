"""Scraper de Nicovita Ecuador: descubre productos y descarga sus fichas
tecnicas PDF. Sitio 100% HTML estatico (confirmado en MEMORY.md), sin
necesidad de navegador headless.
"""
from __future__ import annotations

import re
from pathlib import Path

import requests

BASE_URL = "https://nicovita.com"
LIST_URL = f"{BASE_URL}/categoria/camarones/?pais=ecuador"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; competence-scraper/1.0)"}
RAW_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "raw" / "nicovita"

# Solo exige el prefijo "nicovita-" tras "/productos/" -- Nicovita NO es
# consistente con el sufijo de pais: la mayoria de los productos usan
# "-ecuador" (ej. nicovita-katal-proterra-ecuador/), pero al menos dos
# (Finalis Proterra, Classic Proterra) estan enlazados en la MISMA pagina de
# categoria Ecuador con una URL generica sin ese sufijo (confirmado
# 2026-09-03: nicovita-finalis-proterra/ da 200 con ficha PDF propia,
# nicovita-finalis-proterra-ecuador/ da 404). Filtrar por "-ecuador" dejaba
# esos productos totalmente fuera del scraper. En vez de perseguir cada
# patron de URL nuevo a mano, se toma TODO link a producto de esta pagina y
# los alias duplicados (ej. nicovita-finalis/ para el mismo Finalis, o
# nicovita-katal-proterra/ sin sufijo para el mismo Katal Proterra) se
# filtran por contenido real en scrape_all() (ver _canonical_key), no por
# como luce la URL -- asi un futuro alias con un patron distinto tambien
# queda cubierto sin tocar este regex de nuevo.
_PRODUCT_URL_RE = re.compile(r"https://nicovita\.com/productos/nicovita-[a-z0-9\-]+/?")
_PDF_LINK_RE = re.compile(
    r'href="(https://nicovita\.com/wp-content/uploads/[^"]+\.pdf)"\s+class="btn-link btn-violeta"\s+download'
)
_TITLE_RE = re.compile(r"<title>(.*?)</title>", re.S)


def fetch(url: str, session: requests.Session | None = None) -> str:
    s = session or requests
    r = s.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.text


def discover_product_urls(session: requests.Session | None = None) -> list[str]:
    html = fetch(LIST_URL, session=session)
    urls = {u.rstrip("/") + "/" for u in _PRODUCT_URL_RE.findall(html)}
    # Las URLs "-ecuador" van primero: si dos terminan siendo la misma
    # pagina (ver _canonical_key en scrape_all), la version localizada queda
    # como fuente_url en vez de un alias generico, igual que en los datos
    # historicos.
    return sorted(urls, key=lambda u: (not u.rstrip("/").endswith("-ecuador"), u))


def find_pdf_url(product_html: str) -> str | None:
    m = _PDF_LINK_RE.search(product_html)
    return m.group(1) if m else None


def _canonical_key(html: str, pdf_url: str | None) -> tuple[str | None, str | None]:
    """Identidad real de una pagina de producto: nombre normalizado + URL de
    su ficha PDF. Dos URLs de /productos/ con la MISMA clave son la misma
    pagina bajo dos alias -- caso real 2026-09-03: "Nicovita Finalis Ecuador
    » Nicovita" y "Nicovita Finalis » Nicovita" son el mismo titulo salvo la
    palabra "Ecuador", y ambas URLs devuelven el mismo PDF byte a byte.
    No alcanza con comparar solo el PDF: Terap y Terap E+ comparten a
    proposito la misma ficha (Nicovita no publica una distinta para la
    variante E+, ver _SLUG_TO_NAME en parsers/nicovita.py) pero son
    productos distintos -- por eso la clave exige que el nombre TAMBIEN
    coincida, no solo el PDF."""
    m = _TITLE_RE.search(html)
    title = m.group(1) if m else None
    if title:
        title = re.sub(r"\s*»\s*Nicovita\s*$", "", title, flags=re.I)
        title = re.sub(r"\bEcuador\b", "", title, flags=re.I)
        title = re.sub(r"\s+", " ", title).strip().lower()
    return title, pdf_url


def download_pdf(pdf_url: str, session: requests.Session | None = None) -> bytes:
    s = session or requests
    r = s.get(pdf_url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.content


def save_pdf(pdf_url: str, content: bytes) -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    filename = pdf_url.rsplit("/", 1)[-1]
    dest = RAW_DIR / filename
    dest.write_bytes(content)
    return dest


def scrape_all() -> list[dict]:
    """Devuelve una lista de dicts crudos: {url, html, pdf_url, pdf_bytes,
    pdf_path} listos para pasar al parser. pdf_bytes es None si la pagina no
    tiene ficha tecnica enlazada (no deberia pasar segun MEMORY.md, pero no
    se asume). Salta paginas que son un alias duplicado de una ya vista
    (mismo nombre + mismo PDF, ver _canonical_key) para no generar dos filas
    identicas con distinto fuente_url."""
    session = requests.Session()
    results = []
    seen_keys: set[tuple[str, str]] = set()
    for url in discover_product_urls(session):
        html = fetch(url, session=session)
        pdf_url = find_pdf_url(html)
        key = _canonical_key(html, pdf_url)
        if key[0] is not None and key in seen_keys:
            continue
        seen_keys.add(key)
        pdf_bytes = None
        pdf_path = None
        if pdf_url:
            pdf_bytes = download_pdf(pdf_url, session=session)
            pdf_path = save_pdf(pdf_url, pdf_bytes)
        results.append(
            {
                "url": url,
                "html": html,
                "pdf_url": pdf_url,
                "pdf_bytes": pdf_bytes,
                "pdf_path": pdf_path,
            }
        )
    return results
