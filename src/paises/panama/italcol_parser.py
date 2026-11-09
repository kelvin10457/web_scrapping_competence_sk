"""Parser de Italcol (Colombia, fuente de Panama por decision del usuario
2026-11-09), R8.11. Ficha WooCommerce: descripcion en <p> y composicion
garantizada en listas <ul><li>PARAMETRO</li><li>VALOR</li></ul>."""
from __future__ import annotations

import datetime
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import schema  # noqa: E402

EMPRESA = "Italcol"


def _nombre(soup) -> str | None:
    """`.product_title` de WooCommerce; respaldo: <title> del <head> sin el
    sufijo del sitio (nunca un <title> de un SVG; revision Codex)."""
    h = soup.select_one(".product_title")
    if h is None and soup.head is not None and soup.head.title is not None:
        h = soup.head.title
    if h is None:
        return None
    texto = " ".join(h.get_text(" ").split())
    return re.split(r"\s+[-|–]\s+Italcol\b", texto)[0].strip() or None


def parse_page(url: str, html: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    marca = soup.find(string=re.compile(r"COMPOSICI[OÓ]N GARANTIZADA", re.I))
    nombre = _nombre(soup)
    if marca is None or not nombre:
        return []
    # El contenedor es el primer ancestro que tiene la descripcion y las listas
    # de composicion, no el div inmediato (revision Codex).
    bloque = next((d for d in marca.find_parents("div") if d.find("p") and d.find("ul")), None)
    if bloque is None:
        return []
    descripcion = " ".join(p.get_text(" ") for p in bloque.find_all("p"))
    proteina = None
    for ul in bloque.find_all("ul"):
        items = [" ".join(li.get_text(" ").split()) for li in ul.find_all("li")]
        if len(items) == 2 and re.match(r"PROTE[IÍ]NA", items[0], re.I):
            proteina = schema.normalize_proteina(items[1])
    record = schema.empty_record(EMPRESA)
    record["nombre_producto"] = nombre
    record["proteina_pct"] = proteina
    record["fuente_url"] = url
    record["fecha_extraccion"] = datetime.date.today().isoformat()
    record["_etapas_detectadas"] = True
    record.update(schema.columnas_etapa(schema.detectar_etapas(descripcion)))
    return [record]
