import importlib

import pytest

import fuentes
import schema


def test_every_registered_source_has_a_run_function():
    for pais, empresa in fuentes.listar():
        assert pais in schema.PAIS_VALUES
        modulo = importlib.import_module(f"paises.{pais}.{empresa}")
        assert callable(modulo.run)


def test_every_pais_has_a_package_even_without_sources():
    for pais in schema.PAIS_VALUES:
        assert isinstance(importlib.import_module(f"paises.{pais}").FUENTES, list)


def test_listar_filters_by_pais_and_empresa():
    assert ("ecuador", "nicovita") in fuentes.listar(pais="ecuador")
    assert all(p == "ecuador" for p, _ in fuentes.listar(pais="ecuador"))
    assert fuentes.listar(empresa="haid") == [("ecuador", "haid")]
    assert {p for p, _ in fuentes.listar(empresa="nicovita")} == {"ecuador", "honduras", "mexico"}
    assert fuentes.listar(pais="nicaragua") == []


def test_run_fuente_unknown_raises():
    with pytest.raises(ValueError):
        fuentes.run_fuente("panama", "nicovita")
