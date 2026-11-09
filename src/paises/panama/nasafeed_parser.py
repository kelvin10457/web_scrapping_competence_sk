"""Parser de la ficha Linea Premium de Aquanasa (NasaFeed, Panama), R8.10.

Una tabla de analisis con una columna por formula (25/30/35 % de proteina) y
dos diametros (1.4 y 2.4 mm) sin decir cual va con cual: una fila por
proteina y tamano vacio (decision del usuario 2026-11-09)."""
from __future__ import annotations

import datetime
import io
import re
import sys
from pathlib import Path

import pdfplumber

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import schema  # noqa: E402

EMPRESA = "NasaFeed"
_PROTEINA_RE = re.compile(r"Prote[ií]na\s+Cruda\s*\(m[ií]nima\)\s+((?:\d+(?:[.,]\d+)?\s*)+)", re.I)
_KG_RE = re.compile(r"\(\s*(\d+(?:[.,]\d+)?)\s*Kg\s*\)", re.I)
_DESCRIPCION_RE = re.compile(r"DESCRIPCI[OÓ]N DEL PRODUCTO\s*:?\s*(.*?)(?:\n[A-ZÁÉÍÓÚ ]{6,}:|\Z)", re.S)


def _texto(pdf_bytes: bytes) -> str:
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        return "\n".join(p.extract_text() or "" for p in pdf.pages)


def parse_pdf(url: str, pdf_bytes: bytes) -> list[dict]:
    texto = _texto(pdf_bytes)
    m = _PROTEINA_RE.search(texto)
    proteinas = [schema.normalize_proteina(x) for x in m.group(1).split()] if m else []
    mk = _KG_RE.search(texto)
    md = _DESCRIPCION_RE.search(texto)
    descripcion = md.group(1) if md else ""
    peletizado = re.search(r"pel+e?tizad", descripcion, re.I)
    etapas = schema.detectar_etapas(descripcion)
    hoy = datetime.date.today().isoformat()
    records = []
    for p in proteinas:
        if p is None:
            continue
        record = schema.empty_record(EMPRESA)
        record["nombre_producto"] = f"Aquanasa Línea Premium {p:g}%"
        record["proteina_pct"] = p
        record["empaque_kg"] = f"{float(mk.group(1).replace(',', '.')):g}" if mk else None
        record["tipo_presentacion"] = schema.normalize_presentacion("Pelletizado") if peletizado else None
        record["fuente_url"] = url
        record["fecha_extraccion"] = hoy
        record["_etapas_detectadas"] = True
        record.update(schema.columnas_etapa(etapas))
        records.append(record)
    return records
