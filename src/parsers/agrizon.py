"""Parser de Agrizon: completa los campos tecnicos de BioMar que
biomar.com no publica (MEMORY.md / PLAN.md § 5) -- tamano_pellet_mm,
tipo_presentacion, empaque_kg, proteina_pct y etapa -- a partir del listado
de un distribuidor ecuatoriano.

Los registros que devuelve este modulo se AGREGAN a los de
src/parsers/biomar.py bajo el mismo empresa="BioMar" (distinguibles por
fuente_url: agrizon.com vs biomar.com), NO los reemplazan: el grano es
distinto (un registro por SKU real de tamano/proteina, como Nicovita/
Aquaxcel, contra un registro por familia de producto en biomar.com) y en 2
de las 5 lineas de producto que aparecen en Agrizon (Exia Start, Larviva)
no se puede saber a que sub-linea especifica de biomar.com corresponde
cada SKU (INICIO Focus/Maxio/Prime/Pro; LARVIVA Mysis/PL/Zoea) -- forzar
una equivalencia ahi seria inventar dato, asi que en esos 2 casos
nombre_producto queda con el nombre generico que usa Agrizon.

grasa_pct sigue sin publicarse en ningun lado (ni biomar.com ni Agrizon) --
queda None igual que antes.

proteina_pct se lee del TITULO del producto (confirmado con el usuario
2026-09-03): un producto (Exia Prime 35% Precria 0.6-0.9mm) tiene su
`body_html` en desacuerdo con su titulo (25% vs 35%) -- decision del
usuario fue que el titulo es el dato real y el body_html el equivocado, asi
que no se usa body_html para ningun campo aca.
"""
from __future__ import annotations

import datetime
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import schema  # noqa: E402

# Titulo de Agrizon: "<nombre de linea> <proteina>% [Pelletized|Extruded|...]
# <tamano> mm|microns <empaque> kg." -- todo lo que sigue al nombre de linea
# arranca con un digito (proteina), asi que alcanza con cortar antes del
# primer token numerico.
_LINE_NAME_RE = re.compile(r"^(\D+?)\s*\d")
_PROTEIN_RE = re.compile(r"(\d+(?:\.\d+)?)\s*%")
_SIZE_RE = re.compile(r"(\d+(?:\.\d+)?)\s*-?\s*(\d+(?:\.\d+)?)?\s*(mm|microns?)", re.I)


def _line_name(title: str) -> str:
    m = _LINE_NAME_RE.match(title)
    return m.group(1).strip() if m else title.strip()


def _proteina_pct(title: str) -> str | None:
    m = _PROTEIN_RE.search(title)
    return m.group(1) if m else None


def _tamano_mm(title: str) -> str | None:
    """mm directo, o "microns"/1000 convertido a mm (Larviva). Preserva
    rangos como texto (ej. "0.6-0.9"), igual que Nicovita en su tabla PDF --
    no se colapsa a un solo numero para no perder informacion real."""
    m = _SIZE_RE.search(title)
    if not m:
        return None
    lo, hi, unit = m.group(1), m.group(2), m.group(3).lower()
    divisor = 1000.0 if unit.startswith("micron") else 1.0
    lo_mm = float(lo) / divisor
    if hi:
        hi_mm = float(hi) / divisor
        return f"{lo_mm:g}-{hi_mm:g}"
    return f"{lo_mm:g}"


def _etapa(tags_text: str, tamano_pellet_mm: str | None, tipo_presentacion: str | None) -> str | None:
    """Los tags de Agrizon son categorias de merchandising, no siempre
    etapa real -- ej. "Exia Prime 35% Pelletized 1.2mm" trae "engorde" Y
    "Iniciadores" a la vez en el mismo SKU (un tag de linea/marketing junto
    a uno de tamano real). Si el texto matchea MAS de una etapa distinta
    (schema.etapa_matches) se descarta como ambiguo -- mismo criterio que
    usa parsers/biomar.py cuando biomar.com publica 2 valores de Etapa a la
    vez -- y se cae al fallback de tamano de pellet (dato fisico, sin esa
    ambiguedad). Confirmado contra los 17 productos reales 2026-09-03: este
    orden (tags si son inequivocos, si no tamano) es el unico que clasifica
    correctamente tanto Larviva ("larva", que etapa_from_tamano no puede
    devolver por diseño) como Exia Prime 1.2mm ("precria", donde el tag es
    ambiguo pero el tamano no)."""
    matches = schema.etapa_matches(tags_text)
    if len(matches) == 1:
        return matches.pop()
    return schema.etapa_from_tamano(tamano_pellet_mm, tipo_presentacion)


def parse_product(product: dict) -> dict:
    record = schema.empty_record("BioMar")
    title = product.get("title") or ""
    tags_text = ", ".join(product.get("tags") or [])
    handle = product.get("handle") or ""

    record["fuente_url"] = f"https://agrizon.com/en/products/{handle}"
    record["fecha_extraccion"] = datetime.date.today().isoformat()
    record["nombre_producto"] = _line_name(title)
    record["proteina_pct"] = _proteina_pct(title)
    record["tamano_pellet_mm"] = _tamano_mm(title)
    # title+tags: el titulo dice "Pelletized"/"Extruded" (ingles) para todos
    # los productos que tienen tecnologia mencionada, pero el tag en
    # espanol ("Pelletizado"/"extruido"/"Extrusado") no siempre esta
    # presente (ej. EXIA Perform/Pro) -- combinar ambos cierra ese hueco.
    record["tipo_presentacion"] = schema.detect_tecnologia(f"{title} {tags_text}")
    record["producto_salud"] = schema.detect_producto_salud(tags_text)
    record["etapa"] = _etapa(tags_text, record["tamano_pellet_mm"], record["tipo_presentacion"])

    variant = (product.get("variants") or [{}])[0]
    grams = variant.get("grams")
    record["empaque_kg"] = f"{grams / 1000:g}" if grams else None

    return record


def parse_listing(products: list[dict]) -> list[dict]:
    return [parse_product(p) for p in products]
