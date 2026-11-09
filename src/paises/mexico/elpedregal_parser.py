"""Parser de El Pedregal (Mexico), R7.5.

Imagenes (texto OCR): cada titulo con "(PP-GG)" es un producto; se genera una
fila por tamano publicado (una fila por SKU). Tipo por linea de tamano:
- "Micropartículas: 100, 200 ... um" -> mm, Microparticulado.
- "Micropelets" de Microtek -> Extruido (el PDF Alimentos-Extruidos-Crustaceos.pdf
  del fabricante: "micropelets extruidos de 0.6, 0.8, 1 y 1.4mm").
- "Minipelets" -> sin tipo (no se publica).
- "Pelets: 2.1x 3 mm" -> diametro (2.1); tipo segun el titulo ("ENGORDA EXTRUIDO").
Etapas: encabezado de seccion + texto desde "Uso:".

Tabla HTML ?t=mp: una fila por SKU (nombre, tamano, talla, proteina, ...)."""
from __future__ import annotations

import datetime
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import schema  # noqa: E402

EMPRESA = "El Pedregal"
_NUM_RE = re.compile(r"\d+(?:[.,]\d+)?")
_TITULO_RE = re.compile(r"\(\d{2}-\d{1,2}\)")
_SECCION_RE = re.compile(r"(?:PRE ?ENGORDA Y ENGORDA|PREENGORDA|ENGORDA|LARVAS Y POSTLARVAS|POSTLARVAS|LARVAS)")
_PROT_RE = re.compile(r"PROTE[IÍ]NA\s*:\s*(\d+(?:[.,]\d+)?)\s*%", re.I)
_TAMANO_RE = re.compile(r"(Micropart[ií]culas|Micropelets|Minipelets|Pelets)\s*:\s*(.*)", re.I)
_TITULO_MM_RE = re.compile(r"(\d+\.\d+)\s*mm", re.I)


def _fmt(x: float) -> str:
    return f"{x:g}"


def _num(s: str) -> float:
    return float(s.replace(",", "."))


def _record(nombre: str, url: str, etapa_texto: str) -> dict:
    record = schema.empty_record(EMPRESA)
    record["nombre_producto"] = nombre
    record.update(schema.columnas_etapa(schema.detectar_etapas(etapa_texto)))
    record["_etapas_detectadas"] = True
    record["fuente_url"] = url
    record["fecha_extraccion"] = datetime.date.today().isoformat()
    return record


def _tamanos(tipo_linea: str, valor: str, titulo: str) -> tuple[list[str], str | None]:
    """(tamanos en mm como texto, tipo_presentacion) de una linea de tamano."""
    clave = tipo_linea.lower()
    nums = [_num(n) for n in _NUM_RE.findall(valor)]
    if clave.startswith("micropart"):
        return [_fmt(n / 1000) for n in nums], "Microparticulado"
    if clave == "micropelets":
        return [_fmt(n) for n in nums], ("Extruido" if titulo.upper().startswith("MICROTEK") else None)
    if clave == "minipelets":
        return [_fmt(n) for n in nums], None
    # "Pelets: 2.1x 3 mm": diametro x largo; vale el diametro.
    if not nums:
        return [], schema.detect_tecnologia(titulo)
    diametro = nums[0]
    m = _TITULO_MM_RE.search(titulo)
    if m and diametro > 10 and abs(diametro / 10 - float(m.group(1))) < 1e-9:
        diametro = float(m.group(1))  # el OCR perdio el punto ("21x 3"); manda el titulo
    return [_fmt(diametro)], schema.detect_tecnologia(titulo)


def parse_ocr(url: str, texto: str) -> list[dict]:
    lineas = [ln.strip() for ln in texto.splitlines() if ln.strip()]
    bloques: list[tuple[str, str, list[str]]] = []  # (seccion, titulo, lineas)
    seccion = ""
    for ln in lineas:
        if _SECCION_RE.fullmatch(ln):
            seccion = ln
        elif _TITULO_RE.search(ln) and ":" not in ln:
            bloques.append((seccion, ln, []))
        elif bloques:
            bloques[-1][2].append(ln)

    records = []
    for seccion, titulo, cuerpo in bloques:
        texto_bloque = "\n".join(cuerpo)
        m = _PROT_RE.search(texto_bloque)
        proteina = schema.normalize_proteina(_num(m.group(1))) if m else None
        uso = texto_bloque[texto_bloque.find("Uso:"):] if "Uso:" in texto_bloque else ""
        etapa_texto = f"{seccion} {uso}"
        for ln in cuerpo:
            mt = _TAMANO_RE.match(ln)
            if not mt:
                continue
            tamanos, tipo = _tamanos(mt.group(1), mt.group(2), titulo)
            for tamano in tamanos:
                record = _record(titulo, url, etapa_texto)
                record["tamano_pellet_mm"] = tamano
                record["tipo_presentacion"] = tipo
                record["proteina_pct"] = proteina
                records.append(record)
    return records


def _tamano_rango(texto: str) -> str | None:
    nums = [_num(n) for n in _NUM_RE.findall(texto or "")]
    if not nums or len(nums) > 2:
        return None
    return "-".join(_fmt(n) for n in nums)


def parse_table(url: str, html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    h1 = soup.find("h1")
    seccion = h1.get_text(" ", strip=True) if h1 else ""
    records = []
    for tr in soup.find_all("tr"):
        celdas = [td.get_text(" ", strip=True) for td in tr.find_all(["td", "th"])]
        if len(celdas) < 4 or not celdas[0].startswith("*"):
            continue
        nombre = re.sub(r"^[*\s]+", "", celdas[0])
        record = _record(nombre, url, seccion)
        record["tamano_pellet_mm"] = _tamano_rango(celdas[1])
        record["tipo_presentacion"] = schema.detect_tecnologia(nombre)
        nums = _NUM_RE.findall(celdas[3])
        record["proteina_pct"] = schema.normalize_proteina(_num(nums[0])) if len(nums) == 1 else None
        records.append(record)
    return records


def parse_listing(items: list[dict]) -> list[dict]:
    records = []
    for item in items:
        if "ocr" in item:
            records.extend(parse_ocr(item["url"], item["ocr"]))
        else:
            records.extend(parse_table(item["url"], item["html"]))
    return records
