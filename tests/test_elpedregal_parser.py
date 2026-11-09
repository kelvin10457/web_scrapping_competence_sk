"""R7.5 El Pedregal (Mexico). Fixtures reales del 2026-11-09: pagina principal,
tabla ?t=mp y la salida de `tesseract -l spa` sobre las 5 imagenes de los modales."""
from conftest import FIXTURES

import schema
from paises.mexico import elpedregal_parser as parser
from paises.mexico import elpedregal_scraper as scraper

BASE = "https://el-pedregal.com/alimento/crustaceos"


def _read(name):
    return (FIXTURES / name).read_text(encoding="utf-8")


def _ocr(n):
    return parser.parse_ocr(f"https://el-pedregal.com/img/crustaceos-info-{n}.png", _read(f"elpedregal_info{n}.ocr.txt"))


def _por_nombre(records, nombre):
    return [r for r in records if r["nombre_producto"] == nombre]


# REQ-1
def test_urls_de_imagenes_y_tabla_mp():
    urls = scraper.discover_image_urls(_read("elpedregal_crustaceos.html"))
    assert urls == [f"https://el-pedregal.com/img/crustaceos-info-{n}.png" for n in (1, 2, 4, 3, 5)]
    assert scraper.TABLE_URLS == [f"{BASE}?t=mp"]


# REQ-2
def test_una_fila_por_tamano_y_tipo_por_linea():
    bd = _por_nombre(_ocr(2), "MICROTEK CRUSTÁCEOS BD (45-11)")
    assert [r["tamano_pellet_mm"] for r in bd] == ["0.2", "0.3", "0.5", "0.6", "0.8", "1", "1.4"]
    assert [r["tipo_presentacion"] for r in bd] == ["Microparticulado"] * 3 + ["Extruido"] * 4
    assert bd[0]["empresa"] == "El Pedregal"
    ar = _por_nombre(_ocr(4), "MINIPELET CRUSTÁCEOS AR (40-10)")
    assert [(r["tamano_pellet_mm"], r["tipo_presentacion"]) for r in ar] == [("1.6", None), ("1.8", None)]
    assert len(_ocr(2)) == 7 + 3 + 2


# REQ-3
def test_proteina_y_diametro_con_punto_perdido_por_ocr():
    bd25 = _por_nombre(_ocr(5), "ENGORDA EXTRUIDO 2.1 mm BD (25-8) SHP")
    assert len(bd25) == 1
    assert (bd25[0]["tamano_pellet_mm"], bd25[0]["proteina_pct"]) == ("2.1", 25.0)
    assert bd25[0]["tipo_presentacion"] == "Extruido"
    plus = _por_nombre(_ocr(1), "MICROTEK CRUSTÁCEOS PLUS (45-11)")
    assert [r["proteina_pct"] for r in plus] == [45.0] * 4
    assert [r["tamano_pellet_mm"] for r in plus] == ["0.1", "0.2", "0.3", "0.5"]


# REQ-4
def test_detectar_etapas_engorda_y_preengorda():
    assert schema.detectar_etapas("ENGORDA") == {"engorde"}
    assert schema.detectar_etapas("PREENGORDA") == {"post_transferencia"}
    assert schema.detectar_etapas("Pre-engorda") == {"post_transferencia"}
    assert schema.detectar_etapas("PREENGORDA Y ENGORDA") == {"post_transferencia", "engorde"}


def test_etapas_por_seccion_y_uso():
    def etapas(r):
        return {e for e in schema.ETAPAS if r[f"etapa_{e}"]}

    plus = _ocr(1)[0]
    assert etapas(plus) == {"larva", "post_larva"}  # LARVAS, Zoea 1 hasta PL 15
    rc = _por_nombre(_ocr(2), "MICROTEK CRUSTACEOS RC (40-10)")[0]
    assert etapas(rc) == {"post_larva"}
    ar = _por_nombre(_ocr(4), "MINIPELET CRUSTÁCEOS AR (40-10)")[0]
    assert etapas(ar) == {"post_transferencia"}
    ultra = _por_nombre(_ocr(4), "MINIPELET CRUSTÁCEOS PLUS ULTRA (35-9)")[0]
    assert etapas(ultra) == {"post_transferencia", "engorde"}
    assert etapas(_ocr(3)[0]) == {"engorde"}


# REQ-5
def test_tabla_migajas_post_larva():
    records = parser.parse_table(f"{BASE}?t=mp", _read("elpedregal_crustaceos_t_mp.html"))
    assert len(records) == 8
    first = records[0]
    assert first["nombre_producto"] == "Migajas # 1 Peletizado (45-9)"
    assert first["tamano_pellet_mm"] == "0.6-0.85"
    assert (first["proteina_pct"], first["tipo_presentacion"]) == (45.0, "Pellet")
    assert first["etapa_post_larva"] is True and first["etapa_engorde"] is False
    assert records[-1]["nombre_producto"] == "Migajas # 4 Peletizado (40-8)"
    assert records[-1]["tamano_pellet_mm"] == "2-3"


# REQ-6
def test_registrada_en_mexico():
    import fuentes
    from pathlib import Path

    assert ("mexico", "elpedregal") in fuentes.listar(solo_activas=True)
    spec = (Path(__file__).resolve().parents[1] / "ScraperCompetencia.spec").read_text(encoding="utf-8")
    for mod in ("paises.mexico.elpedregal", "paises.mexico.elpedregal_scraper", "paises.mexico.elpedregal_parser"):
        assert f"'{mod}'" in spec
