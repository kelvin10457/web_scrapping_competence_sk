"""Scraper de El Pedregal Silver Cup (Mexico): el-pedregal.com/alimento/crustaceos.
Verificado 2026-11-09 (R7.5). El catalogo actual esta en las imagenes de los
modales de la pagina principal (crustaceos-info-N.png) y se lee con OCR local.
De las tablas HTML (?t=...) solo se usa ?t=mp (migajas post-larva), que no esta
en las imagenes; ?t=ep quedo reemplazada por las imagenes y ?t=p / ?t=e estan
marcadas "(NO)" y no se enlazan desde el sitio (decision del usuario)."""
from __future__ import annotations

import io
import re

import pytesseract
import requests
from PIL import Image

import netutil
import ocr

BASE_URL = "https://el-pedregal.com"
PAGE_URL = f"{BASE_URL}/alimento/crustaceos"
TABLE_URLS = [f"{PAGE_URL}?t=mp"]
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                         "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"}
_IMG_RE = re.compile(r'src="(https://el-pedregal\.com/img/crustaceos-info-\d+\.png)"')

ocr.configurar()  # Tesseract del .exe, de Windows o del PATH (R10.1)


def _get(url: str, session) -> requests.Response:
    r = netutil.get(session, url, headers=HEADERS, timeout=60)
    r.raise_for_status()
    return r


def discover_image_urls(page_html: str) -> list[str]:
    """Imagenes de los modales, en el orden del HTML y sin repetir."""
    return list(dict.fromkeys(_IMG_RE.findall(page_html)))


def ocr(image_bytes: bytes) -> str:
    return pytesseract.image_to_string(Image.open(io.BytesIO(image_bytes)), lang="spa")


def scrape_all() -> list[dict]:
    """[{url, ocr}] por imagen y [{url, html}] por tabla."""
    session = requests.Session()
    items = []
    for url in discover_image_urls(_get(PAGE_URL, session).text):
        items.append({"url": url, "ocr": ocr(_get(url, session).content)})
    for url in TABLE_URLS:
        items.append({"url": url, "html": _get(url, session).text})
    return items
