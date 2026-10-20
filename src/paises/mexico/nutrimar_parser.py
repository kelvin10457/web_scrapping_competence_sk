"""Parser de Nutrimar (Mexico). Nombre desde el <title> de la pagina y, si la
pagina enlaza una ficha tecnica (PDF con texto, o imagen leida por OCR; ver
nutrimar_scraper), proteina / calibre / empaque desde esa ficha (RONDA2 R2.4).

- empresa: "Zeigler" para lo que Nutrimar distribuye, "Nutrimar" para su linea
  propia; fuente_url es siempre la pagina de Nutrimar.
- proteina: "Proteina (cruda) Minimo 35,0%". Si la ficha publica varias
  separadas por "/" ("35.0/30.0%") sale una fila por SKU ("Semi-intensivo 35%").
  En fichas de producto liquido ("11,0% 36,7%": base humeda y seca) se toma la
  primera (tal como se vende).
- calibre: rango min-max de todos los "N mm" y "A-B micrones" de la ficha.
- Si el valor viene de OCR y es dudoso (proteina fuera de 20-60 %, calibre
  fuera de 0.1-4 mm) queda en None y se registra `ocr_fuera_de_rango`."""
from __future__ import annotations

import datetime
import html as htmllib
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import schema  # noqa: E402

_TITLE_RE = re.compile(r"<title>(.*?)</title>", re.S | re.I)
_NUM = r"\d+(?:[.,]\d+)?"
# "Proteina cruda Minimo 40,0%", "Proteina cruda min 12,0%", "Proteina cruda  Min50,0%"
_PROT_RE = re.compile(rf"prote[ií]na(?:\s+cruda)?\W+m[ií]n(?:imo)?\.?\W*({_NUM}(?:\s*/\s*{_NUM})*)\s*%", re.I)
# "N mm", salvo el largo del pellet ("3.5 mm de largo").
_MM_RE = re.compile(rf"({_NUM})\s*mm\b(?!\s*de\s+largo)", re.I)
_MICRAS_RE = re.compile(rf"({_NUM})\s*-\s*({_NUM})\s*micr", re.I)
_KG_RE = re.compile(rf"({_NUM})\s*kg\b(?!\s*/)", re.I)

PROTEINA_OCR_RANGO = (20.0, 60.0)
CALIBRE_OCR_RANGO = (0.1, 4.0)


def _num(text: str) -> float:
    return float(text.replace(",", "."))


def _fmt(x: float) -> str:
    return f"{x:g}"


def proteinas_de_ficha(texto: str) -> list[float]:
    m = _PROT_RE.search(texto or "")
    return [_num(n) for n in re.split(r"\s*/\s*", m.group(1))] if m else []


def calibres_mm_de_ficha(texto: str) -> list[float]:
    texto = texto or ""
    vals = [_num(n) for n in _MM_RE.findall(texto)]
    for lo, hi in _MICRAS_RE.findall(texto):
        vals += [_num(lo) / 1000, _num(hi) / 1000]
    return vals


def empaque_de_ficha(texto: str) -> str | None:
    m = _KG_RE.search(texto or "")
    return _fmt(_num(m.group(1))) if m else None


def _nombre(html: str) -> str | None:
    m = _TITLE_RE.search(html)
    if not m:
        return None
    nombre = htmllib.unescape(m.group(1)).replace("\xa0", " ")
    return re.sub(r"\s*\|\s*Nutrimar\s*$", "", nombre, flags=re.I).strip() or None


def parse_product(url: str, html: str, marca: str = "Nutrimar", ficha_texto: str | None = None,
                  ficha_ocr: bool = False) -> list[dict]:
    nombre = _nombre(html)
    if not nombre:
        return []
    record = schema.empty_record(marca)
    record["nombre_producto"] = nombre
    record["fuente_url"] = url
    record["fecha_extraccion"] = datetime.date.today().isoformat()
    if not ficha_texto:
        return [record]

    record["empaque_kg"] = empaque_de_ficha(ficha_texto)
    calibres = calibres_mm_de_ficha(ficha_texto)
    if calibres:
        lo, hi = min(calibres), max(calibres)
        if ficha_ocr and not (CALIBRE_OCR_RANGO[0] <= lo and hi <= CALIBRE_OCR_RANGO[1]):
            schema.registrar_conflicto(record, "tamano_pellet_mm", None, "ocr_fuera_de_rango",
                                       [(c, "ocr") for c in calibres])
        else:
            record["tamano_pellet_mm"] = _fmt(lo) if lo == hi else f"{_fmt(lo)}-{_fmt(hi)}"

    proteinas = proteinas_de_ficha(ficha_texto)
    if ficha_ocr and any(not (PROTEINA_OCR_RANGO[0] <= p <= PROTEINA_OCR_RANGO[1]) for p in proteinas):
        schema.registrar_conflicto(record, "proteina_pct", None, "ocr_fuera_de_rango",
                                   [(p, "ocr") for p in proteinas])
        return [record]
    if len(proteinas) <= 1:
        record["proteina_pct"] = proteinas[0] if proteinas else None
        return [record]
    filas = []
    for p in proteinas:
        fila = dict(record, _conflictos=list(record.get("_conflictos", [])))
        fila["proteina_pct"] = p
        fila["nombre_producto"] = f"{nombre} {_fmt(p)}%"
        filas.append(fila)
    return filas


def parse_listing(items: list[dict]) -> list[dict]:
    records = []
    for item in items:
        records.extend(parse_product(item["url"], item["html"], item.get("marca", "Nutrimar"),
                                     item.get("ficha_texto"), item.get("ficha_ocr", False)))
    return records
