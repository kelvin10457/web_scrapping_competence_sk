"""R7.9: ProAqua (Mexico), alimentos formulados de la categoria Camaron."""
import fuentes
from conftest import FIXTURES
from paises.mexico import proaqua_parser as parser

D = FIXTURES / "proaqua"
BASE = "https://proaqua.mx/"


def _parse(slug):
    return parser.parse_producto(BASE + slug + "/", (D / f"{slug}.html").read_text(encoding="utf-8"))


def _uno(slug):
    recs = _parse(slug)
    assert len(recs) == 1
    return recs[0]


# REQ-1
def test_listado_solo_formulados():
    productos = []
    for n in (1, 2, 3):
        productos += parser.productos_de_listado((D / f"camaron_p{n}.html").read_text(encoding="utf-8"))
    slugs = sorted(u.rstrip("/").rsplit("/", 1)[1] for u, _ in productos)
    assert len(slugs) == 9 and len(set(slugs)) == 9
    assert sorted(p.name[:-5] for p in D.glob("*.html") if not p.name.startswith("camaron_p")) == slugs
    assert _uno("epifeed-mbf-cu-ete-epicore")["empresa"] == "Epicore"
    assert _uno("biogrow-formula-4-300-500-micras-pl-saco-25-kilos")["empresa"] == "Biogrow"


# REQ-2
def test_variantes_por_columna_y_por_ficha():
    lhf = {r["nombre_producto"]: r for r in _parse("epifeed-lhf-bote-1-litro-epicore")}
    assert set(lhf) == {"Epifeed LHF1", "Epifeed LHF2"}
    assert lhf["Epifeed LHF1"]["tamano_pellet_mm"] == "0.03" and lhf["Epifeed LHF2"]["tamano_pellet_mm"] == "0.085"
    assert all(r["proteina_pct"] == 15.0 for r in lhf.values())
    e300 = _uno("epibal-300-cu-ete-20-kilos-epicore")
    assert e300["nombre_producto"] == "Epibal-300" and e300["tamano_pellet_mm"] == "0.3" and e300["proteina_pct"] == 49.0
    assert _uno("epibal-500-cu-ete-20-kilos-epicore")["tamano_pellet_mm"] == "0.5"
    xt = _parse("alimento-para-camaron-biogrow-xt-ultra-adicionado-con-qrill-orego-stim-optimax-a-y-glucan-mos")
    assert sorted(r["tamano_pellet_mm"] for r in xt) == ["0.3", "0.6", "0.8"]
    assert all(r["proteina_pct"] == 45.0 and r["nombre_producto"] == "Biogrow XT ultra" for r in xt)


def test_variante_nombrada_sin_columna_no_se_reparte():
    html = (D / "epibal-300-cu-ete-20-kilos-epicore.html").read_text(encoding="utf-8")
    html = html.replace("<title>Epibal-300", "<title>Epibal-200")
    recs = parser.parse_producto(BASE + "x/", html)
    assert len(recs) == 1 and recs[0]["nombre_producto"] == "Epibal-200"
    assert recs[0]["tamano_pellet_mm"] is None and recs[0]["proteina_pct"] == 49.0


# REQ-3
def test_tamano_y_empaque():
    f1 = _uno("biogrow-formula-1-00-50-micras-zoea-lata-1-lilbra")
    assert f1["tamano_pellet_mm"] == "0-0.05" and f1["empaque_kg"] == "0.45" and f1["proteina_pct"] == 60.4
    f2 = _uno("biogrow-formula-2-040-150-micras-mysis-lata-1-libra")
    assert f2["tamano_pellet_mm"] == "0.04-0.15"
    assert _uno("biogrow-formula-3-100-300-micras-mysis-pl-cubeta-5-kilos")["empaque_kg"] == "5"
    assert _uno("biogrow-formula-4-300-500-micras-pl-saco-25-kilos")["empaque_kg"] == "25"
    assert _uno("epibal-300-cu-ete-20-kilos-epicore")["empaque_kg"] == "20"
    assert all(r["empaque_kg"] is None for r in _parse("epifeed-lhf-bote-1-litro-epicore"))
    mbf = _uno("epifeed-mbf-cu-ete-epicore")
    assert mbf["empaque_kg"] is None and mbf["tamano_pellet_mm"] is None and mbf["proteina_pct"] == 43.0


# REQ-4
def test_etapas_y_presentacion():
    f1 = _uno("biogrow-formula-1-00-50-micras-zoea-lata-1-lilbra")
    assert f1["etapa_larva"] is True and f1["etapa_post_larva"] is False
    assert f1["tipo_presentacion"] == "Microencapsulado"
    f2 = _uno("biogrow-formula-2-040-150-micras-mysis-lata-1-libra")
    assert f2["etapa_larva"] is True and f2["etapa_post_larva"] is True
    f4 = _uno("biogrow-formula-4-300-500-micras-pl-saco-25-kilos")
    assert f4["etapa_post_larva"] is True and f4["tipo_presentacion"] == "Extruido"
    mbf = _uno("epifeed-mbf-cu-ete-epicore")
    assert mbf["etapa_reproductores"] is True and mbf["etapa_larva"] is False
    e300 = _uno("epibal-300-cu-ete-20-kilos-epicore")
    assert e300["etapa_post_larva"] is True and e300["etapa_larva"] is False
    assert e300["tipo_presentacion"] == "Granulado"
    lhf = _parse("epifeed-lhf-bote-1-litro-epicore")
    assert all(r["etapa_larva"] is True and r["etapa_post_larva"] is False for r in lhf)
    assert all(r["tipo_presentacion"] == "Líquido" for r in lhf)
    xt = _parse("alimento-para-camaron-biogrow-xt-ultra-adicionado-con-qrill-orego-stim-optimax-a-y-glucan-mos")
    assert all(r["etapa_larva"] is None and r["tipo_presentacion"] is None for r in xt)


# REQ-5
def test_registrada_en_mexico():
    assert ("mexico", "proaqua") in fuentes.listar(solo_activas=True)
    spec = (FIXTURES.parent.parent / "ScraperCompetencia.spec").read_text(encoding="utf-8")
    for m in ("paises.mexico.proaqua", "paises.mexico.proaqua_scraper", "paises.mexico.proaqua_parser"):
        assert f"'{m}'" in spec
