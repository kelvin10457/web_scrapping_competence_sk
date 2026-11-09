import re
from conftest import FIXTURES
from paises.mexico import apiaba_parser as parser
from paises.mexico import apiaba_scraper as scraper


def _read(name):
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_discover_product_urls_lists_three_shrimp_products():
    urls = scraper.discover_product_urls(_read("apiaba_camarones.html"))
    assert len(urls) == 3
    assert "https://www.acuacultura.com.mx/productos/raceways-20-kg/" in urls


def test_raceways_has_protein_pack_and_micropellet():
    rec = parser.parse_product("u", _read("apiaba_raceways.html"))[0]
    assert rec["empresa"] == "Api-Aba"
    assert rec["nombre_producto"] == "Raceways 20 Kg"
    assert (rec["proteina_pct"], rec["empaque_kg"], rec["tamano_pellet_mm"]) == (45.0, "20", "0.8-1.1")


def test_dorado_40_matches_title_and_analysis():
    rec = parser.parse_product("u", _read("apiaba_dorado40.html"))[0]
    assert rec["proteina_pct"] == 40.0
    assert rec["tamano_pellet_mm"] is None


def test_dorado_35_conflicto_resuelto_por_coincidencia():
    # Titulo 35, texto "35% de proteina" (x2) y analisis garantizado 40:
    # dos fuentes coinciden en 35 -> regla coincidencia, queda en _conflictos.
    recs = parser.parse_listing([{"url": "u35", "html": _read("apiaba_dorado35.html")},
                                 {"url": "u40", "html": _read("apiaba_dorado40.html")}])
    d35, d40 = recs
    assert d35["proteina_pct"] == 35.0
    assert d35["tamano_pellet_mm"] == "1.8-2.32"
    (conf,) = d35["_conflictos"]
    assert (conf["campo"], conf["valor_elegido"], conf["regla"]) == ("proteina_pct", "35", "coincidencia")
    assert "40 (analisis)" in conf["candidatos"]
    assert d40["proteina_pct"] == 40.0 and not d40["_conflictos"]


def _sin_menciones(html: str) -> str:
    return re.sub(r"\d+%\s*de\s+prote", "de prote", html)


def test_dorado_35_sin_texto_detecta_analisis_copiado_de_dorado_40():
    recs = parser.parse_listing([{"url": "u35", "html": _sin_menciones(_read("apiaba_dorado35.html"))},
                                 {"url": "u40", "html": _read("apiaba_dorado40.html")}])
    d35 = recs[0]
    assert d35["_analisis"] == recs[1]["_analisis"]
    assert d35["proteina_pct"] == 35.0
    assert d35["_conflictos"][0]["regla"] == "analisis_copiado_de:" + recs[1]["nombre_producto"]


def test_dorado_35_solo_default_nombre_comercial():
    rec = parser.parse_product("u35", _sin_menciones(_read("apiaba_dorado35.html")))[0]
    assert rec["proteina_pct"] == 35.0
    assert rec["_conflictos"][0]["regla"] == "nombre_comercial"


def test_etapas_de_tres_productos_reales():
    import schema
    for fixture, expected in [("apiaba_dorado40.html", {"post_larva"}),
                              ("apiaba_dorado35.html", {"engorde"}),
                              ("apiaba_raceways.html", set())]:
        r = parser.parse_product("u", _read(fixture))[0]
        assert r.get("_etapas_detectadas") is True
        assert {c for c in schema.ETAPA_COLUMNS if r[c] is True} == {"etapa_" + e for e in expected}
        assert all(r[c] is (False if expected else None) for c in schema.ETAPA_COLUMNS
                   if c.removeprefix("etapa_") not in expected)


def test_etapas_no_contaminadas_por_navegacion_o_relacionados():
    from bs4 import BeautifulSoup
    import schema
    soup = BeautifulSoup(_read("apiaba_raceways.html"), "html.parser")
    # Perturbación de fixture real: el texto ajeno al producto no debe contar.
    for tag in [soup.find("nav"), soup.select_one("article.card-product")]:
        assert tag is not None
        tag.append(BeautifulSoup("<p>larvas precría engorde reproductores</p>", "html.parser"))
    r = parser.parse_product("u", str(soup))[0]
    assert r.get("_etapas_detectadas") is True
    assert all(r[c] is None for c in schema.ETAPA_COLUMNS)
