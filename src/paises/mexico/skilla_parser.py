"""Parser de Skilla (BioBlue, Mexico), R7.8. Pagina bioblue.com/skilla/.

Cada etapa del portafolio es un bloque: rotulo (<p>Inicio</p>), titulo con los
codigos (<h3>4008 – 3505</h3>) y una foto por codigo, en el mismo orden, cuyo
pie dice "diametro x largo mm" (leido por OCR en el scraper). Una fila por
(codigo, diametro); las etapas de los bloques donde aparece se suman."""
from __future__ import annotations

import datetime
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import schema  # noqa: E402

EMPRESA = "Skilla"
_CODIGOS_RE = re.compile(r"^\d{4}(?:\s*[–-]\s*\d{4})*$")
# Solo fotos de producto (nombre con el codigo); el scraper usa el mismo filtro.
FOTO_RE = re.compile(r'src="(https://bioblue\.com/wp-content/uploads/[^"?]*Skilla[-_]\d{4}[^"?]*\.png)"')
# El pie completo, sin numeros malformados: "1.5.5 x 2.5 mm" o "1/2 x 2.5 mm" no valen (revision Codex).
_PIE_RE = re.compile(r"\s*(\d+(?:[.,]\d+)?)\s*[xX×]\s*\d+(?:[.,]\d+)?\s*mm\.?\s*", re.I)


def _fmt(x: float) -> str:
    return f"{x:g}"


def diametro(texto: str | None) -> str | None:
    """"1.5 x 2.5 mm" -> "1.5" (vale el diametro). Sin patron, vacio."""
    m = _PIE_RE.fullmatch(texto or "")
    return _fmt(float(m.group(1).replace(",", "."))) if m else None


def _bloques(html: str) -> list[tuple[str, list[str], list[str]]]:
    """[(rotulo, codigos, urls_de_foto)] en el orden de la pagina."""
    soup = BeautifulSoup(html, "lxml")
    bloques = []
    for h3 in soup.find_all("h3"):
        titulo = " ".join(h3.get_text(" ").split())
        if not _CODIGOS_RE.match(titulo):
            continue
        codigos = re.findall(r"\d{4}", titulo)
        rotulo = h3.find_previous("p")
        contenedor = h3.find_parent("div").find_next_sibling("div")
        fotos = list(dict.fromkeys(FOTO_RE.findall(str(contenedor)))) if contenedor else []
        bloques.append((" ".join(rotulo.get_text(" ").split()) if rotulo else "", codigos, fotos))
    return bloques


def parse_page(url: str, html: str, ocr_por_url: dict[str, str]) -> list[dict]:
    extruido = "alimento extruido" in BeautifulSoup(html, "lxml").get_text(" ").lower()
    filas: dict[tuple[str, str | None], set[str]] = {}
    for rotulo, codigos, fotos in _bloques(html):
        # Sin correspondencia foto-codigo no se adivina: el producto queda, sin tamano.
        if len(fotos) != len(codigos):
            fotos = [None] * len(codigos)
        for codigo, foto in zip(codigos, fotos):
            clave = (codigo, diametro(ocr_por_url.get(foto)) if foto else None)
            filas.setdefault(clave, set()).update(schema.detectar_etapas(rotulo))
    hoy = datetime.date.today().isoformat()
    records = []
    for (codigo, tamano), etapas in filas.items():
        record = schema.empty_record(EMPRESA)
        record["nombre_producto"] = f"SKILLA {codigo}"
        record["tamano_pellet_mm"] = tamano
        record["tipo_presentacion"] = schema.normalize_presentacion("Extruido") if extruido else None
        record["fuente_url"] = url
        record["fecha_extraccion"] = hoy
        record["_etapas_detectadas"] = True
        record.update(schema.columnas_etapa(etapas))
        records.append(record)
    return records
