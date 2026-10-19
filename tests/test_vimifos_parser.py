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


def test_micras_converted_and_multiple_proteins_split_in_skus():
    race = parser.parse_product("u", _read("vimifos_race_way.html"))
    assert race[0]["tamano_pellet_mm"] == "0.4-0.6"
    assert race[2]["tamano_pellet_mm"] == "1"
    # Celda real "30%, 35%, 40%" con un solo calibre "2.0MM - 6MM" (M=1, N=3):
    # 3 filas (una por SKU), mismo calibre, sin conflicto.
    bumper = parser.parse_product("u", _read("vimifos_bumper_crop.html"))
    assert len(bumper) == 5
    fin = bumper[2:]
    assert [r["proteina_pct"] for r in fin] == [30.0, 35.0, 40.0]
    assert [r["nombre_producto"] for r in fin] == ["Bumper Crop 30%", "Bumper Crop 35%", "Bumper Crop 40%"]
    assert {r["tamano_pellet_mm"] for r in fin} == {"2-6"}
    assert all(not r.get("_conflictos") for r in fin)


def _tabla(proteina: str, tamano: str) -> str:
    return (f"<table><tr><td>LINEA X</td><td>ENGORDA</td></tr>"
            f"<tr><td>% PROTEINA</td><td>{proteina}</td></tr>"
            f"<tr><td>TAMANO PARTICULA</td><td>{tamano}</td></tr></table>")


def test_varias_proteinas_m_igual_n_empareja_en_orden():
    recs = parser.parse_product("u", _tabla("35%, 40%", "1.2MM, 2.0MM"))
    assert [(r["proteina_pct"], r["tamano_pellet_mm"]) for r in recs] == [(35.0, "1.2"), (40.0, "2")]


def test_varias_proteinas_m_distinto_n_deja_texto_y_registra_conflicto():
    recs = parser.parse_product("u", _tabla("30%, 35%, 40%", "1.2MM, 2.0MM"))
    assert len(recs) == 3
    assert {r["tamano_pellet_mm"] for r in recs} == {"1.2MM, 2.0MM"}
    assert all(r["_conflictos"][0]["regla"] == "calibre_no_emparejable" for r in recs)


def test_asociacion_explicita_manda_sobre_el_orden():
    recs = parser.parse_product("u", _tabla("35% (2.0 mm), 40% (1.2 mm)", "1.2MM, 2.0MM"))
    assert [(r["proteina_pct"], r["tamano_pellet_mm"]) for r in recs] == [(35.0, "2"), (40.0, "1.2")]


def test_strong_breed_is_reproductores():
    rec = parser.parse_product("u", _read("vimifos_strong_breed.html"))[0]
    assert rec["etapa_competidor"] == "reproductores"
    assert rec["tamano_pellet_mm"] == "2.4"
