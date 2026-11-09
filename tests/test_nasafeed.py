"""R8.10: NasaFeed Aquanasa Linea Premium (Panama), ficha PDF (copia de Wayback)."""
import requests

import fuentes
from conftest import FIXTURES
from paises.panama import nasafeed_parser as parser
from paises.panama import nasafeed_scraper as scraper

PDF = (FIXTURES / "nasafeed_linea_premium.pdf").read_bytes()


def _recs():
    return {r["nombre_producto"]: r for r in parser.parse_pdf(scraper.WAYBACK_URL, PDF)}


# REQ-1
def test_tres_filas_por_proteina_sin_tamano():
    r = _recs()
    assert sorted(r) == ["AQUANASA 25", "AQUANASA 30", "AQUANASA 35"]
    assert [r[n]["proteina_pct"] for n in sorted(r)] == [25.0, 30.0, 35.0]
    assert all(x["empresa"] == "NasaFeed" and x["tamano_pellet_mm"] is None for x in r.values())
    assert all(x["fuente_url"] == scraper.WAYBACK_URL for x in r.values())


# REQ-2
def test_empaque_tipo_y_etapas():
    for x in _recs().values():
        assert x["empaque_kg"] == "45.36" and x["tipo_presentacion"] == "Pellet"
        assert x["etapa_post_larva"] and x["etapa_precria"] and x["etapa_post_transferencia"] and x["etapa_engorde"]
        assert x["etapa_larva"] is False and x["etapa_reproductores"] is False


# REQ-3
def test_usa_wayback_si_el_sitio_no_responde(monkeypatch):
    pedidas = []

    def falso_get(session, url, **kw):
        pedidas.append(url)
        if url == scraper.PDF_URL:
            raise requests.ConnectionError("timeout")
        r = requests.Response()
        r.status_code, r._content = 200, PDF
        return r

    monkeypatch.setattr(scraper.netutil, "get", falso_get)
    url, contenido = scraper.descargar()
    assert pedidas == [scraper.PDF_URL, scraper.WAYBACK_URL]
    assert url == scraper.WAYBACK_URL and contenido == PDF
    assert "id_/" in scraper.WAYBACK_URL


import pytest  # noqa: E402


@pytest.mark.parametrize("falla", ["html", "captcha"])
def test_html_o_captcha_tambien_pasan_a_wayback(monkeypatch, falla):
    def falso_get(session, url, **kw):
        if url == scraper.PDF_URL and falla == "captcha":
            raise scraper.netutil.BlockedError(url, "captcha", None)
        r = requests.Response()
        r.status_code = 200
        r._content = b"<html>hola</html>" if url == scraper.PDF_URL else PDF
        return r

    monkeypatch.setattr(scraper.netutil, "get", falso_get)
    assert scraper.descargar() == (scraper.WAYBACK_URL, PDF)


def test_wayback_que_no_es_pdf_falla():
    import requests as rq

    def falso_get(session, url, **kw):
        r = rq.Response()
        r.status_code, r._content = 200, b"<html/>"
        return r

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(scraper.netutil, "get", falso_get)
        with pytest.raises(scraper.NoEsPDF):
            scraper.descargar()


# REQ-4
def test_registrada_en_panama():
    assert ("panama", "nasafeed") in fuentes.listar(solo_activas=True)
    spec = (FIXTURES.parent.parent / "ScraperCompetencia.spec").read_text(encoding="utf-8")
    for m in ("paises.panama.nasafeed", "paises.panama.nasafeed_scraper", "paises.panama.nasafeed_parser"):
        assert f"'{m}'" in spec
