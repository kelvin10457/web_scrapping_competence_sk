"""R7.7: Prilabsa (Ecuador, distribuidor) — catalogo PDF de alimentos."""
from pathlib import Path

import schema
from conftest import FIXTURES
from paises.ecuador import prilabsa_parser as parser
from paises.ecuador import prilabsa_scraper as scraper

PDF = FIXTURES / "prilabsa_catalogo_p3-23.pdf"
_CACHE = {}


def _recs():
    if "r" not in _CACHE:
        _CACHE["r"] = parser.parse_pdf(PDF)
    return _CACHE["r"]


def _por_nombre():
    return {r["nombre_producto"]: r for r in _recs()}


# REQ-1
def test_empresa_por_indice_y_19_fichas():
    recs = _recs()
    assert {r["empresa"] for r in recs} == {"Zeigler", "Mackay Marine", "Higashimaru"}
    fichas = {r["_ficha"] for r in recs}
    assert len(fichas) == 19
    assert len(recs) == 48
    emp = {r["_ficha"]: r["empresa"] for r in recs}
    assert emp["LARVA Z - PLUS"] == "Zeigler" and emp["PRE- MIX PL"] == "Zeigler"
    assert emp["CISTOS DE ARTEMIA"] == "Mackay Marine" and emp["ESPIRULINA"] == "Mackay Marine"
    assert emp["P. VANNAMEI"] == "Higashimaru" and emp["ZM FEED"] == "Higashimaru"
    assert len({r["nombre_producto"] for r in recs}) == len(recs)


# REQ-2
def test_una_fila_por_tamano_en_mm():
    r = _por_nombre()
    zplus = sorted(x["tamano_pellet_mm"] for x in _recs() if x["_ficha"] == "LARVA Z - PLUS")
    assert zplus == sorted(["<0.05", "<0.1", "0.1-0.15", "0.15-0.25"])
    assert sorted(x["tamano_pellet_mm"] for x in _recs() if x["_ficha"] == "EZ ARTEMIA") == ["0.05-0.2", "0.3-0.5"]
    assert sorted(x["tamano_pellet_mm"] for x in _recs() if x["_ficha"] == "Z PRO") == ["0.15", "0.25", "0.35"]
    assert sorted(x["tamano_pellet_mm"] for x in _recs() if x["_ficha"] == "P. VANNAMEI") == \
        ["0.03-0.05", "0.08-0.13", "0.2-0.3"]
    sin = [x for x in _recs() if x["_ficha"] == "EZ MATE"]
    assert len(sin) == 1 and sin[0]["tamano_pellet_mm"] is None
    assert "LARVA Z - PLUS <50 micras" in r


# REQ-3
def test_proteina_unica_o_vacia():
    by = {x["_ficha"]: x["proteina_pct"] for x in _recs()}
    assert by["LARVA Z - PLUS"] == 50.0 and by["Z PRO"] == 44.0 and by["CISTOS DE ARTEMIA"] == 54.0
    assert by["EZ ARTEMIA"] is None       # 52% peso seco y 14% liquido
    assert by["EZ ARTEMIA ULTRA"] is None  # 12% (peso seco 45%)
    assert by["ESPIRULINA"] is None        # 60-70%
    assert by["ZM FEED"] is None           # 58% y 55%: dos productos


# REQ-4
def test_empaque_de_envases_sin_dosis():
    by = {x["_ficha"]: x["empaque_kg"] for x in _recs()}
    assert by["LARVA Z - PLUS"] == "0.5"
    assert by["CISTOS DE ARTEMIA"] == "0.454,7"
    assert by["REDI-MATE"] == "15,5"   # no 3,5 kg / dia
    assert by["SHRIMP MEAL"] == "16.3,20"
    assert by["P. VANNAMEI"] == "1"    # no la dosis en g


# REQ-5
def test_tipo_y_etapas():
    by = {x["_ficha"]: x for x in _recs()}
    assert by["LARVA Z - PLUS"]["tipo_presentacion"] == "Microparticulado"
    assert by["EZ LARVA"]["tipo_presentacion"] == "Microencapsulado"
    assert by["CISTOS DE ARTEMIA"]["tipo_presentacion"] == "Quistes de artemia"
    assert by["P. VANNAMEI"]["tipo_presentacion"] == "Microparticulado"
    assert by["SHRIMP MEAL"]["tipo_presentacion"] is None
    assert by["LARVA Z - PLUS"]["etapa_larva"] is True
    assert by["EZ MATE"]["etapa_reproductores"] is True


# REQ-6
def test_tamano_menor_que_no_inventa_minimo():
    assert schema.parse_particula_range("<0.05") == (None, 0.05)
    assert schema.parse_particula_range("0.1-0.15") == (0.1, 0.15)


# REQ-7
def test_registrada_y_scraper_con_ua(tmp_path, monkeypatch):
    import fuentes

    assert ("ecuador", "prilabsa") in fuentes.listar(solo_activas=True)
    spec = (Path(__file__).resolve().parents[1] / "ScraperCompetencia.spec").read_text(encoding="utf-8")
    for mod in ("paises.ecuador.prilabsa", "paises.ecuador.prilabsa_scraper", "paises.ecuador.prilabsa_parser"):
        assert f"'{mod}'" in spec
    enviados = []

    class R:
        content = b"%PDF-1.5 x"

        def raise_for_status(self):
            pass

    monkeypatch.setattr(scraper, "RAW_DIR", tmp_path)
    monkeypatch.setattr(scraper.netutil, "get", lambda s, url, **kw: enviados.append(kw) or R())
    path = scraper.descargar(max_dias=0)
    assert path.read_bytes() == R.content
    assert enviados[0]["headers"]["User-Agent"].startswith("Mozilla/5.0 (Windows")
    scraper.descargar(max_dias=30)
    assert len(enviados) == 1  # cache


# Revision Codex R7.7
def test_envase_por_tamano_z_pro():
    by = {x["tamano_pellet_mm"]: x["empaque_kg"] for x in _recs() if x["_ficha"] == "Z PRO"}
    assert by == {"0.15": "0.5", "0.25": "4", "0.35": "4"}


def test_espirulina_tamanos_bajo_titulo_sin_asignar_envase():
    rs = [x for x in _recs() if x["_ficha"] == "ESPIRULINA"]
    assert sorted(x["tamano_pellet_mm"] for x in rs) == ["0.008-0.01", "0.02"]
    assert all(x["empaque_kg"] == "0.5,1" for x in rs)  # la ficha no dice que envase va con cada tamano


def test_encabezado_de_tabla_no_marca_larva():
    rs = [x for x in _recs() if x["_ficha"] == "SHRIMP MEAL"]
    assert rs and all(not x["etapa_larva"] for x in rs)
    assert all(x["etapa_post_larva"] and x["etapa_precria"] for x in rs)
