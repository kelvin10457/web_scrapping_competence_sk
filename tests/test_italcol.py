"""R8.11: Italcol AQUACAMARON 35 como fuente de Panama."""
import fuentes
from conftest import FIXTURES
from paises.panama import italcol_parser as parser

URL = "https://italcol.com/producto/camaron-levante/"


def _rec():
    recs = parser.parse_page(URL, (FIXTURES / "italcol_camaron_levante.html").read_text(encoding="utf-8"))
    assert len(recs) == 1
    return recs[0]


# REQ-1
def test_una_fila_con_proteina():
    r = _rec()
    assert r["empresa"] == "Italcol" and r["nombre_producto"] == "AQUACAMARON 35"
    assert r["proteina_pct"] == 35.0 and r["fuente_url"] == URL


# REQ-2
def test_etapa_engorde_y_vacios():
    r = _rec()
    assert r["etapa_engorde"] is True and r["etapa_precria"] is False
    assert r["tamano_pellet_mm"] is None and r["tipo_presentacion"] is None and r["empaque_kg"] is None


def test_html_cambiado_no_rompe_ni_inventa():
    html = (FIXTURES / "italcol_camaron_levante.html").read_text(encoding="utf-8")
    envuelto = html.replace("<p><strong>COMPOSICIÓN GARANTIZADA</strong></p>",
                            "<div><p><strong>COMPOSICIÓN GARANTIZADA</strong></p></div>")
    assert envuelto != html
    r = parser.parse_page(URL, envuelto)[0]
    assert r["proteina_pct"] == 35.0 and r["etapa_engorde"] is True
    sin_h = html.replace("product_title", "otra_clase").replace("AQUACAMARON 35 - Italcol</title>",
                                                                "AQUACAMARON 35 | Italcol</title>")
    assert parser.parse_page(URL, sin_h)[0]["nombre_producto"] == "AQUACAMARON 35"


# REQ-3
def test_registrada_en_panama():
    assert ("panama", "italcol") in fuentes.listar(solo_activas=True)
    spec = (FIXTURES.parent.parent / "ScraperCompetencia.spec").read_text(encoding="utf-8")
    for m in ("paises.panama.italcol", "paises.panama.italcol_scraper", "paises.panama.italcol_parser"):
        assert f"'{m}'" in spec
