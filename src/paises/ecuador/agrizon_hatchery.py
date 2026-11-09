"""R11.2: hatchery que publica Agrizon y que no trae ninguna otra fuente.

- Prilabsa "Biomasa de Artemia Congelada" (compite con Skretting Ignis): una
  fila nueva que `prilabsa.run()` suma a las del PDF.
- Megasupply Megalikuid B/C (dieta liquida, compite con InVita): fuente
  `megasupply` de Ecuador.
- Proteina de los Bernaqua (Royal Caviar, Royal Seafood, MPEX, MeM, Royal
  Pepper Protein). Agripac ya los trae como filas propias, pero sin proteina:
  aca solo se completa esa celda, sin agregar filas (decision 2026-11-09).

Zeigler y Mackay tambien estan en Agrizon, pero no se toman porque ya los
trae Prilabsa.
"""
from __future__ import annotations

import datetime
import functools
import re

import requests

import schema
from paises.ecuador import agrizon_scraper

_PROTEINA_BODY_RE = re.compile(r"Prote[ií]na\s*([\d.,]+(?:\s*-\s*[\d.,]+)?)\s*%", re.I)
_TAMANO_MICRAS_RE = re.compile(r"\((\d+(?:[.,]\d+)?)\s*-\s*(\d+(?:[.,]\d+)?)\s*[μµu]\)")
_EMPAQUE_FINAL_RE = re.compile(r"\s+\d+(?:[.,]\d+)?\s*(?:kg|gr|g|lt|l)\.?$", re.I)


@functools.cache
def productos() -> list[dict]:
    """Coleccion de Agrizon, pedida una sola vez por corrida (Agripac y Prilabsa
    la usan; cada pedido extra suma al 429). Si falla, lista vacia y aviso."""
    try:
        return agrizon_scraper.fetch_collection_products(collection_url=agrizon_scraper.COLLECTION_URL_ES)
    except requests.RequestException as e:
        print(f"  [aviso] Agrizon no respondio ({e}); se sigue sin su hatchery.")
        return []


def _texto(html: str | None) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html or "")).strip()


def clave_nombre(nombre: str) -> str:
    """Nombre comparable entre Agripac y Agrizon: minusculas, guion largo a
    guion, sin espacios alrededor del guion y sin el empaque final."""
    n = (nombre or "").replace("–", "-").replace("—", "-").strip()
    n = _EMPAQUE_FINAL_RE.sub("", n)
    n = re.sub(r"\s*-\s*", "-", n)
    return re.sub(r"\s+", " ", n).strip().lower()


def _url(p: dict) -> str:
    return f"https://agrizon.com/en/products/{p.get('handle', '')}"


def biomasa_artemia(products: list[dict]) -> list[dict]:
    filas = []
    for p in products:
        title = p.get("title") or ""
        if p.get("vendor") != "Prilabsa" or "biomasa de artemia" not in title.lower():
            continue
        r = schema.empty_record("Prilabsa")
        r["nombre_producto"] = _EMPAQUE_FINAL_RE.sub("", title.strip()).strip()
        r["fuente_url"] = _url(p)
        r["fecha_extraccion"] = datetime.date.today().isoformat()
        grams = (p.get("variants") or [{}])[0].get("grams")
        r["empaque_kg"] = f"{grams / 1000:g}" if grams else None
        r["es_producto_de_salud"] = schema.detect_es_producto_de_salud(", ".join(p.get("tags") or []))
        # El titulo no nombra etapa; los tags si ("Post-larva").
        r.update(schema.columnas_etapa(schema.detectar_etapas(f"{title} {', '.join(p.get('tags') or [])}")))
        r["_etapas_detectadas"] = True
        filas.append(r)
    return filas


def megalikuid(products: list[dict]) -> list[dict]:
    """Dietas liquidas Megalikuid de Megasupply (rivales de InVita), una fila
    por producto. Promegabiotic (probiotico) no entra."""
    filas = []
    for p in products:
        title = p.get("title") or ""
        if p.get("vendor") != "Megasupply" or not title.lower().startswith("megalikuid"):
            continue
        body = _texto(p.get("body_html"))
        tags = ", ".join(p.get("tags") or [])
        r = schema.empty_record("Megasupply")
        r["nombre_producto"] = _EMPAQUE_FINAL_RE.sub("", title.strip()).strip()
        r["fuente_url"] = _url(p)
        r["fecha_extraccion"] = datetime.date.today().isoformat()
        m = _PROTEINA_BODY_RE.search(body)
        r["proteina_pct"] = schema.normalize_proteina(m.group(1)) if m else None
        t = _TAMANO_MICRAS_RE.search(body)
        if t:
            lo, hi = (float(x.replace(",", ".")) / 1000 for x in t.groups())
            r["tamano_pellet_mm"] = f"{lo:g}-{hi:g}"
        r["tipo_presentacion"] = schema.detect_tecnologia(f"{title} {tags}")
        grams = (p.get("variants") or [{}])[0].get("grams")
        r["empaque_kg"] = f"{grams / 1000:g}" if grams else None
        r["es_producto_de_salud"] = schema.detect_es_producto_de_salud(tags)
        r.update(schema.columnas_etapa(schema.detectar_etapas(f"{title} {tags} {body}")))
        r["_etapas_detectadas"] = True
        filas.append(r)
    return filas


def proteinas_bernaqua(products: list[dict]) -> dict[str, tuple[float | None, str]]:
    """clave_nombre -> (proteina del body_html, url). Un rango queda en None."""
    out = {}
    for p in products:
        if p.get("vendor") != "Bernaqua":
            continue
        m = _PROTEINA_BODY_RE.search(_texto(p.get("body_html")))
        out[clave_nombre(p.get("title") or "")] = (schema.normalize_proteina(m.group(1)) if m else None, _url(p))
    return out


def completar_proteina(records: list[dict], products: list[dict]) -> list[dict]:
    """Completa proteina_pct de las filas de Agripac con la de Agrizon. Si
    Agripac ya trae un valor gana Agripac; el desacuerdo queda registrado."""
    prot = proteinas_bernaqua(products)
    for r in records:
        valor, url = prot.get(clave_nombre(r.get("nombre_producto") or ""), (None, None))
        if valor is None:
            continue
        actual = r.get("proteina_pct")
        if actual is None or actual == "":
            r["proteina_pct"] = valor
            schema.registrar_conflicto(r, "proteina_pct", valor, "completado:agrizon",
                                       [(valor, f"agrizon {url}")])
        else:
            schema.resolver_y_registrar(r, "proteina_pct", [(actual, "agripac"), (valor, "agrizon")],
                                        [schema.regla_preferir("agripac")])
    return records
