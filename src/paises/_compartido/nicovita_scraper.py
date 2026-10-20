"""Scraper de Nicovita Ecuador: descubre productos y descarga sus fichas
tecnicas PDF. Sitio 100% HTML estatico (confirmado en MEMORY.md), sin
necesidad de navegador headless.
"""
from __future__ import annotations

import re
import time
from pathlib import Path

import requests

import netutil

BASE_URL = "https://nicovita.com"
LIST_URL_TEMPLATE = f"{BASE_URL}/categoria/camarones/?pais={{pais_slug}}"
LIST_URL = LIST_URL_TEMPLATE.format(pais_slug="ecuador")
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; competence-scraper/1.0)"}
RAW_DIR = netutil.DATA_DIR / "raw" / "nicovita"  # no __file__: en el .exe apunta a _MEIxxxx temporal

# PDFs ya descargados en esta corrida (url -> bytes): las fichas se comparten
# entre paises (PLAN_REGIONAL.md 2.6), asi no se bajan dos veces.
_PDF_CACHE: dict[str, bytes] = {}

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


CACHE_TTL_SECONDS = 24 * 3600
HTML_CACHE_DIR = RAW_DIR.parent / "nicovita_html"


def cache_path(url: str) -> Path:
    """Archivo de cache de una URL. Si el sitio bloquea (captcha), se puede
    guardar la pagina a mano desde el navegador con este nombre exacto en
    data/raw/nicovita_html/ y el scraper la usa (ver README de _compartido)."""
    return HTML_CACHE_DIR / (re.sub(r"[^a-z0-9]+", "_", url.lower()).strip("_") + ".html")


def fetch(url: str, session: requests.Session | None = None) -> str:
    """HTML de una URL: cache de 24 h -> red (con pausa de cortesia) -> si el
    sitio bloquea, cualquier copia guardada (aunque sea vieja o manual)."""
    path = cache_path(url)
    if path.exists() and time.time() - path.stat().st_mtime < CACHE_TTL_SECONDS:
        return path.read_text(encoding="utf-8", errors="replace")
    s = session or requests
    try:
        r = netutil.get(s, url, headers=HEADERS, timeout=30)
        r.raise_for_status()
    except netutil.BlockedError:
        if path.exists():
            return path.read_text(encoding="utf-8", errors="replace")
        raise
    HTML_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(r.text, encoding="utf-8")
    return r.text


MANUAL_DIR = RAW_DIR.parent.parent / "manual" / "nicovita"
_CANONICAL_RES = (
    re.compile(r'<link[^>]+rel="canonical"[^>]+href="([^"]+)"', re.I),
    re.compile(r'property="og:url"[^>]+content="([^"]+)"', re.I),
)


def manual_pages(pais_slug: str) -> dict[str, str]:
    """Paginas de producto guardadas a mano desde el navegador en
    data/manual/nicovita/<pais>/ (cualquier nombre de archivo, "Guardar como... Solo
    HTML"). Se reconocen por su URL canonica real, asi que no hay que renombrar nada.
    Se usan solo si el sitio bloquea (captcha). {url: html}"""
    pages: dict[str, str] = {}
    folder = MANUAL_DIR / pais_slug
    if not folder.is_dir():
        return pages
    for path in sorted(list(folder.glob("*.htm")) + list(folder.glob("*.html"))):
        html = path.read_text(encoding="utf-8", errors="replace")
        for rx in _CANONICAL_RES:
            m = rx.search(html)
            if m and _PRODUCT_URL_RE.fullmatch(m.group(1).strip()):
                pages[m.group(1).strip().rstrip("/") + "/"] = html
                break
    return pages


def discover_product_urls(session: requests.Session | None = None, pais_slug: str = "ecuador") -> list[str]:
    html = fetch(LIST_URL_TEMPLATE.format(pais_slug=pais_slug), session=session)
    urls = {u.rstrip("/") + "/" for u in _PRODUCT_URL_RE.findall(html)}
    # Las URLs "-{pais_slug}" van primero: si dos terminan siendo la misma
    # pagina (ver _canonical_key en scrape_all), la version localizada queda
    # como fuente_url en vez de un alias generico, igual que en los datos
    # historicos.
    return sorted(urls, key=lambda u: (not u.rstrip("/").endswith(f"-{pais_slug}"), u))


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
    # Las fichas casi no cambian y se comparten entre paises: si ya estan en
    # data/raw/nicovita/ no se vuelven a pedir.
    existing = RAW_DIR / pdf_url.rsplit("/", 1)[-1]
    if existing.exists():
        return existing.read_bytes()
    s = session or requests
    r = netutil.get(s, pdf_url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.content


def save_pdf(pdf_url: str, content: bytes) -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    filename = pdf_url.rsplit("/", 1)[-1]
    dest = RAW_DIR / filename
    dest.write_bytes(content)
    return dest


def scrape_all(pais_slug: str = "ecuador") -> list[dict]:
    """Devuelve una lista de dicts crudos: {url, html, pdf_url, pdf_bytes,
    pdf_path} listos para pasar al parser. pdf_bytes es None si la pagina no
    tiene ficha tecnica enlazada (no deberia pasar segun MEMORY.md, pero no
    se asume). Salta paginas que son un alias duplicado de una ya vista
    (mismo nombre + mismo PDF, ver _canonical_key) para no generar dos filas
    identicas con distinto fuente_url."""
    session = requests.Session()
    results = []
    seen_keys: set[tuple[str, str]] = set()
    try:
        urls = discover_product_urls(session, pais_slug=pais_slug)
        get_html = lambda u: fetch(u, session=session)  # noqa: E731
    except netutil.BlockedError:
        manual = manual_pages(pais_slug)
        if not manual:
            raise
        print(f"  [bloqueado: usando {len(manual)} paginas guardadas a mano en {MANUAL_DIR / pais_slug}]")
        urls = sorted(manual, key=lambda u: (not u.rstrip("/").endswith(f"-{pais_slug}"), u))
        get_html = manual.__getitem__
    for url in urls:
        html = get_html(url)
        pdf_url = find_pdf_url(html)
        key = _canonical_key(html, pdf_url)
        if key[0] is not None and key in seen_keys:
            continue
        seen_keys.add(key)
        pdf_bytes = None
        pdf_path = None
        if pdf_url:
            pdf_bytes = _PDF_CACHE.get(pdf_url)
            if pdf_bytes is None:
                pdf_bytes = _PDF_CACHE[pdf_url] = download_pdf(pdf_url, session=session)
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
