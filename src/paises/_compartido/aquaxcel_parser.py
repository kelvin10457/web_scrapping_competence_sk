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

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import schema  # noqa: E402

from paises._compartido.aquaxcel_scraper import LISTING_URL  # noqa: E402

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


def _metric(section, label: str) -> str | None:
    """Valor grande (h3) de la tarjeta cuyo rotulo (strong) es `label`."""
    for h3 in section.find_all("h3"):
        strong = h3.find_next("strong")
        if strong and strong.get_text(strip=True).lower().startswith(label):
            return h3.get_text(strip=True)
    return None


def _h4_value(section, label: str) -> str | None:
    for h4 in section.find_all("h4"):
        b = h4.find("b")
        if b and b.get_text(strip=True).lower().startswith(label):
            return h4.get_text(" ", strip=True).split(":", 1)[-1].strip() or None
    return None


def _parse_cards(soup: BeautifulSoup, fecha: str) -> list[dict]:
    """Layout del listado de Mexico (verificado 2026-10-19): una <section
    id="container-{etapa}"> por producto con h1 = etapa/linea, h2 = nombre,
    h3+strong = proteina/grasa/..., y h4 "Tecnologia:" / "Calibre:". No publica
    empaque (queda None). fuente_url es la URL canonica de la pagina."""
    canonical = soup.find("link", rel="canonical")
    url = canonical["href"] if canonical and canonical.get("href") else LISTING_URL
    linea_descriptions = _line_descriptions(soup)
    records = []
    for section in soup.find_all("section", id=re.compile(r"^container-")):
        h1, h2 = section.find("h1"), section.find("h2")
        if not h1 or not h2:
            continue
        linea = h1.get_text(strip=True)
        record = schema.empty_record("Cargill")
        record["nombre_producto"] = h2.get_text(strip=True)
        record["etapa_competidor"] = schema.normalize_etapa(linea)
        record["producto_salud"] = schema.detect_producto_salud(linea_descriptions.get(linea.upper()))
        mm = _first_number(_h4_value(section, "calibre") or "")
        record["tamano_pellet_mm"] = f"{mm:g}" if mm is not None else None
        record["tipo_presentacion"] = _h4_value(section, "tecnolog")
        record["proteina_pct"] = _first_number(_metric(section, "prote") or "")
        record["fuente_url"] = url
        record["fecha_extraccion"] = fecha
        records.append(record)
    records.sort(key=lambda r: (r["nombre_producto"] or "",))
    return records


def parse_listing(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    fecha = datetime.date.today().isoformat()
    records = []
    if not any(h2.get_text(strip=True).upper().startswith("PORTAFOLIO") for h2 in soup.find_all("h2")):
        return _parse_cards(soup, fecha)
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
            producto, proteina, _grasa, tecnologia, calibre, etapa_txt, kg = values

            record = schema.empty_record("Cargill")
            record["nombre_producto"] = producto
            record["etapa_competidor"] = schema.normalize_etapa(etapa_txt)
            record["producto_salud"] = producto_salud
            mm = _first_number(calibre)
            record["tamano_pellet_mm"] = f"{mm:g}" if mm is not None else None
            record["tipo_presentacion"] = tecnologia or None
            kg_val = _first_number(kg)
            record["empaque_kg"] = f"{kg_val:g}" if kg_val is not None else None
            record["proteina_pct"] = _first_number(proteina)
            record["fuente_url"] = LISTING_URL
            record["fecha_extraccion"] = fecha
            records.append(record)

    records.sort(key=lambda r: (r["nombre_producto"] or "",))
    return records
