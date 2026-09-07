"""Parser de Agripac (linea Feedpac): HTML de la pagina de producto -> dict
con el esquema unificado (schema.SCHEMA_COLUMNS). Todo por regex/keyword-
matching, sin LLM (PLAN.md § 6).

A diferencia de Nicovita/HAID no hay ficha tecnica PDF: los datos tecnicos
viven en las pestanas WooCommerce de la propia pagina ("Tipo", "Subtipo",
"Presentaciones", "Ingredientes", "Modo de uso") -- confirmado 2026-09-03
contra los 20 productos reales del catalogo. Cada pagina de producto es un
solo SKU (un tamano, una proteina), asi que el grano es una fila por URL,
igual que Aquaxcel/Agrizon -- no hay tabla combinatoria que explotar como en
Nicovita.
"""
from __future__ import annotations

import datetime
import html as html_lib
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import schema  # noqa: E402

_TITLE_RE = re.compile(r'<h1 class="elementor-heading-title elementor-size-default">([^<]+)</h1>')
_TAB_RE = re.compile(
    r'woocommerce-Tabs-panel--(?P<name>[\w-]+) panel entry-content wc-tab"'
    r' id="tab-[\w-]+" role="tabpanel"[^>]*>(?P<body>.*?)</div>\s*'
    r'(?:<div class="woocommerce-Tabs-panel|\Z)',
    re.S,
)

_PROTEIN_RE = re.compile(r"(\d+(?:\.\d+)?)\s*%")
_NUCLEO_PROTEIN_RE = re.compile(r"n[uú]cleo\s+(\d+(?:\.\d+)?)\s*%", re.I)
# Acepta "." y "," como separador decimal -- el sitio usa ambos segun el
# producto (ej. "1.2mm" en unos, "1,8 Mm" en Santa Monica/Ultra Gregarinas).
_MM_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*mm", re.I)
_KG_RE = re.compile(r"(\d+(?:\.\d+)?)\s*kg", re.I)


def _extract_title(html: str) -> str | None:
    # html_lib.unescape() agregado 2026-09-07: caso real "MeM 300 - 500"
    # (division Larvicultura) -- su <h1> trae el guion como entidad HTML
    # literal ("MeM 300 &#8211; 500") en vez del caracter "-" ya resuelto,
    # a diferencia del resto del catalogo balanceado (sin entidades en el
    # titulo). Sin decodificar, "&#8211;" quedaba tal cual en nombre_producto.
    m = _TITLE_RE.search(html)
    return html_lib.unescape(m.group(1)).strip() if m else None


def _extract_tabs(html: str) -> dict[str, str]:
    tabs: dict[str, str] = {}
    for m in _TAB_RE.finditer(html):
        text = re.sub(r"<[^>]+>", " ", m.group("body"))
        text = re.sub(r"\s+", " ", text).strip()
        if text:
            tabs[m.group("name")] = text
    return tabs


def _proteina_pct(title: str, ingredientes: str) -> str | None:
    """El % va en el titulo para casi todo el catalogo (ej. "Feedpac 35%
    Ultra Micropellet 1.2mm"). La unica excepcion confirmada es "Premium
    Agua Dulce" (sin % en el titulo) -- ahi el % solo aparece en el texto
    de Ingredientes ("nucleo 35% Premium agua dulce"), asi que se usa como
    fallback en vez de dejarlo en None cuando el dato si esta publicado."""
    m = _PROTEIN_RE.search(title)
    if m:
        return m.group(1)
    m = _NUCLEO_PROTEIN_RE.search(ingredientes)
    return m.group(1) if m else None


def _tamano_mm(title: str, subtipo: str) -> str | None:
    """"Subtipo" es el campo dedicado a tamano y es la fuente preferida,
    pero 2 productos ("Premium Micropellet Agua Dulce" 1.2mm/1.5mm) no
    tienen esa pestana aunque el tamano SI esta en el titulo -- se cae a
    extraerlo de ahi en vez de dejarlo vacio cuando el dato esta a la
    vista. Sin pestana "Subtipo" y sin mm en el titulo (ej. Feedpac 35%
    Premium base) queda en None: esa ficha realmente no publica un tamano
    puntual, no hay que inventarlo."""
    text = subtipo or title
    m = _MM_RE.search(text)
    return m.group(1).replace(",", ".") if m else None


def _empaque_kg(presentaciones: str) -> str | None:
    m = _KG_RE.search(presentaciones)
    return m.group(1) if m else None


def parse_product(url: str, html: str, es_larvicultura: bool = False) -> dict:
    record = schema.empty_record("Agripac")
    record["fuente_url"] = url
    record["fecha_extraccion"] = datetime.date.today().isoformat()
    # Marcador interno (no es columna del esquema -- pipeline.write_csv()
    # arma el DataFrame con schema.SCHEMA_COLUMNS, asi que esta clave nunca
    # llega al CSV): agregado 2026-09-07 para que write_csv() pueda pasarle
    # a schema.clasificacion_camaron_from_row() que este producto viene de
    # la division Larvicultura -- a pedido del usuario, TODO producto de esa
    # division es "Hatchery" sin mirar tamano (ver docstring de esa funcion).
    record["_es_larvicultura"] = es_larvicultura

    title = _extract_title(html) or ""
    record["nombre_producto"] = title

    tabs = _extract_tabs(html)
    ingredientes = tabs.get("ingredientes", "")
    subtipo = tabs.get("subtipo", "")
    presentaciones = tabs.get("presentaciones", "")

    record["proteina_pct"] = _proteina_pct(title, ingredientes)
    record["tamano_pellet_mm"] = _tamano_mm(title, subtipo)
    # Solo la pestana "Tipo" (campo dedicado) decide tipo_presentacion -- la
    # "Descripcion" es texto de marketing que en al menos 2 productos
    # (Premium Micropellet Agua Dulce) dice "pelletizado" mientras que su
    # propia pestana "Tipo" dice "Polvo" (ficha internamente inconsistente,
    # confirmado 2026-09-03). Desde 2026-09-07 "Polvo"/"Microparticulado"/
    # "Liquido" son valores propios de tipo_presentacion (ver
    # schema.detect_tecnologia), asi que ya no quedan en None -- a pedido
    # del usuario, tras encontrar estos 3 casos reales en la division
    # Larvicultura (Artemia Cysts, Mpex, Royal Pepper Protein).
    record["tipo_presentacion"] = schema.detect_tecnologia(tabs.get("tipo"))
    record["empaque_kg"] = _empaque_kg(presentaciones)

    etapa_text = " ".join(
        [title, tabs.get("description", ""), tabs.get("modo-de-uso", ""), ingredientes]
    )
    record["producto_salud"] = schema.detect_producto_salud(etapa_text)
    etapa = schema.normalize_etapa(title)
    if etapa is None:
        etapa = schema.normalize_etapa(etapa_text)
    if etapa is None:
        etapa = schema.etapa_from_tamano(record["tamano_pellet_mm"], record["tipo_presentacion"])
    record["etapa"] = etapa

    return record


def parse_listing(products: list[dict]) -> list[dict]:
    return [parse_product(p["url"], p["html"], p.get("es_larvicultura", False)) for p in products]
