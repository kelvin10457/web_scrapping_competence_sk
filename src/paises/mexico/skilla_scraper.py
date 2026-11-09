"""Scraper de Skilla (BioBlue / Grupo NU3, Mexico): bioblue.com/skilla/.
Verificado 2026-11-09 (R7.8). El texto solo nombra los productos y las etapas;
el tamano esta en el pie de la foto de cada etapa ("1.5 x 2.5 mm") y se lee con
OCR local (Tesseract, R10.1). Las imagenes reales estan en <noscript> (lazy load)."""
from __future__ import annotations

import io

import pytesseract
import requests
from PIL import Image

import netutil
import ocr
from paises.mexico import skilla_parser

PAGE_URL = "https://bioblue.com/skilla/"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                         "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"}

ocr.configurar()  # Tesseract del .exe, de Windows o del PATH (R10.1)


def _get(url: str, session) -> requests.Response:
    r = netutil.get(session, url, headers=HEADERS, timeout=60)
    r.raise_for_status()
    return r


def discover_image_urls(page_html: str) -> list[str]:
    """Fotos de producto por etapa (nombre con el codigo SKILLA), sin repetir."""
    return list(dict.fromkeys(skilla_parser.FOTO_RE.findall(page_html)))


def leer_pie(image_bytes: bytes) -> str:
    """OCR del pie de la foto. El PNG es transparente: sin aplanarlo sobre
    blanco Tesseract no lee nada; se recorta el 15 % inferior y se agranda x3."""
    im = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    fondo = Image.new("RGBA", im.size, "white")
    fondo.alpha_composite(im)
    gris = fondo.convert("L")
    w, h = gris.size
    pie = gris.crop((0, int(h * 0.85), w, h))
    pie = pie.resize((pie.width * 3, pie.height * 3))
    return pytesseract.image_to_string(pie, lang="spa", config="--psm 7").strip()


def scrape_all() -> list[dict]:
    """[{url, html, ocr: {url_imagen: texto}}]."""
    session = requests.Session()
    html = _get(PAGE_URL, session).text
    textos = {u: leer_pie(_get(u, session).content) for u in discover_image_urls(html)}
    return [{"url": PAGE_URL, "html": html, "ocr": textos}]
