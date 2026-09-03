"""Parser de HAID: HTML de pagina de producto + texto de la ficha tecnica
PDF (nativo u OCR) -> dict con el esquema unificado.

HAID publica sus fichas en 2 plantillas distintas (marca HAID base vs.
sub-marca "Shrimpy") pero ambas comparten las mismas etiquetas de campo
(Humedad/Proteina/Grasa/Fibra/Ceniza, Empaque+kg, tamanos en mm), por lo
que un solo set de regex por keyword de linea sirve para las dos.
"""
from __future__ import annotations

import datetime
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import schema  # noqa: E402
from scrapers import haid as sc  # noqa: E402

# Fallback de etapa cuando ni el texto de la ficha (marcador de peso) ni las
# reglas genericas de schema.normalize_etapa resuelven el caso. Solo aplica
# a "starter": su ficha describe el rango en gramos directamente (1 a 3 g)
# sin mencionar "PL" ni "tamano de mercado/cosecha", pero HAID lo agrupa en
# su propio sitio bajo el tab "Iniciadores" junto a Starter Pro, y su rango
# de peso es continuacion directa del de Starter Pro (que si se resuelve a
# 'precria' via el marcador PL10). Ver MEMORY.md.
_ETAPA_FALLBACK_BY_SLUG = {"starter": "precria"}

_REPRODUCTOR_MARKER = re.compile(r"reproductor|broodstock|maduraci[oó]n", re.I)
_PL10_MARKER = re.compile(r"\bpl\s?10\b", re.I)
_EARLY_MARKER = re.compile(r"post\s*larva|\bpl\s?\d+\b", re.I)
_LATE_MARKER = re.compile(r"tama[ñn]o de mercado|hasta\s+la\s+cosecha|hasta\s+cosecha|\bengorde\b", re.I)


def _infer_etapa(slug: str, text: str) -> str | None:
    """Ya NO prioriza el marcador de enfermedad (ver _detect_producto_salud):
    un producto con funcion terapeutica (ej. Fitness, "camarones juveniles
    y engorde que... previene enfermedades") no tiene una etapa propia por
    ser 'salud' -- devolverla aca antes descartaba la etapa real que el
    mismo texto tambien describia (hallazgo del usuario 2026-09-02, ver
    MEMORY.md)."""
    if _REPRODUCTOR_MARKER.search(text):
        return "reproductores"
    late = bool(_LATE_MARKER.search(text))
    if _PL10_MARKER.search(text) and not late:
        return "precria"
    early = bool(_EARLY_MARKER.search(text))
    if early and not late:
        return "larva"
    if late and not early:
        return "engorde"
    return _ETAPA_FALLBACK_BY_SLUG.get(slug)


def _line_number(text: str, label: str) -> float | None:
    for line in text.splitlines():
        if re.search(label, line, re.I):
            m = re.search(r"\d+(?:\.\d+)?", line)
            if m:
                return float(m.group(0))
    return None


def _extract_pellet_mm(text: str) -> str | None:
    nums = re.findall(r"(\d+(?:\.\d+)?)\s*mm", text, re.I)
    if not nums:
        return None
    unique_values = sorted({float(n) for n in nums})
    return ",".join(f"{v:.1f}" for v in unique_values)


def _extract_empaque_kg(text: str) -> str | None:
    m = re.search(
        r"empaque\s*[:\n]?(.*?)(?:condiciones de (?:conservaci[oó]n|almacenamiento))",
        text,
        re.I | re.S,
    )
    if not m:
        return None
    kgs = re.findall(r"(\d+(?:\.\d+)?)\s*kg", m.group(1), re.I)
    return ",".join(f"{v:g}" for v in sorted({float(k) for k in kgs})) if kgs else None


_EMPAQUE_SENTENCE_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*kg\s+para\s+(?:el\s+di[aá]metro|los\s+di[aá]metros)\s*(.+?)\.(?!\d)",
    re.I | re.S,
)
_MM_RE = re.compile(r"(\d+(?:\.\d+)?)\s*mm", re.I)


def _extract_empaque_pairs(text: str) -> dict[float, str]:
    """Extrae kg por tamano cuando la ficha lo desglosa explicitamente por
    diametro -- caso real HAID Starter Pro: "10kg para los diametros #0 -
    0.3mm, #1 - 0.5mm" / "25kg para el diametro #2 - 0.8mm" (dos sacos
    distintos para el mismo producto, hallazgo del usuario 2026-09-02).
    El "(?!\\d)" evita que el "." decimal de "0.3mm" se confunda con el
    punto final de la oracion. Devuelve {} si la ficha NO tiene esa frase
    (la mayoria de fichas HAID -- Starter/Happiness/Fitness -- usan un solo
    peso para todos sus tamanos sin desglosar por diametro); en ese caso el
    llamador debe seguir usando _extract_empaque_kg(), no forzar nada aca.
    Confirmado con el texto real (incluye ruido de OCR) de las 6 fichas:
    Speed y Happiness Plus SI tienen esta frase pero con un solo kg para
    varios diametros -- da el mismo resultado que _extract_empaque_kg, no
    cambia nada para esos dos."""
    pairs: dict[float, str] = {}
    for m in _EMPAQUE_SENTENCE_RE.finditer(text or ""):
        kg = m.group(1)
        for size_m in _MM_RE.finditer(m.group(2)):
            pairs[float(size_m.group(1))] = kg
    return pairs


def _extract_descripcion(text: str) -> str:
    m = re.search(
        r"descripci[oó]n del producto\s*:?\s*\n?(.*?)(?:ingredientes|composici[oó]n)",
        text,
        re.I | re.S,
    )
    return " ".join(m.group(1).split()) if m else ""


def _extract_recomendaciones(text: str) -> str:
    m = re.search(r"recomendaciones de uso\s*:?\s*\n?(.*?)(?:responsable t[eé]cnico|lotizaci[oó]n)", text, re.I | re.S)
    return " ".join(m.group(1).split()) if m else ""


def parse_product(url: str, html: str, pdf_bytes: bytes | None) -> list[dict]:
    """Devuelve una fila por tamano de pellet listado (mismo grano que
    Nicovita/Aquaxcel) en vez de una sola fila con los tamanos en una lista.
    A diferencia de Nicovita, aqui no hay ambiguedad que resolver: cada
    ficha HAID publica un unico % de proteina/grasa para TODOS sus
    calibres (son la misma formula en distintas moliendas, confirmado
    contra las 6 fichas reales -- ver MEMORY.md) asi que proteina_pct y
    grasa_pct se repiten igual en cada fila explotada."""
    record = schema.empty_record("HAID")
    record["fuente_url"] = url
    record["fecha_extraccion"] = datetime.date.today().isoformat()

    slug = url.rstrip("/").rsplit("/", 1)[-1]
    title_match = re.search(r'property="og:title" content="([^"]+)"', html)
    nombre = title_match.group(1).strip() if title_match else slug.replace("-", " ").title()
    record["nombre_producto"] = f"HAID {nombre}"

    pdf_text = ""
    if pdf_bytes:
        pdf_text, _used_ocr = sc.extract_pdf_text(pdf_bytes)

    record["proteina_pct"] = _line_number(pdf_text, r"prote[ií]na")
    record["grasa_pct"] = _line_number(pdf_text, r"grasa")

    pellet_from_pdf = _extract_pellet_mm(pdf_text)
    pellet_from_html = _extract_pellet_mm(html)
    record["tamano_pellet_mm"] = pellet_from_pdf or pellet_from_html

    record["tipo_presentacion"] = schema.detect_tecnologia(pdf_text)
    record["empaque_kg"] = _extract_empaque_kg(pdf_text)
    empaque_por_tamano = _extract_empaque_pairs(pdf_text)

    descripcion = _extract_descripcion(pdf_text)
    recomendaciones = _extract_recomendaciones(pdf_text)

    etapa_text = f"{descripcion} {recomendaciones}"
    record["etapa"] = _infer_etapa(slug, etapa_text)
    record["producto_salud"] = schema.detect_producto_salud(etapa_text)

    tamanos = [t for t in (record["tamano_pellet_mm"] or "").split(",") if t]
    if not tamanos:
        return [record]

    records = []
    for tamano in tamanos:
        row = dict(record)
        row["tamano_pellet_mm"] = tamano
        if empaque_por_tamano:
            row["empaque_kg"] = empaque_por_tamano.get(float(tamano), record["empaque_kg"])
        records.append(row)
    return records
