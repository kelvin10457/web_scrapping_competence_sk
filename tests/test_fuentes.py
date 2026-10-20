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


def test_nicovita_pausada_no_corre_sin_argumentos_pero_sigue_registrada():
    for pais in ("ecuador", "honduras", "mexico"):
        assert not fuentes.activa(pais, "nicovita")
        assert (pais, "nicovita") in fuentes.listar()  # build_master sigue incluyendo su CSV
    assert all(e != "nicovita" for _, e in fuentes.listar(solo_activas=True))
    assert ("mexico", "vimifos") in fuentes.listar(solo_activas=True)


def test_todo_modulo_que_usa_netutil_lo_importa():
    # Regresion 2026-10-19: aquaxcel_scraper usaba netutil.get sin importarlo.
    from pathlib import Path
    src = Path(__file__).resolve().parents[1] / "src"
    sin_import = [str(p.relative_to(src)) for p in src.rglob("*.py")
                  if "netutil." in p.read_text(encoding="utf-8") and p.name != "netutil.py"
                  and "import netutil" not in p.read_text(encoding="utf-8")]
    assert sin_import == []


def test_cache_de_scrapers_vive_en_data_junto_al_exe(monkeypatch, tmp_path):
    # Regresion 2026-10-20: nicovita/haid/nutrimar calculaban data/raw desde
    # __file__, que en el .exe es la carpeta temporal _MEIxxxx (se borra al
    # cerrar): el .exe no veia las paginas de Nicovita guardadas a mano.
    import importlib
    import sys

    import netutil
    from paises._compartido import nicovita_scraper
    from paises.ecuador import haid_scraper
    from paises.mexico import nutrimar_scraper

    for mod in (nicovita_scraper, haid_scraper, nutrimar_scraper):
        assert mod.RAW_DIR.parent == netutil.DATA_DIR / "raw"

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(tmp_path / "ScraperCompetencia.exe"))
    try:
        assert importlib.reload(netutil).DATA_DIR == tmp_path / "data"
    finally:
        monkeypatch.undo()
        importlib.reload(netutil)
