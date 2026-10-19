from conftest import FIXTURES
from parsers import apiaba as parser
from scrapers import apiaba as scraper


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


def test_dorado_35_conflicting_protein_left_null():
    # La pagina dice 35% en titulo y texto pero su analisis garantizado muestra 40%.
    rec = parser.parse_product("u", _read("apiaba_dorado35.html"))[0]
    assert rec["proteina_pct"] is None
    assert rec["tamano_pellet_mm"] == "1.8-2.32"
