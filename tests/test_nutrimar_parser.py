from conftest import FIXTURES
from parsers import nutrimar as parser
from scrapers import nutrimar as scraper


def _read(name):
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_discover_skips_non_feed_links():
    urls = scraper.discover_product_urls(_read("nutrimar_listing.html"))
    assert "https://www.nutrimar.mx/ez-larva" in urls
    assert "https://www.nutrimar.mx/krill" not in urls
    assert "https://www.nutrimar.mx/engorda-nutrimar" not in urls


def test_parse_product_is_name_only():
    rec = parser.parse_product("https://www.nutrimar.mx/ez-larva", _read("nutrimar_ez_larva.html"))[0]
    assert rec["empresa"] == "Nutrimar"
    assert rec["nombre_producto"] == "EZ Larva"
    assert rec["proteina_pct"] is None and rec["tamano_pellet_mm"] is None and rec["empaque_kg"] is None
    assert parser.parse_product("u", _read("nutrimar_intensivo.html"))[0]["nombre_producto"] == "Intensivo"
