"""R11.2: hatchery de Agrizon (Biomasa de Artemia de Prilabsa + proteina de Bernaqua)."""
import json

import requests

import schema
from conftest import FIXTURES
from paises.ecuador import agrizon_hatchery as hatchery


def _products() -> list[dict]:
    return json.loads((FIXTURES / "agrizon_hatchery_products.json").read_text(encoding="utf-8"))


def _agripac(nombre, proteina=None):
    r = schema.empty_record("Agripac")
    r["nombre_producto"] = nombre
    r["proteina_pct"] = proteina
    return r


# REQ-1
def test_biomasa_artemia_una_fila_prilabsa():
    filas = hatchery.biomasa_artemia(_products())
    assert len(filas) == 1
    r = filas[0]
    assert r["empresa"] == "Prilabsa"
    assert r["nombre_producto"] == "Biomasa de Artemia Congelada"
    assert r["fuente_url"] == "https://agrizon.com/en/products/biomasa-de-artemia-congelada-1-kg"
    assert r["empaque_kg"] == "1"
    assert r["etapa_post_larva"] is True and r["etapa_engorde"] is False
    assert r["proteina_pct"] is None and r["tipo_presentacion"] is None


# REQ-2
def test_proteina_bernaqua_del_body_y_rango_vacio():
    prot = hatchery.proteinas_bernaqua(_products())
    assert prot[hatchery.clave_nombre("Royal Caviar 5-50 400 gr")][0] == 55.0
    assert prot[hatchery.clave_nombre("Royal Seafood 50-100  1500gr")][0] == 54.0
    assert prot[hatchery.clave_nombre("Royal Pepper Protein  1lt")][0] == 11.0
    assert prot[hatchery.clave_nombre("MPEX 300-500  20kg")][0] is None  # "55-60%"


# REQ-3
def test_clave_nombre_empata_agripac_con_agrizon():
    assert hatchery.clave_nombre("MeM 300 – 500") == hatchery.clave_nombre("MEM 300-500  20kg")
    assert hatchery.clave_nombre("Royal Pepper Protein") == hatchery.clave_nombre("Royal Pepper Protein  1lt")
    assert hatchery.clave_nombre("Mpex 100-200") == hatchery.clave_nombre("MPEX 100-200  5kg")


def test_completa_proteina_vacia_y_registra_origen():
    recs = [_agripac("Royal Caviar 5-50"), _agripac("MeM 300 – 500"), _agripac("Feedpac 35%")]
    hatchery.completar_proteina(recs, _products())
    assert recs[0]["proteina_pct"] == 55.0
    assert recs[1]["proteina_pct"] == 55.0
    assert recs[2]["proteina_pct"] is None
    c = recs[0]["_conflictos"][0]
    assert c["campo"] == "proteina_pct" and c["regla"] == "completado:agrizon"
    assert "_conflictos" not in recs[2]


# REQ-4
def test_no_pisa_proteina_de_agripac():
    igual, distinta = _agripac("Royal Caviar 5-50", 55.0), _agripac("Royal Seafood 5-50", 50.0)
    hatchery.completar_proteina([igual, distinta], _products())
    assert igual["proteina_pct"] == 55.0 and "_conflictos" not in igual
    assert distinta["proteina_pct"] == 50.0
    assert distinta["_conflictos"][0]["regla"] == "agripac"


# REQ-6
def test_megalikuid_filas_megasupply():
    filas = {r["nombre_producto"]: r for r in hatchery.megalikuid(_products())}
    assert set(filas) == {"Megalikuid B", "Megalikuid C"}
    b, c = filas["Megalikuid B"], filas["Megalikuid C"]
    assert b["empresa"] == "Megasupply"
    assert b["proteina_pct"] == 6.5 and c["proteina_pct"] == 6.5
    assert b["tamano_pellet_mm"] == "0.05-0.12" and c["tamano_pellet_mm"] == "0.12-0.4"
    assert b["tipo_presentacion"] == "Líquido"
    assert b["etapa_larva"] is True and b["etapa_post_larva"] is True and b["etapa_engorde"] is False
    assert b["empaque_kg"] == "1"


# REQ-5
def test_agrizon_caido_devuelve_vacio(monkeypatch, capsys):
    def falla(*a, **k):
        raise requests.ConnectionError("sin red")
    monkeypatch.setattr(hatchery.agrizon_scraper, "fetch_collection_products", falla)
    hatchery.productos.cache_clear()
    assert hatchery.productos() == []
    assert "Agrizon" in capsys.readouterr().out
    hatchery.productos.cache_clear()
