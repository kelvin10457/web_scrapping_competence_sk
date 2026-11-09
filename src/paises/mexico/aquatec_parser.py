"""Parser de AQUATEC (Mexico), R7.6. Pagina nutrimentos.com.mx/acuicultura_1.

Arriba, 3 fichas completas ("LÍNEA PERFORMANCE/HD/ESTÁNDAR" + titulo +
analisis garantizado + indicaciones + saco). Abajo, despues de "Mas...", una
columna por linea con variantes cuyo texto es la plantilla del editor web.
Una fila por SKU (linea, nombre). La ficha solo completa la SKU de su misma
linea y mismo nombre: las variantes no heredan nada (decision del usuario)."""
from __future__ import annotations

import datetime
import re
import sys
import unicodedata
from pathlib import Path

from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import schema  # noqa: E402

EMPRESA = "AQUATEC"
_BLOQUES = ["p", "div", "li", "ul", "ol", "h1", "h2", "h3", "h4", "h5", "h6",
            "td", "th", "tr", "table", "section", "article", "header", "footer"]
_LINEAS = {"PERFORMANCE": "Performance", "HD": "HD", "ESTANDAR": "Estándar"}
_FICHA_RE = re.compile(r"^LINEA (PERFORMANCE|HD|ESTANDAR)$")
_COLUMNA_RE = re.compile(r"^(?:LINEA )?(PERFORMANCE|HD|ESTANDAR)$")
_SKU_RE = re.compile(r"^AQUATEC\s+\d+(?:[.,]\d+)?\s*%")
_PCT_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*%")
_MM_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*mm\b", re.I)
_PROT_ANALISIS_RE = re.compile(r"Prote[ií]na\s+cruda\s+M[ií]n\.?\s+(\d+(?:[.,]\d+)?)\s*%", re.I)
_SACO_RE = re.compile(r"Saco\s+de\s+(\d+(?:[.,]\d+)?)\s*kg", re.I)
_INDICACIONES_RE = re.compile(r"INDICACIONES\s*(.*?)(?:\n\s*DOSIS|$)", re.S)


def _clave(texto: str) -> str:
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return " ".join(t.upper().split())


def _num(s: str) -> float:
    return float(s.replace(",", "."))


def _fmt(x: float) -> str:
    return f"{x:g}"


def _lineas_visibles(html: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    # Solo los elementos de bloque cortan linea: un <span> dentro de un titulo
    # no lo parte (revision Codex R7.6).
    for tag in soup.find_all(_BLOQUES):
        tag.insert_before("\n")
        tag.insert_after("\n")
    for br in soup.find_all("br"):
        br.replace_with("\n")
    return [" ".join(ln.split()) for ln in soup.get_text("").splitlines() if ln.strip()]


def _secciones(lineas: list[str]) -> tuple[list[tuple[str, str, str]], list[tuple[str, str]]]:
    """(fichas [(linea, titulo, texto)], variantes [(linea, nombre)])."""
    fichas, variantes = [], []
    linea, en_columnas = None, False
    for ln in lineas:
        k = _clave(ln)
        if k == "MAS...":
            en_columnas, linea = True, None
            continue
        if not en_columnas:
            m = _FICHA_RE.match(k)
            if m:
                linea = _LINEAS[m.group(1)]
                fichas.append([linea, None, []])
            elif fichas and fichas[-1][1] is None and _SKU_RE.match(k):
                fichas[-1][1] = " ".join(ln.split())
            elif fichas and fichas[-1][1]:
                fichas[-1][2].append(ln)
        else:
            m = _COLUMNA_RE.match(k)
            if m:
                linea = _LINEAS[m.group(1)]
            elif linea and _SKU_RE.match(k):
                variantes.append((linea, " ".join(ln.split())))
    return [(l, t, "\n".join(x)) for l, t, x in fichas if t], variantes


def _record(url: str, linea: str, nombre: str) -> dict:
    record = schema.empty_record(EMPRESA)
    record["nombre_producto"] = f"{nombre} (Línea {linea})"
    record["fuente_url"] = url
    record["fecha_extraccion"] = datetime.date.today().isoformat()
    record["_etapas_detectadas"] = True
    m = _MM_RE.search(nombre)
    record["tamano_pellet_mm"] = _fmt(_num(m.group(1))) if m else None
    record["tipo_presentacion"] = schema.normalize_presentacion("Pellet") if "PELLET" in _clave(nombre) else None
    return record


def parse_page(url: str, html: str) -> list[dict]:
    fichas, variantes = _secciones(_lineas_visibles(html))
    skus = list(dict.fromkeys(variantes + [(l, t) for l, t, _ in fichas]))
    por_sku = {(l, _clave(t)): texto for l, t, texto in fichas}
    records = []
    for linea, nombre in skus:
        record = _record(url, linea, nombre)
        m = _PCT_RE.search(nombre)
        titulo = schema.normalize_proteina(_num(m.group(1))) if m else None
        ficha = por_sku.get((linea, _clave(nombre)))
        if ficha is None:
            record["proteina_pct"] = titulo
            record.update(schema.columnas_etapa(set()))
        else:
            ma = _PROT_ANALISIS_RE.search(ficha)
            analisis = schema.normalize_proteina(_num(ma.group(1))) if ma else None
            schema.resolver_y_registrar(record, "proteina_pct", [(analisis, "analisis"), (titulo, "titulo")],
                                        schema.reglas_titulo_vs_analisis())
            ms = _SACO_RE.search(ficha)
            record["empaque_kg"] = _fmt(_num(ms.group(1))) if ms else None
            mi = _INDICACIONES_RE.search(ficha)
            record.update(schema.columnas_etapa(schema.detectar_etapas(mi.group(1) if mi else "")))
        records.append(record)
    return records
