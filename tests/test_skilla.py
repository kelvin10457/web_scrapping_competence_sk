"""R7.8: Skilla (BioBlue, Mexico) via bioblue.com/skilla/ + OCR de los pies de foto."""
import json

import fuentes
from conftest import FIXTURES
from paises.mexico import skilla_parser as parser

URL = "https://bioblue.com/skilla/"


def _records():
    html = (FIXTURES / "skilla_bioblue.html").read_text(encoding="utf-8")
    textos = json.loads((FIXTURES / "skilla_ocr.json").read_text(encoding="utf-8"))
    return parser.parse_page(URL, html, textos)


def _por_clave():
    return {(r["nombre_producto"], r["tamano_pellet_mm"]): r for r in _records()}


# REQ-1
def test_una_fila_por_codigo_y_diametro():
    recs = _records()
    assert sorted((r["nombre_producto"], r["tamano_pellet_mm"]) for r in recs) == [
        ("SKILLA 3505", "1.5"), ("SKILLA 3505", "2.5"), ("SKILLA 4008", "1"), ("SKILLA 4008", "1.5")]
    assert all(r["empresa"] == "Skilla" and r["fuente_url"] == URL for r in recs)


# REQ-2
def test_foto_se_asigna_por_orden_y_sin_pie_queda_vacio():
    html = (FIXTURES / "skilla_bioblue.html").read_text(encoding="utf-8")
    textos = json.loads((FIXTURES / "skilla_ocr.json").read_text(encoding="utf-8"))
    textos = {u: ("" if u.endswith("Skilla_3505-3.png") else t) for u, t in textos.items()}
    recs = parser.parse_page(URL, html, textos)
    tres = {r["tamano_pellet_mm"] for r in recs if r["nombre_producto"] == "SKILLA 3505"}
    assert tres == {"1.5", None}


# REQ-3
def test_etapas_tipo_y_vacios():
    r = _por_clave()
    assert r[("SKILLA 4008", "1")]["etapa_post_transferencia"] is None
    assert r[("SKILLA 4008", "1")]["etapa_engorde"] is None
    assert r[("SKILLA 4008", "1.5")]["etapa_post_transferencia"] is True
    assert r[("SKILLA 3505", "1.5")]["etapa_post_transferencia"] is True
    assert r[("SKILLA 3505", "2.5")]["etapa_engorde"] is True
    assert r[("SKILLA 3505", "2.5")]["etapa_post_transferencia"] is False
    for x in r.values():
        assert x["tipo_presentacion"] == "Extruido"
        assert x["proteina_pct"] is None and x["empaque_kg"] is None


# REQ-4
def test_registrada_en_mexico():
    assert ("mexico", "skilla") in fuentes.listar(solo_activas=True)
    spec = (FIXTURES.parent.parent / "ScraperCompetencia.spec").read_text(encoding="utf-8")
    for m in ("paises.mexico.skilla", "paises.mexico.skilla_scraper", "paises.mexico.skilla_parser"):
        assert f"'{m}'" in spec


# REQ-2 (revision Codex)
def test_pie_malformado_no_da_diametro():
    assert parser.diametro("1.5 x 2.5 mm") == "1.5" and parser.diametro("1x1.5mm") == "1"
    for malo in ("1.5.5 x 2.5 mm", "1/2 x 2.5 mm", "", None, "2.5 mm"):
        assert parser.diametro(malo) is None


def test_foto_faltante_conserva_el_producto_sin_tamano():
    html = (FIXTURES / "skilla_bioblue.html").read_text(encoding="utf-8")
    html = html.replace("Bioblue-Nu3-Skilla_3505-3.png", "otra-foto.png")
    recs = parser.parse_page(URL, html, json.loads((FIXTURES / "skilla_ocr.json").read_text(encoding="utf-8")))
    assert ("SKILLA 3505", None) in {(r["nombre_producto"], r["tamano_pellet_mm"]) for r in recs}
