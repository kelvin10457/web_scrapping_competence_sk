"""Scraper de HAID Ecuador: descubre productos y descarga sus fichas
tecnicas PDF. Sitio HTML estatico. A diferencia de Nicovita, 3 de las 6
fichas de HAID son PDF de imagen escaneada sin capa de texto (confirmado
con pdfplumber y pymupdf) -- se resuelve con OCR local (Tesseract, sin
costo de API, decision confirmada con el usuario).
"""
from __future__ import annotations

import io
import re
from pathlib import Path

import fitz  # pymupdf
import pdfplumber
import pytesseract
import requests
from PIL import Image

BASE_URL = "https://www.haid.com.ec"
LIST_URL = f"{BASE_URL}/productos/"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; competence-scraper/1.0)"}
RAW_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "raw" / "haid"

# Confirmado manualmente (MEMORY.md): a la fecha estos son los 6 productos
# reales de HAID Ecuador. Se mantiene como fallback/referencia, pero
# scrape_all() ya NO depende de esta lista fija -- ver discover_product_slugs.
PRODUCT_SLUGS = ["starter-pro", "starter", "speed", "happiness", "happiness-plus", "fitness"]

# Candidatos a link de producto: un href de un solo segmento tipo
# "https://www.haid.com.ec/<slug>/" en el listado (NO cualquier URL del
# sitio -- el HTML tambien trae URLs de recursos internos de WordPress
# como wp-includes/wp-content en src= de scripts/estilos, que no son
# paginas navegables). El listado ademas usa tabs de Elementor duplicados
# para desktop/mobile (mismo href repetido dos veces), lo que hace fragil
# reconstruir DATOS de producto leyendo esos tabs -- pero para solo extraer
# el slug de la URL el duplicado no molesta (set() lo colapsa solo).
_PRODUCT_LINK_RE = re.compile(r'href="https://www\.haid\.com\.ec/([a-z0-9\-]+)/?"')

_TESSERACT_CANDIDATES = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    str(Path.home() / "AppData/Local/Programs/Tesseract-OCR/tesseract.exe"),
]
for _candidate in _TESSERACT_CANDIDATES:
    if Path(_candidate).exists():
        pytesseract.pytesseract.tesseract_cmd = _candidate
        break


def fetch(url: str, session: requests.Session | None = None) -> str:
    s = session or requests
    r = s.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.text


def product_url(slug: str) -> str:
    return f"{BASE_URL}/{slug}/"


def find_pdf_url(product_html: str) -> str | None:
    m = re.search(r'https://www\.haid\.com\.ec/wp-content/uploads/[^"\'\s)]+\.pdf', product_html, re.I)
    return m.group(0) if m else None


def discover_product_slugs(session: requests.Session | None = None) -> list[str]:
    """Descubre los slugs de producto en vez de depender de la lista fija
    PRODUCT_SLUGS, que quedaria desactualizada en silencio si HAID agrega un
    producto nuevo (mismo tipo de bug que dejaba fuera a Nicovita Finalis/
    Classic Proterra, ver src/scrapers/nicovita.py).

    El listado (LIST_URL) linkea tanto productos como paginas de navegacion
    (contactanos, sostenibilidad, el feed RSS, el endpoint REST de WP, etc.)
    bajo el mismo patron de URL "haid.com.ec/<slug>/", asi que no alcanza con
    juntar los links -- cada candidato se visita y se confirma como producto
    real solo si su pagina enlaza una ficha tecnica ("Ficha-tecnica-*.pdf" o
    variantes de mayuscula, el nombre de archivo que usa HAID para sus 6
    fichas reales). Confirmado 2026-09-03: distingue bien de "sostenibilidad"
    (SI tiene un PDF enlazado -- su Codigo de Conducta -- pero el archivo no
    se llama "ficha", asi que no matchea)."""
    s = session or requests.Session()
    html = fetch(LIST_URL, session=s)
    candidates = sorted(set(_PRODUCT_LINK_RE.findall(html)))
    slugs = []
    for slug in candidates:
        try:
            page_html = fetch(product_url(slug), session=s)
        except requests.HTTPError:
            continue
        pdf_url = find_pdf_url(page_html)
        if pdf_url and "ficha" in pdf_url.lower():
            slugs.append(slug)
    return slugs


def download_pdf(pdf_url: str, session: requests.Session | None = None) -> bytes:
    s = session or requests
    r = s.get(pdf_url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.content


def save_pdf(pdf_url: str, content: bytes) -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    dest = RAW_DIR / pdf_url.rsplit("/", 1)[-1]
    dest.write_bytes(content)
    return dest


def extract_pdf_text(pdf_bytes: bytes) -> tuple[str, bool]:
    """Devuelve (texto, uso_ocr). Intenta texto nativo primero (pdfplumber);
    si esta vacio (ficha escaneada como imagen), cae a OCR local con
    Tesseract (idioma espanol) sobre cada pagina renderizada a 300dpi."""
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        text = "\n".join(p.extract_text() or "" for p in pdf.pages)
    if text.strip():
        return text, False

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages_text = []
    for page in doc:
        pix = page.get_pixmap(dpi=300)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        pages_text.append(pytesseract.image_to_string(img, lang="spa"))
    doc.close()
    return "\n".join(pages_text), True


def scrape_all() -> list[dict]:
    session = requests.Session()
    results = []
    for slug in discover_product_slugs(session):
        url = product_url(slug)
        html = fetch(url, session=session)
        pdf_url = find_pdf_url(html)
        pdf_bytes = download_pdf(pdf_url, session=session) if pdf_url else None
        if pdf_bytes:
            save_pdf(pdf_url, pdf_bytes)
        results.append({"url": url, "slug": slug, "html": html, "pdf_url": pdf_url, "pdf_bytes": pdf_bytes})
    return results
