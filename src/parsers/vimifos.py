"""Parser de Vimifos (Mexico). Cada pagina de linea trae una <table> cuya
primera fila es [NOMBRE DE LINEA, columna1, columna2, ...] y cuyas filas
siguientes se rotulan PRESENTACION / % PROTEINA / TAMANO PARTICULA / peso
del camaron. Cada columna es un producto. Solo se toma lo que el sitio
publica: celdas con varios valores (ej. "30%, 35%, 40%") dejan proteina_pct
en None en vez de elegir uno; "migaja"/"micropelet" no son un valor valido de
tipo_presentacion y quedan en None."""
from __future__ import annotations

import datetime
import html as htmllib
import re
import sys
import unicodedata
from pathlib import Path

from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import schema  # noqa: E402

_NUM = r"\d+(?:\.\d+)?"


def _fold(text: str) -> str:
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()


def _row_kind(label: str) -> str | None:
    f = _fold(label)
    if f.startswith("presentaci"):
        return "presentacion"
    if "proteina" in f:
        return "proteina"
    if f.startswith("tama"):
        return "tamano"
    if f.startswith(("peso", "pero", "kilos")):
        return "peso"
    return None


def _parse_proteina(text: str) -> float | None:
    nums = re.findall(rf"({_NUM})\s*%", text)
    return float(nums[0]) if len(nums) == 1 else None


def _fmt(x: float) -> str:
    return f"{x:g}"


def _parse_tamano(text: str) -> str | None:
    t = _fold(text)
    micras = "micra" in t
    nums = [float(n) for n in re.findall(_NUM, t)]
    if not nums or len(nums) > 2:
        return None
    if micras:
        nums = [n / 1000 for n in nums]
    return "-".join(_fmt(n) for n in nums)


def _parse_empaque(text: str) -> str | None:
    m = re.search(rf"({_NUM})\s*kg", text, re.I)
    return _fmt(float(m.group(1))) if m else None


def parse_product(url: str, html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    fecha = datetime.date.today().isoformat()
    records = []
    for table in soup.find_all("table"):
        rows = [
            [htmllib.unescape(td.get_text(" ", strip=True)).replace("\xa0", " ").strip() for td in tr.find_all(["td", "th"])]
            for tr in table.find_all("tr")
        ]
        if len(rows) < 2 or len(rows[0]) < 2 or not any(_row_kind(r[0]) for r in rows[1:] if r):
            continue
        linea = rows[0][0].title()
        by_kind = {_row_kind(r[0]): r[1:] for r in rows[1:] if r and _row_kind(r[0])}
        for j, header in enumerate(rows[0][1:]):
            def cell(kind):
                vals = by_kind.get(kind, [])
                return vals[j] if j < len(vals) else ""

            record = schema.empty_record("Vimifos")
            same_line = _fold(header).startswith(_fold(rows[0][0]))
            record["nombre_producto"] = header.title() if same_line else linea
            record["etapa_competidor"] = schema.normalize_etapa(header) or schema.normalize_etapa(cell("peso"))
            record["tamano_pellet_mm"] = _parse_tamano(cell("tamano"))
            record["tipo_presentacion"] = schema.detect_tecnologia(cell("presentacion"))
            record["empaque_kg"] = _parse_empaque(cell("presentacion"))
            record["proteina_pct"] = _parse_proteina(cell("proteina"))
            record["fuente_url"] = url
            record["fecha_extraccion"] = fecha
            records.append(record)
    return records


def parse_listing(items: list[dict]) -> list[dict]:
    records = []
    for item in items:
        records.extend(parse_product(item["url"], item["html"]))
    return records
