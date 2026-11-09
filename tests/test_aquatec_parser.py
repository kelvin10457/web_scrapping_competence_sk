"""R7.6: AQUATEC (Mexico) via nutrimentos.com.mx/acuicultura_1."""
from pathlib import Path

from conftest import FIXTURES
from paises.mexico import aquatec_parser as parser
from paises.mexico import aquatec_scraper as scraper

URL = "https://nutrimentos.com.mx/acuicultura_1"


def _records():
    html = (FIXTURES / "aquatec_acuicultura_1.html").read_text(encoding="utf-8")
    return {r["nombre_producto"]: r for r in parser.parse_page(URL, html)}


# REQ-1
def test_una_fila_por_sku_sin_duplicados():
    recs = parser.parse_page(URL, (FIXTURES / "aquatec_acuicultura_1.html").read_text(encoding="utf-8"))
    nombres = [r["nombre_producto"] for r in recs]
    assert len(nombres) == len(set(nombres)) == 11
    assert sum(n.endswith("(Línea Performance)") for n in nombres) == 3
    assert sum(n.endswith("(Línea HD)") for n in nombres) == 5
    assert sum(n.endswith("(Línea Estándar)") for n in nombres) == 3
    assert "AQUATEC 40% - MIGAJA (Línea Estándar)" in nombres  # solo en la ficha
    assert all(r["empresa"] == "AQUATEC" and r["fuente_url"] == URL for r in recs)


# REQ-2
def test_sku_con_ficha_toma_analisis_y_saco():
    r = _records()
    hd = r["AQUATEC 45% - MIGAJA (Línea HD)"]
    assert hd["proteina_pct"] == 45.0 and hd["empaque_kg"] == "25"
    for n in ("AQUATEC 40% - MIGAJA (Línea Performance)", "AQUATEC 40% - MIGAJA (Línea Estándar)"):
        assert r[n]["proteina_pct"] == 40.0 and r[n]["empaque_kg"] == "25"
    assert not any(x.get("_conflictos") for x in r.values())  # titulo y analisis coinciden


# REQ-3
def test_variante_de_plantilla_no_hereda():
    r = _records()
    v = r["AQUATEC 45% - MIGAJA 0.3 mm (Línea HD)"]
    assert v["empaque_kg"] is None
    assert v["proteina_pct"] == 45.0 and v["tamano_pellet_mm"] == "0.3"
    assert all(v[c] is None for c in ("etapa_larva", "etapa_post_larva", "etapa_precria",
                                       "etapa_post_transferencia", "etapa_engorde", "etapa_reproductores"))
    assert r["AQUATEC 25% - PELLET 2.0 mm (Línea Estándar)"]["proteina_pct"] == 25.0
    assert r["AQUATEC 25% - PELLET 2.0 mm (Línea Estándar)"]["empaque_kg"] is None


# REQ-4
def test_tamano_y_tipo_desde_el_nombre():
    r = _records()
    p = r["AQUATEC 40% - PELLET 1.8 mm (Línea HD)"]
    assert p["tamano_pellet_mm"] == "1.8" and p["tipo_presentacion"] == "Pellet"
    m = r["AQUATEC 45% - MIGAJA (Línea HD)"]
    assert m["tamano_pellet_mm"] is None and m["tipo_presentacion"] is None
    assert r["AQUATEC 35% - PELLET 2.0 mm (Línea Performance)"]["tamano_pellet_mm"] == "2"


# REQ-5
def test_scraper_verify_false_solo_para_nutrimentos(monkeypatch):
    llamadas = []

    class R:
        text = "<html></html>"
        is_redirect = False

        def raise_for_status(self):
            pass

    def get(session, url, **kw):
        llamadas.append((url, kw))
        return R()
    monkeypatch.setattr(scraper.netutil, "get", get)
    scraper.scrape_all()
    assert llamadas and all(kw.get("verify") is False for u, kw in llamadas if "nutrimentos.com.mx" in u)
    assert all(kw["headers"]["User-Agent"].startswith("Mozilla/5.0 (Windows") for _, kw in llamadas)
    assert scraper._verify(URL) is False and scraper._verify("https://el-pedregal.com/x") is True


# REQ-6
def test_registrada_en_mexico():
    import fuentes

    assert ("mexico", "aquatec") in fuentes.listar(solo_activas=True)
    spec = (Path(__file__).resolve().parents[1] / "ScraperCompetencia.spec").read_text(encoding="utf-8")
    for mod in ("paises.mexico.aquatec", "paises.mexico.aquatec_scraper", "paises.mexico.aquatec_parser"):
        assert f"'{mod}'" in spec


def test_redireccion_a_otro_dominio_no_lleva_verify_false(monkeypatch):
    llamadas = []

    class R:
        def __init__(self, loc=None):
            self.is_redirect = loc is not None
            self.headers = {"Location": loc} if loc else {}
            self.text = ""

        def raise_for_status(self):
            pass

    def get(session, url, **kw):
        llamadas.append((url, kw["verify"], kw["allow_redirects"]))
        return R("https://otro-dominio.example/catalogo") if "nutrimentos" in url else R()
    monkeypatch.setattr(scraper.netutil, "get", get)
    scraper._get(URL, None)
    assert llamadas == [(URL, False, False), ("https://otro-dominio.example/catalogo", True, False)]


def test_span_dentro_del_titulo_no_parte_la_linea():
    html = (FIXTURES / "aquatec_acuicultura_1.html").read_text(encoding="utf-8")
    assert "AQUATEC 40% - PELLET 1.8 mm" in html
    html = html.replace("AQUATEC 40% - PELLET 1.8 mm", "AQUATEC 40% - <span>PELLET 1.8 mm</span>", 1)
    nombres = {r["nombre_producto"] for r in parser.parse_page(URL, html)}
    assert "AQUATEC 40% - PELLET 1.8 mm (Línea Performance)" in nombres
    assert len(nombres) == 11
