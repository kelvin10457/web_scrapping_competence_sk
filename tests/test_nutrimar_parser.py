from conftest import FIXTURES
from paises.mexico import nutrimar_parser as parser
from paises.mexico import nutrimar_scraper as scraper


def _read(name):
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_discover_skips_non_feed_links():
    urls = scraper.discover_product_urls(_read("nutrimar_listing.html"))
    assert "https://www.nutrimar.mx/ez-larva" in urls
    assert "https://www.nutrimar.mx/krill" not in urls
    assert "https://www.nutrimar.mx/engorda-nutrimar" not in urls


def test_parse_product_is_name_only():
    rec = parser.parse_product("https://www.nutrimar.mx/ez-larva", _read("nutrimar_ez_larva.html"))[0]
    assert rec["empresa"] == "Nutrimar"
    assert rec["nombre_producto"] == "EZ Larva"
    assert rec["proteina_pct"] is None and rec["tamano_pellet_mm"] is None and rec["empaque_kg"] is None
    assert parser.parse_product("u", _read("nutrimar_intensivo.html"))[0]["nombre_producto"] == "Intensivo"


# --- RONDA2 R2.4: fichas tecnicas -------------------------------------------
def test_find_ficha_pdf_o_imagen_de_tabla():
    extensivo, pl_raceway = _read("nutrimar_ficha_snippets.html").split("<!-- pl-raceway-40-9 -->")
    assert scraper.find_ficha(extensivo) == (
        "imagen", "https://static.wixstatic.com/media/9bbeda_c349f38ffe684808a068c064cc725e31~mv2.png")
    assert scraper.find_ficha(pl_raceway) == (
        "pdf", "https://www.nutrimar.mx/_files/ugd/5003b5_20c38972191f48b6b3a4763452ce7a7c.pdf")
    assert scraper.find_ficha("<html>sin ficha</html>") is None


def test_marca_zeigler_segun_categoria():
    marcas = scraper.marcas_por_slug({
        "larvario-zeigler": '<a href="https://www.nutrimar.mx/ez-larva"></a><a href="https://www.nutrimar.mx/larvario-zeigler"></a>',
        "engorda-nutrimar": '<a href="https://www.nutrimar.mx/intensivo"></a>',
    })
    assert marcas == {"ez-larva": "Zeigler", "intensivo": "Nutrimar"}


def test_ficha_pdf_pl_raceway_validada():
    # Ficha real: Proteina cruda Minimo 40,0%; saco de 20 kg; 400-600 / 600-850 / 850-1200 micrones.
    (rec,) = parser.parse_product("https://www.nutrimar.mx/pl-raceway-40-9", _read("nutrimar_intensivo.html"),
                                  "Zeigler", _read("nutrimar_ficha_pl_raceway_40_9.txt"))
    assert rec["empresa"] == "Zeigler" and rec["fuente_url"] == "https://www.nutrimar.mx/pl-raceway-40-9"
    assert (rec["proteina_pct"], rec["tamano_pellet_mm"], rec["empaque_kg"]) == (40.0, "0.4-1.2", "20")


def test_ficha_pdf_semi_intensivo_dos_proteinas_dos_skus():
    # Ficha real: "Proteina Minimo 35.0/30.0%", 25 kg, pellets 1.6 a 2.5 mm.
    recs = parser.parse_product("u", _read("nutrimar_intensivo.html"), "Nutrimar", _read("nutrimar_ficha_semi_intensivo.txt"))
    assert [(r["nombre_producto"], r["proteina_pct"]) for r in recs] == [("Intensivo 35%", 35.0), ("Intensivo 30%", 30.0)]
    assert {(r["tamano_pellet_mm"], r["empaque_kg"]) for r in recs} == {("1.6-2.5", "25")}


def test_ficha_imagen_ocr_extensivo_validada():
    # Imagen real "Tabla de Analisis Nutricional": Proteina cruda Minimo 35,0%.
    (rec,) = parser.parse_product("u", _read("nutrimar_intensivo.html"), "Nutrimar",
                                  _read("nutrimar_ficha_extensivo_ocr.txt"), ficha_ocr=True)
    assert rec["proteina_pct"] == 35.0 and not rec.get("_conflictos")


def test_ocr_fuera_de_rango_queda_null_y_se_registra():
    texto = "Proteina cruda Minimo 3,5%\nPellet 24 mm"
    (rec,) = parser.parse_product("u", _read("nutrimar_intensivo.html"), "Nutrimar", texto, ficha_ocr=True)
    assert rec["proteina_pct"] is None and rec["tamano_pellet_mm"] is None
    assert sorted(c["campo"] for c in rec["_conflictos"]) == ["proteina_pct", "tamano_pellet_mm"]
    assert {c["regla"] for c in rec["_conflictos"]} == {"ocr_fuera_de_rango"}
    # El mismo texto en un PDF con texto (no OCR) no se filtra.
    assert parser.parse_product("u", _read("nutrimar_intensivo.html"), "Nutrimar", texto)[0]["proteina_pct"] == 3.5


def test_etapas_fichas_reales_y_expansion_sku():
    import schema
    cases = [("nutrimar_ficha_pl_raceway_40_9.txt", {"post_larva", "precria", "post_transferencia", "engorde"}, 1),
             ("nutrimar_ficha_semi_intensivo.txt", {"engorde"}, 2),
             ("nutrimar_ficha_extensivo_ocr.txt", set(), 1)]
    for fixture, expected, count in cases:
        records = parser.parse_product("u", _read("nutrimar_intensivo.html"), ficha_texto=_read(fixture),
                                       ficha_ocr="ocr" in fixture)
        assert len(records) == count
        for r in records:
            assert r.get("_etapas_detectadas") is True
            assert {c for c in schema.ETAPA_COLUMNS if r[c] is True} == {"etapa_" + e for e in expected}
            assert all(r[c] is (False if expected else None) for c in schema.ETAPA_COLUMNS
                       if c.removeprefix("etapa_") not in expected)


def test_etapas_sin_ficha_desde_nombre_y_pagina_sin_inferir():
    import schema
    larva = parser.parse_product("u", _read("nutrimar_ez_larva.html"))[0]
    assert larva.get("_etapas_detectadas") is True
    assert {c for c in schema.ETAPA_COLUMNS if larva[c] is True} == {"etapa_larva"}
    r = parser.parse_product("https://example.test/engorde", _read("nutrimar_intensivo.html"))[0]
    assert r.get("_etapas_detectadas") is True
    assert all(r[c] is None for c in schema.ETAPA_COLUMNS)


def test_ficha_tiene_prioridad_y_retorno_ocr_conserva_marcador():
    from bs4 import BeautifulSoup
    import schema
    soup = BeautifulSoup(_read("nutrimar_intensivo.html"), "html.parser")
    soup.find("main").append(BeautifulSoup("<p>larvas reproductores</p>", "html.parser"))
    r = parser.parse_product("u", str(soup), ficha_texto=_read("nutrimar_ficha_extensivo_ocr.txt"), ficha_ocr=True)[0]
    assert r.get("_etapas_detectadas") is True
    assert all(r[c] is None for c in schema.ETAPA_COLUMNS)
    # Perturbación del OCR real para recorrer el retorno por valor dudoso.
    texto = _read("nutrimar_ficha_extensivo_ocr.txt").replace("35,0%", "3,5%")
    r = parser.parse_product("u", str(soup), ficha_texto=texto, ficha_ocr=True)[0]
    assert r.get("_etapas_detectadas") is True
    assert all(r[c] is None for c in schema.ETAPA_COLUMNS)
    assert r["_conflictos"][0]["regla"] == "ocr_fuera_de_rango"


def test_etapas_web_excluyen_menu_footer_y_scripts():
    from bs4 import BeautifulSoup
    import schema
    soup = BeautifulSoup(_read("nutrimar_intensivo.html"), "html.parser")
    for selector in ["header", "footer", "script"]:
        tag = soup.find(selector)
        assert tag is not None
        tag.string = "larvas precría engorde reproductores"
    r = parser.parse_product("u", str(soup))[0]
    assert r.get("_etapas_detectadas") is True
    assert all(r[c] is None for c in schema.ETAPA_COLUMNS)
