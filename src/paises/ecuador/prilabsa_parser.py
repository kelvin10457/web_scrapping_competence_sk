"""Parser del catalogo de Prilabsa (Ecuador), R7.7.

Seccion "Alimentos" del indice: una ficha por pagina. La empresa sale del
indice (rango de paginas por fabricante) y del numero impreso al pie. Una
fila por tamano publicado (etiqueta encima de cada "MICRAS", o "#N a-b
micras" en Higashimaru); sin tabla de tamanos, una fila sin tamano.
Proteina solo si la ficha publica un unico valor; empaque = pesos de envase
(no la dosis). Etapas de la ficha completa (como El Pedregal)."""
from __future__ import annotations

import datetime
import re
import sys
from pathlib import Path

import pdfplumber

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import schema  # noqa: E402

PDF_URL = "https://prilabsa.com/assets/pdfs/CATALOGO%20PRODUCTOS%20JULIO%20PRILABSA.pdf"
FABRICANTES = {"ZEIGLER": "Zeigler", "MACKAY": "Mackay Marine", "HIGASHIMARU": "Higashimaru"}
_INDICE_RE = re.compile(r"^(.+?)\.{3,}\s*(\d+)\s*$")
_TITULO_RE = re.compile(r"^(.*?)\s*\(([^)]*)\)\s*$")
_PROT_RE = re.compile(r"Prote[ií]na\s*Cruda\s*\.{2,}\s*\(m[ií]nim[ao]\)\s*([^\n%]*%(?:\s*\([^)\n]*\))?)", re.I)
_ENVASE_RE = re.compile(r"\b(?:latas?|baldes?|fundas?|sacos?|envases?|bolsas?)\b[^\d\n]{0,45}?"
                        r"(\d+(?:[.,]\d+)?)\s*(kg|gr|g)\b", re.I)
_HASH_RE = re.compile(r"(#\d)\s+(\d+)\s*-\s*(\d+)\s*micras", re.I)
_PRESENTACION_EXTRA = {"CISTOS DE ARTEMIA": "Quistes de artemia"}
# Encabezado de la tabla de tamanos (Shrimp Meal): no es una etapa del producto.
_ENCABEZADO_TABLA_RE = re.compile(r"TAMA[NÑ]O DE PART[IÍ]CULAS?\s*Y ESTADIO LARVAL")
# "150: Latas ... 500 gr." / "250, 350: Fundas ... 4kg" (Z PRO): envase por tamano.
_ENVASE_POR_TAMANO_RE = re.compile(
    r"(\d+(?:\s*,\s*\d+)*)\s*:\s*(?:latas?|baldes?|fundas?|sacos?|envases?|bolsas?)\b[^\d\n]{0,45}?"
    r"(\d+(?:[.,]\d+)?)\s*(kg|gr|g)\b", re.I)
# Espirulina: "Tamaños" y debajo "8 a 10 micras 20 micras".
_TAMANOS_LINEA_RE = re.compile(r"(\d+)\s*a\s*(\d+)\s*micras|(\d+)\s*micras", re.I)


def _mm(micras: str) -> str:
    return f"{float(micras) / 1000:g}"


def _tamano(etiqueta: str) -> str | None:
    e = " ".join(etiqueta.split())
    if m := re.fullmatch(r"<\s*(\d+)", e):
        return "<" + _mm(m.group(1))
    if m := re.fullmatch(r"(\d+)\s*-\s*(\d+)", e):
        return f"{_mm(m.group(1))}-{_mm(m.group(2))}"
    if m := re.fullmatch(r"\d+", e):
        return _mm(m.group(0))
    return None


def _rangos_indice(texto: str) -> list[tuple[int, int, str]]:
    """[(desde, hasta_excl, empresa)] de la seccion Alimentos del indice."""
    entradas = [(m.group(1).strip(), int(m.group(2)))
                for ln in texto.splitlines() if (m := _INDICE_RE.match(ln.strip()))]
    rangos = []
    for i, (nombre, desde) in enumerate(entradas):
        clave = next((v for k, v in FABRICANTES.items() if k in nombre.upper()), None)
        if clave:
            hasta = entradas[i + 1][1] if i + 1 < len(entradas) else desde + 1
            rangos.append((desde, hasta, clave))
    return rangos


def _numero_impreso(page) -> int | None:
    """Numero de pagina del catalogo: la palabra numerica mas baja de la
    pagina (en Z PRO comparte renglon con la tabla de etapas)."""
    words = page.extract_words()
    if not words:
        return None
    ultima = max(words, key=lambda w: w["bottom"])
    return int(ultima["text"]) if ultima["text"].isdigit() else None


def _etiquetas_micras(page) -> list[str]:
    words = page.extract_words()
    out = []
    for m in (w for w in words if w["text"].upper().startswith("MICRA")):
        cx = (m["x0"] + m["x1"]) / 2
        arriba = [w for w in words if 0 < m["top"] - w["top"] < 12 and abs((w["x0"] + w["x1"]) / 2 - cx) < 15]
        out.append(" ".join(w["text"] for w in sorted(arriba, key=lambda w: w["x0"])))
    return list(dict.fromkeys(out))


def _kg(num: str, unidad: str) -> str:
    v = float(num.replace(",", "."))
    return f"{v if unidad.lower() == 'kg' else v / 1000:g}"


def _envase_por_tamano(texto: str) -> dict[str, str]:
    """{'150': '0.5', '250': '4', ...} cuando la ficha dice que envase lleva cada tamano."""
    out = {}
    for tamanos, num, unidad in _ENVASE_POR_TAMANO_RE.findall(texto):
        for t in re.findall(r"\d+", tamanos):
            out[t] = _kg(num, unidad)
    return out


def _tamanos_bajo_titulo(texto: str) -> list[tuple[str, str]]:
    lineas = texto.splitlines()
    for i, ln in enumerate(lineas[:-1]):
        if re.fullmatch(r"(?:Tama[nñ]os\s*)+", ln.strip(), re.I):
            return [(f"{a}-{b}" if a else c, f"{_mm(a)}-{_mm(b)}" if a else _mm(c))
                    for a, b, c in _TAMANOS_LINEA_RE.findall(lineas[i + 1])]
    return []


def _proteina(texto: str) -> float | None:
    valores = [schema.normalize_proteina(v) for v in _PROT_RE.findall(texto)]
    return valores[0] if valores and None not in valores and len(set(valores)) == 1 else None


def _empaque(texto: str) -> str | None:
    kg = []
    for num, unidad in _ENVASE_RE.findall(texto):
        kg.append(_kg(num, unidad))
    kg = list(dict.fromkeys(kg))
    return ",".join(kg) if kg else None


def _tipo(ficha: str, paren: str | None, texto: str) -> str | None:
    if ficha.upper() in _PRESENTACION_EXTRA:
        return _PRESENTACION_EXTRA[ficha.upper()]
    if paren:
        return schema.normalize_presentacion(re.sub(r"s$", "", paren.strip()))
    if re.search(r"\bMICROPARTICULADO\b", texto):
        return "Microparticulado"
    return None


def parse_pdf(path: Path, url: str = PDF_URL) -> list[dict]:
    hoy = datetime.date.today().isoformat()
    records = []
    with pdfplumber.open(path) as pdf:
        textos = [p.extract_text() or "" for p in pdf.pages]
        indice = next((t for t in textos if re.search(r"^Alimentos\s*$", t, re.M) and "Zeigler" in t), "")
        rangos = _rangos_indice(indice)
        for page, texto in zip(pdf.pages, textos):
            n = _numero_impreso(page)
            empresa = next((e for d, h, e in rangos if n is not None and d <= n < h), None)
            if empresa is None:
                continue
            titulo = texto.strip().splitlines()[0].strip()
            m = _TITULO_RE.match(titulo)
            ficha, paren = (m.group(1).strip(), m.group(2)) if m else (titulo, None)
            tamanos = [(e, t) for e in _etiquetas_micras(page) if (t := _tamano(e))]
            if not tamanos:
                tamanos = [(f"{h} {a}-{b}", f"{_mm(a)}-{_mm(b)}") for h, a, b in _HASH_RE.findall(texto)]
            if not tamanos:
                tamanos = _tamanos_bajo_titulo(texto)
            envase_por_tamano = _envase_por_tamano(texto)
            base = schema.empty_record(empresa)
            base.update(schema.columnas_etapa(schema.detectar_etapas(_ENCABEZADO_TABLA_RE.sub(" ", texto))))
            base.update({"_etapas_detectadas": True, "_ficha": ficha, "fuente_url": url,
                         "fecha_extraccion": hoy, "proteina_pct": _proteina(texto),
                         "empaque_kg": _empaque(texto), "tipo_presentacion": _tipo(ficha, paren, texto)})
            for etiqueta, tamano in tamanos or [(None, None)]:
                r = dict(base)
                r["nombre_producto"] = f"{ficha} {' '.join(etiqueta.split())} micras" if etiqueta else ficha
                r["tamano_pellet_mm"] = tamano
                if etiqueta and etiqueta.strip() in envase_por_tamano:
                    r["empaque_kg"] = envase_por_tamano[etiqueta.strip()]
                records.append(r)
    return records
