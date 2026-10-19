"""Parser de Api-Aba (Mexico). Publica nombre (con el saco en kg), analisis
garantizado (proteina/humedad/fibra) y, en Raceways, el tamano de micropellet.
No publica etapa normalizable ni tecnologia: quedan en None.

Si el % de proteina del titulo ("Dorado 35%") contradice el analisis
garantizado de la misma pagina (ocurre hoy en Dorado 35%, que muestra 40%), no
se elige ninguno: proteina_pct queda en None."""
from __future__ import annotations

import datetime
import html as htmllib
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import schema  # noqa: E402


def _lines(soup: BeautifulSoup) -> list[str]:
    text = soup.get_text("\n")
    return [htmllib.unescape(l).replace("\xa0", " ").strip() for l in text.splitlines() if l.strip()]


def _title(soup: BeautifulSoup) -> str | None:
    h1 = soup.find("h1")
    if not h1:
        return None
    return re.sub(r"[\s®™]+", " ", htmllib.unescape(h1.get_text(" ", strip=True))).strip() or None


def _guaranteed_protein(lines: list[str]) -> float | None:
    for i, line in enumerate(lines):
        if re.fullmatch(r"prote[ií]na", line, re.I) and i > 0:
            m = re.fullmatch(r"(\d+(?:\.\d+)?)\s*%", lines[i - 1])
            if m:
                return float(m.group(1))
    return None


def _micropellet(text: str) -> str | None:
    """Tamanos publicados tras "micropellet de ..." (ej. "1.8 y 2.0 mm y pellet
    de 2.32 mm", "0.8 y 1.1 de tamano"): se reporta el rango min-max de todos
    los numeros de esa frase, que corta en "para"/"de tamano"."""
    m = re.search(r"micro\s*pellet\s+de\s+(.{0,80})", text, re.I)
    if not m:
        return None
    frase = re.split(r"para|de\s+tama", m.group(1), maxsplit=1, flags=re.I)[0]
    nums = [float(n) for n in re.findall(r"\d+(?:\.\d+)?", frase)]
    if not nums:
        return None
    lo, hi = min(nums), max(nums)
    return f"{lo:g}" if lo == hi else f"{lo:g}-{hi:g}"


def parse_product(url: str, html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    nombre = _title(soup)
    if not nombre:
        return []
    lines = _lines(soup)
    proteina = _guaranteed_protein(lines)
    in_title = re.search(r"(\d+(?:\.\d+)?)\s*%", nombre)
    if in_title and proteina is not None and float(in_title.group(1)) != proteina:
        proteina = None
    kg = re.search(r"(\d+(?:\.\d+)?)\s*kg", nombre, re.I)

    record = schema.empty_record("Api-Aba")
    record["nombre_producto"] = nombre
    record["tamano_pellet_mm"] = _micropellet(" ".join(lines))
    record["empaque_kg"] = f"{float(kg.group(1)):g}" if kg else None
    record["proteina_pct"] = proteina
    record["fuente_url"] = url
    record["fecha_extraccion"] = datetime.date.today().isoformat()
    return [record]


def parse_listing(items: list[dict]) -> list[dict]:
    records = []
    for item in items:
        records.extend(parse_product(item["url"], item["html"]))
    return records
