"""Scraper de Nutrimar (Grupo Acuicola Mexicano, Mexico). La pagina
https://www.grupoacuicolamexicano.com.mx/nutrimar enlaza cada producto en
https://www.nutrimar.mx/<slug> (Wix, HTML renderizado en servidor, robots.txt
permite todo; verificado 2026-10-19).

Fichas tecnicas (RONDA2 R2.4, revisado 2026-10-19): la mayoria de las paginas
de producto enlazan un PDF con texto en /_files/ugd/<id>.pdf ("Ficha Tecnica")
y se lee con pdfplumber; "Extensivo" publica la tabla de analisis como imagen
(static.wixstatic.com/media, alt "Tabla de Analisis...") y se lee con el mismo
OCR de HAID (`haid_scraper.ocr_image`). Sin Playwright.

Marca: los productos enlazados desde las categorias /*-zeigler son de Zeigler
(Nutrimar los distribuye); el resto (linea "Engorda") es propio de Nutrimar."""
from __future__ import annotations

import io
import re
import urllib.parse
from pathlib import Path

import requests
from PIL import Image, ImageOps

import netutil
from paises.ecuador import haid_scraper

LISTING_URL = "https://www.grupoacuicolamexicano.com.mx/nutrimar"
BASE_URL = "https://www.nutrimar.mx"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; competence-scraper/1.0)"}
RAW_DIR = Path(__file__).resolve().parents[3] / "data" / "raw" / "nutrimar"
_LINK_RE = re.compile(r"https://www\.nutrimar\.mx/([A-Za-z0-9%\-]+)")
_PDF_RE = re.compile(r"https://www\.nutrimar\.mx/_files/ugd/[0-9a-f_]+\.pdf")
# Wix: https://static.wixstatic.com/media/<id>~mv2.png/v1/fill/.../<nombre original>.png
# El nombre original de la imagen de la ficha dice "Tabla de Analisis ...".
_TABLA_IMG_RE = re.compile(
    r'(https://static\.wixstatic\.com/media/[^/"\s]+)/v1/[^"\s]*?(?:tabla|an%C3%A1lisis|analisis)', re.I)

# Paginas de categoria: definen la marca de los productos que enlazan.
CATEGORIAS = {
    "engorda-nutrimar": "Nutrimar", "larvario-zeigler": "Zeigler", "maduración-zeigler": "Zeigler",
    "maternidad-zeigler": "Zeigler", "probioticos-zeigler": "Zeigler",
}

# Enlaces del listado que NO son alimento formulado para camaron: alimento
# fresco/congelado, aditivos/probioticos y paginas de categoria.
NON_FEED_SLUGS = {
    "alimento-fresco-meggasuply", "biomasa-de-artemia", "calamar-cortado", "copepodos", "krill",
    "poliquetos", "remediate", "rescue", "probioticos-zeigler", "engorda-nutrimar",
    "larvario-zeigler", "maternidad-zeigler",
}


def fetch(url: str, session: requests.Session | None = None) -> str:
    s = session or requests
    r = netutil.get(s, url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.text


def fetch_bytes(url: str, session: requests.Session | None = None) -> bytes:
    s = session or requests
    r = netutil.get(s, url, headers=HEADERS, timeout=60)
    r.raise_for_status()
    return r.content


def discover_product_urls(listing_html: str) -> list[str]:
    slugs = sorted(set(_LINK_RE.findall(listing_html)))
    return [f"{BASE_URL}/{s}" for s in slugs
            if s not in NON_FEED_SLUGS and "%" not in s and not s.endswith("-zeigler")
            and not s.startswith("copia-de")]


def marcas_por_slug(paginas_categoria: dict[str, str]) -> dict[str, str]:
    """{slug: marca} a partir del HTML de cada pagina de categoria."""
    marcas = {}
    for categoria, html in paginas_categoria.items():
        for slug in set(_LINK_RE.findall(html)):
            if urllib.parse.unquote(slug) not in CATEGORIAS:
                marcas.setdefault(slug, CATEGORIAS[categoria])
    return marcas


def find_ficha(product_html: str) -> tuple[str, str] | None:
    """("pdf", url) o ("imagen", url original sin transformaciones de Wix)."""
    m = _PDF_RE.search(product_html)
    if m:
        return "pdf", m.group(0)
    m = _TABLA_IMG_RE.search(product_html)
    if m:
        return "imagen", m.group(1)
    return None


def preparar_para_ocr(image_bytes: bytes) -> bytes:
    """Las tablas de Wix son texto claro sobre fondo azul con transparencia:
    se aplana sobre blanco, escala de grises x2 y umbral 160 (sin esto
    Tesseract no lee la fila de proteina)."""
    im = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    fondo = Image.new("RGB", im.size, "white")
    fondo.paste(im, mask=im.split()[3])
    gris = ImageOps.grayscale(fondo).resize((im.width * 2, im.height * 2))
    out = io.BytesIO()
    gris.point(lambda p: 255 if p > 160 else 0).save(out, "PNG")
    return out.getvalue()


def leer_ficha(tipo: str, url: str, session=None) -> tuple[str, bool]:
    """(texto, uso_ocr). Guarda el archivo original en data/raw/nutrimar/."""
    contenido = fetch_bytes(url, session=session)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    (RAW_DIR / url.rsplit("/", 1)[-1]).write_bytes(contenido)
    if tipo == "pdf":
        return haid_scraper.extract_pdf_text(contenido)
    return haid_scraper.ocr_image(preparar_para_ocr(contenido)), True


def scrape_all() -> list[dict]:
    session = requests.Session()
    categorias = {c: fetch(f"{BASE_URL}/{urllib.parse.quote(c)}", session=session) for c in CATEGORIAS}
    marcas = marcas_por_slug(categorias)
    items = []
    for url in discover_product_urls(fetch(LISTING_URL, session=session)):
        html = fetch(url, session=session)
        item = {"url": url, "html": html, "marca": marcas.get(url.rsplit("/", 1)[-1], "Nutrimar"),
                "ficha_url": None, "ficha_texto": None, "ficha_ocr": False}
        ficha = find_ficha(html)
        if ficha:
            item["ficha_url"] = ficha[1]
            item["ficha_texto"], item["ficha_ocr"] = leer_ficha(*ficha, session=session)
        items.append(item)
    return items
