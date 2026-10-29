"""R3.7: en todas las fuentes, proteina_pct sale del parser como float o None."""
import json

import pytest

from conftest import FIXTURES, ROOT
from paises._compartido import aquaxcel_parser, nicovita_parser
from paises.ecuador import agripac_parser, agrizon_parser, biomar_parser, haid_parser
from paises.mexico import apiaba_parser, nutrimar_parser, vimifos_parser

RAW = ROOT / "data" / "raw"


def _read(name):
    return (FIXTURES / name).read_text(encoding="utf-8", errors="replace")


def _agripac():
    return [agripac_parser.parse_product("u", _read(f.name)) for f in FIXTURES.glob("agripac_*.html")]


def _agrizon():
    return agrizon_parser.parse_listing(json.loads(_read("agrizon_biomar_products.json")))


def _aquaxcel():
    return [r for f in FIXTURES.glob("aquaxcel_*listing*.html") for r in aquaxcel_parser.parse_listing(_read(f.name))]


def _biomar():
    return [biomar_parser.parse_product("u", _read(f.name)) for f in FIXTURES.glob("biomar_*.html")]


def _apiaba():
    return apiaba_parser.parse_listing(
        [{"url": f.name, "html": _read(f.name)} for f in FIXTURES.glob("apiaba_*.html") if f.name != "apiaba_camarones.html"])


def _nutrimar():
    fichas = [f.name for f in FIXTURES.glob("nutrimar_ficha_*.txt")]
    return [r for ficha in fichas
            for r in nutrimar_parser.parse_product("u", _read("nutrimar_intensivo.html"), "Nutrimar", _read(ficha))]


def _vimifos():
    paginas = [f.name for f in FIXTURES.glob("vimifos_*.html") if "categoria" not in f.name]
    return [r for p in paginas for r in vimifos_parser.parse_product("u", _read(p))]


def _haid():
    pdfs = sorted((RAW / "haid").glob("*.pdf"))[:4]
    if not pdfs:
        pytest.skip("sin PDF de Haid en data/raw/haid")
    return [r for p in pdfs for r in haid_parser.parse_product("u", "", pdf_bytes=p.read_bytes())]


def _nicovita():
    pdfs = sorted((RAW / "nicovita").glob("*.pdf"))[:4]
    if not pdfs:
        pytest.skip("sin PDF de Nicovita en data/raw/nicovita")
    return [r for p in pdfs for r in nicovita_parser.parse_product("u", "", pdf_bytes=p.read_bytes())]


FUENTES = [_agripac, _agrizon, _aquaxcel, _biomar, _apiaba, _nutrimar, _vimifos, _haid, _nicovita]


@pytest.mark.parametrize("fuente", FUENTES, ids=lambda f: f.__name__.strip("_"))
def test_proteina_pct_es_float_o_vacio_en_todas_las_fuentes(fuente):
    records = fuente()
    assert records
    tipos = {type(r["proteina_pct"]).__name__ for r in records}
    assert tipos <= {"float", "NoneType"}, tipos
    if fuente is not _biomar:
        assert any(r["proteina_pct"] is not None for r in records)
