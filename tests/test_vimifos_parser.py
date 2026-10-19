from conftest import FIXTURES
from paises.mexico import vimifos_parser as parser
from paises.mexico import vimifos_scraper as scraper


def _read(name):
    return (FIXTURES / name).read_text(encoding="utf-8", errors="replace")


def test_discover_product_urls_from_category():
    urls = scraper.discover_product_urls(_read("vimifos_categoria_camaron.html"))
    assert "https://vimifos.com/producto/xtrudix" in urls
    assert len(urls) == 6


def test_xtrudix_four_products():
    records = parser.parse_product("https://vimifos.com/producto/xtrudix", _read("vimifos_xtrudix.html"))
    assert [r["nombre_producto"] for r in records] == ["Xtrudix 00", "Xtrudix 0", "Xtrudix 1", "Xtrudix 2"]
    first, last = records[0], records[-1]
    assert first["empresa"] == "Vimifos"
    assert (first["tamano_pellet_mm"], first["proteina_pct"], first["empaque_kg"]) == ("0.8", 40.0, "25")
    assert first["tipo_presentacion"] == "Extruido"
    assert (last["tamano_pellet_mm"], last["proteina_pct"]) == ("1.8", 38.0)


def test_micras_converted_and_multiple_proteins_left_null():
    race = parser.parse_product("u", _read("vimifos_race_way.html"))
    assert race[0]["tamano_pellet_mm"] == "0.4-0.6"
    assert race[2]["tamano_pellet_mm"] == "1"
    bumper = parser.parse_product("u", _read("vimifos_bumper_crop.html"))
    assert bumper[2]["proteina_pct"] is None  # "30%, 35%, 40%": no se elige uno
    assert bumper[2]["tamano_pellet_mm"] == "2-6"


def test_strong_breed_is_reproductores():
    rec = parser.parse_product("u", _read("vimifos_strong_breed.html"))[0]
    assert rec["etapa_competidor"] == "reproductores"
    assert rec["tamano_pellet_mm"] == "2.4"
