"""Parser de Api-Aba (Mexico). Publica nombre (con el saco en kg), analisis
garantizado (proteina/humedad/fibra) y, en Raceways, el tamano de micropellet.
No publica etapa normalizable ni tecnologia: quedan en None.

Si el % de proteina del titulo ("Dorado 35%") contradice el analisis
garantizado de la misma pagina (ocurre hoy en Dorado 35%, que muestra 40%), se
elige con `schema.reglas_titulo_vs_analisis` (RONDA2 R2.3): coincidencia entre
titulo/analisis/texto > analisis copiado de otro producto > nombre comercial.
El caso queda en _conflictos.csv."""
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


def _analisis_normalizado(lines: list[str]) -> str | None:
    """Bloque "ANALISIS GARANTIZADO" como pares valor|etiqueta en minusculas
    (ej. "40%|proteina|12%|humedad|3.5%|fibra"), para detectar copias."""
    for i, line in enumerate(lines):
        if re.fullmatch(r"prote[ií]na", line, re.I) and i > 0:
            bloque = []
            for l in lines[i - 1:i + 13]:
                if re.match(r"an[aá]lisis", l, re.I):
                    break
                bloque.append(re.sub(r"\s+", "", l.lower()).replace("í", "i"))
            return "|".join(bloque)
    return None


def _menciones_texto(lines: list[str], nombre: str) -> list[float]:
    """"35% de proteina" en la descripcion del producto (no en los titulos)."""
    vals = []
    for l in lines:
        if nombre in l:
            continue
        vals += [float(n) for n in re.findall(r"(\d+(?:\.\d+)?)\s*%\s*de\s+prote", l, re.I)]
    return vals


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
    in_title = re.search(r"(\d+(?:\.\d+)?)\s*%", nombre)
    candidatos = [(float(in_title.group(1)) if in_title else None, "titulo"),
                  (_guaranteed_protein(lines), "analisis")]
    candidatos += [(v, "texto") for v in _menciones_texto(lines, nombre)]
    kg = re.search(r"(\d+(?:\.\d+)?)\s*kg", nombre, re.I)

    record = schema.empty_record("Api-Aba")
    record["nombre_producto"] = nombre
    record["tamano_pellet_mm"] = _micropellet(" ".join(lines))
    record["empaque_kg"] = f"{float(kg.group(1)):g}" if kg else None
    record["_candidatos_proteina"] = candidatos
    record["_analisis"] = _analisis_normalizado(lines)
    record["fuente_url"] = url
    record["fecha_extraccion"] = datetime.date.today().isoformat()
    resolver_proteina([record])
    return [record]


def resolver_proteina(records: list[dict]) -> None:
    """Elige proteina_pct de cada record mirando a los demas productos del
    sitio (para la regla de analisis copiado)."""
    def valor_titulo(r):
        return next((v for v, o in r["_candidatos_proteina"] if o == "titulo"), None)
    for record in records:
        otros = [(r["nombre_producto"], r["_analisis"], valor_titulo(r)) for r in records if r is not record]
        record["_conflictos"] = [c for c in record.get("_conflictos", []) if c["campo"] != "proteina_pct"]
        schema.resolver_y_registrar(record, "proteina_pct", record["_candidatos_proteina"],
                                    schema.reglas_titulo_vs_analisis(record["_analisis"], otros))


def parse_listing(items: list[dict]) -> list[dict]:
    records = []
    for item in items:
        records.extend(parse_product(item["url"], item["html"]))
    resolver_proteina(records)
    return records
