"""Parser de Nutrimar (Mexico). Pipeline PARCIAL: la fuente solo publica el
nombre del producto y texto de marketing, asi que solo se llenan empresa,
nombre_producto, fuente_url y fecha_extraccion; todo lo demas queda en None
(mismo criterio que BioMar en PLAN.md)."""
from __future__ import annotations

import datetime
import html as htmllib
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import schema  # noqa: E402

_TITLE_RE = re.compile(r"<title>(.*?)</title>", re.S | re.I)


def parse_product(url: str, html: str) -> list[dict]:
    m = _TITLE_RE.search(html)
    if not m:
        return []
    nombre = htmllib.unescape(m.group(1)).replace("\xa0", " ")
    nombre = re.sub(r"\s*\|\s*Nutrimar\s*$", "", nombre, flags=re.I).strip()
    if not nombre:
        return []
    record = schema.empty_record("Nutrimar")
    record["nombre_producto"] = nombre
    record["fuente_url"] = url
    record["fecha_extraccion"] = datetime.date.today().isoformat()
    return [record]


def parse_listing(items: list[dict]) -> list[dict]:
    records = []
    for item in items:
        records.extend(parse_product(item["url"], item["html"]))
    return records
