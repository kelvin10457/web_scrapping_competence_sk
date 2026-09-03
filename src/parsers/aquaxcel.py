"""Parser de Aquaxcel: la fuente real es un bloque "Portafolio {LINEA}" por
cada linea de producto (Maxima, Rapid, Advance, Active, Adapt Shock, Adapt
Osmo) en la pagina de listado -- una fila HTML (div, no <table>) por SKU con
PRODUCTO/PROTEINA/GRASA/TECNOLOGIA/CALIBRE/ETAPA DE USO/KG. Confirmado
presente en el HTML estatico (sin JS) el 2026-09-01; el hallazgo previo de
"no hay composicion nutricional publicada" (MEMORY.md) estaba desactualizado
-- el parser original solo miraba el primer <table class="table"> (la grilla
comparativa marca x etapa) e ignoraba estos bloques, que no son <table> sino
<div class="row"> de Bootstrap.
"""
from __future__ import annotations

import datetime
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import schema  # noqa: E402

from scrapers.aquaxcel import LISTING_URL  # noqa: E402

_NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")


def _first_number(text: str) -> float | None:
    m = _NUMBER_RE.search(text)
    return float(m.group(0)) if m else None


def _line_descriptions(soup: BeautifulSoup) -> dict[str, str]:
    """Texto de marketing de cada linea de producto (ej. bajo el h2 "Adapt
    Shock": "Para combatir eventos bacterianos extra celulares como la
    vibriosis"), usado para poblar producto_salud por linea. Este texto NO
    esta en los bloques "Portafolio {LINEA}" (esos son solo la tabla de
    SKUs, sin descripcion) sino en secciones de marketing aparte, mas
    arriba en la misma pagina -- hallazgo del usuario 2026-09-02, que
    pregunto por que Aquaxcel quedaba con producto_salud vacio en las 37
    filas: no es que no publiquen esa informacion, es que el parser
    original no la leia. Devuelve {NOMBRE_LINEA_EN_MAYUSCULA: texto},
    para cruzar contra el sufijo de cada heading "Portafolio {LINEA}"."""
    descriptions: dict[str, str] = {}
    for h2 in soup.find_all("h2"):
        heading = h2.get_text(strip=True)
        if not heading or heading.upper().startswith("PORTAFOLIO"):
            continue
        parts = []
        node = h2
        while True:
            node = node.find_next_sibling()
            if node is None or node.name == "h2":
                break
            text = node.get_text(" ", strip=True)
            if text:
                parts.append(text)
        if parts:
            descriptions[heading.upper()] = " ".join(parts)
    return descriptions


def parse_listing(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    fecha = datetime.date.today().isoformat()
    records = []
    linea_descriptions = _line_descriptions(soup)

    for h2 in soup.find_all("h2"):
        heading = h2.get_text(strip=True)
        if not heading.upper().startswith("PORTAFOLIO"):
            continue

        linea = heading.upper().removeprefix("PORTAFOLIO").strip()
        producto_salud = schema.detect_producto_salud(linea_descriptions.get(linea))

        container = h2.parent
        row_divs = container.find_all("div", class_="row", recursive=False)
        if len(row_divs) < 2:
            continue
        data_rows = row_divs[1:]  # row_divs[0] es la fila de encabezados

        for row in data_rows:
            cols = row.find_all("div", recursive=False)
            if len(cols) < 7:
                continue
            values = [c.get_text(strip=True) for c in cols[:7]]
            producto, proteina, grasa, tecnologia, calibre, etapa_txt, kg = values

            record = schema.empty_record("Aquaxcel")
            record["nombre_producto"] = producto
            record["etapa"] = schema.normalize_etapa(etapa_txt)
            record["producto_salud"] = producto_salud
            mm = _first_number(calibre)
            record["tamano_pellet_mm"] = f"{mm:g}" if mm is not None else None
            record["tipo_presentacion"] = tecnologia or None
            kg_val = _first_number(kg)
            record["empaque_kg"] = f"{kg_val:g}" if kg_val is not None else None
            record["proteina_pct"] = _first_number(proteina)
            record["grasa_pct"] = _first_number(grasa)
            record["fuente_url"] = LISTING_URL
            record["fecha_extraccion"] = fecha
            records.append(record)

    records.sort(key=lambda r: (r["nombre_producto"] or "",))
    return records
