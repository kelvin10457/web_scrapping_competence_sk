"""R11.3: microalgas Reed para camarón, con fichas reales de ProAqua."""
from pathlib import Path

import fuentes
import schema
from conftest import FIXTURES
from paises.mexico import proaqua, proaqua_parser as parser, proaqua_scraper as scraper

D = FIXTURES / "proaqua" / "reed"
BASE = "https://proaqua.mx/"
NOMBRES = {
    "concentrado-de-microalga-instant-algae-isochrysis-1800": "Instant Algae Isochrysis 1800",
    "concentrado-de-microalga-instant-algae-tetraselmis-3600": "Instant Algae Tetraselmis 3600",
    "concentrado-de-microalga-instant-algae-tw-1200-thalassiosira-weissflogii": "Instant Algae TW 1200",
    "concentrado-de-microalga-instant-algae-tp-1800-thalassiosira-pseudonana": "Instant Algae TP 1800",
    "concentrado-de-microalgas-lpb-para-larvas-juveniles-y-reproductores-de-reed-mariculture": "LPB Frozen Shellfish Diet",
}


def _registros():
    registros = {}
    for slug, nombre in NOMBRES.items():
        filas = parser.parse_reed(BASE + slug + "/", (D / f"{slug}.html").read_text(encoding="utf-8"))
        assert len(filas) == 1
        registros[nombre] = filas[0]
    return registros


# REQ-1
def test_listado_solo_cinco_microalgas_para_camaron():
    productos = parser.productos_reed_de_listado((D / "listado.html").read_text(encoding="utf-8"))
    assert len(productos) == 5
    assert {url for url, _ in productos} == {BASE + slug + "/" for slug in NOMBRES}
    assert {p.stem for p in D.glob("*.html")} == {"listado", *NOMBRES}
    assert {r["empresa"] for r in _registros().values()} == {"Reed Mariculture"}
    assert ("mexico", "proaqua") in fuentes.listar(solo_activas=True)


# REQ-2
def test_nombres_exactos():
    for nombre, registro in _registros().items():
        assert registro["nombre_producto"] == nombre


# REQ-3
def test_tamano_celular_primera_dimension_en_mm():
    esperados = [None, None, "0.006-0.02", "0.0045-0.008", "0.006-0.015"]
    assert [r["tamano_pellet_mm"] for r in _registros().values()] == esperados


# REQ-4
def test_proteina_publicada_y_empaque_vacio():
    registros = list(_registros().values())
    assert [r["proteina_pct"] for r in registros] == [None, None, None, None, 52.0]
    assert all(r["empaque_kg"] is None for r in registros)


# REQ-5
def test_etapas_solo_del_texto_propio_y_aplicacion_camaron():
    for nombre, r in _registros().items():
        esperado = None if nombre == "Instant Algae Isochrysis 1800" else True
        assert r["etapa_larva"] is esperado
        for columna in schema.ETAPA_COLUMNS:
            if columna != "etapa_larva":
                assert r[columna] is (None if esperado is None else False)
        assert r["tipo_presentacion"] is None


# REQ-6
def test_scraper_y_run_preservan_las_doce_filas_y_agregan_cinco(monkeypatch):
    visitadas = []

    def obtener(url, session):
        visitadas.append(url)
        if url == scraper.LISTADO_URL:
            archivo = D.parent / "camaron_p1.html"
        elif url.startswith(scraper.LISTADO_URL + "?page="):
            archivo = D.parent / f"camaron_p{url.rsplit('=', 1)[1]}.html"
        elif url == "https://proaqua.mx/reed-mariculture/":
            archivo = D / "listado.html"
        else:
            slug = url.rstrip("/").rsplit("/", 1)[1]
            archivo = (D if slug in NOMBRES else D.parent) / f"{slug}.html"
        return type("Respuesta", (), {"text": archivo.read_text(encoding="utf-8")})()

    anteriores = [r for p in sorted(D.parent.glob("*.html")) if not p.name.startswith("camaron_p")
                  for r in parser.parse_producto(BASE + p.stem + "/", p.read_text(encoding="utf-8"))]
    assert len(anteriores) == 12
    monkeypatch.setattr(scraper, "_get", obtener)
    registros = proaqua.run()
    assert len(registros) == 17
    assert sorted((r for r in registros if r["empresa"] != "Reed Mariculture"),
                  key=lambda r: (r["nombre_producto"], r["tamano_pellet_mm"] or "")) == sorted(
                      anteriores, key=lambda r: (r["nombre_producto"], r["tamano_pellet_mm"] or ""))
    assert {r["nombre_producto"] for r in registros if r["empresa"] == "Reed Mariculture"} == set(NOMBRES.values())
    assert len(visitadas) == len(set(visitadas)) == 18
    spec = (Path(__file__).resolve().parents[1] / "ScraperCompetencia.spec").read_text(encoding="utf-8")
    for modulo in ("proaqua", "proaqua_parser", "proaqua_scraper"):
        assert f"'paises.mexico.{modulo}'" in spec
