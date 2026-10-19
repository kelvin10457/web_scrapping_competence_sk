import importlib

import fuentes
import schema


def test_every_registered_source_points_to_importable_modules():
    for (pais, empresa), cfg in fuentes.FUENTES.items():
        assert pais in schema.PAIS_VALUES
        importlib.import_module(f"scrapers.{cfg['scraper']}")
        importlib.import_module(f"parsers.{cfg['parser']}")
        assert cfg["kind"] in {"items", "listing"}


def test_listar_filters_by_pais_and_empresa():
    assert ("ecuador", "nicovita") in fuentes.listar(pais="ecuador")
    assert all(p == "ecuador" for p, _ in fuentes.listar(pais="ecuador"))
    assert fuentes.listar(empresa="haid") == [("ecuador", "haid")]
    assert fuentes.listar(pais="nicaragua") == []


def test_run_fuente_unknown_raises():
    import pytest

    with pytest.raises(ValueError):
        fuentes.run_fuente("panama", "nicovita")
