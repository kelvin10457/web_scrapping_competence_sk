import pytest

from conftest import FIXTURES, ROOT
import schema
from paises._compartido import nicovita_parser as parser


def _skt(record):
    """etapa_skt la calcula pipeline.write_csv; el test aplica la misma regla."""
    etapas = {c.removeprefix("etapa_") for c in schema.ETAPA_COLUMNS if record[c] is True}
    return schema.etapa_skt_from_row(etapas, record["tamano_pellet_mm"])


def test_slug_from_url_and_name_mapping():
    url = "https://nicovita.com/productos/nicovita-katal-ad-ecuador/"
    slug = parser.slug_from_url(url)
    assert slug == "katal-ad"
    assert parser.product_name_from_slug(slug) == "Nicovita Katal AD"


def test_product_name_from_slug_fallback_for_unmapped_slug():
    assert parser.product_name_from_slug("nuevo-producto") == "Nicovita Nuevo Producto"


def test_extract_empaque_kg_from_real_html_fixture():
    html = (FIXTURES / "nicovita_katal_ad.html").read_text(encoding="utf-8")
    assert parser._extract_empaque_kg(html) == "25"


def test_parse_pdf_text_no_tecnologia_mention_stays_none():
    text = "Composicion garantizada\nProteinas (%) 35\nGrasa (%) 5"
    fields = parser.parse_pdf_text(text)
    assert fields["tipo_presentacion"] is None


def test_parse_pdf_text_detects_single_l_peletizada_spelling():
    # Ver captura del usuario: la ficha de Térap dice "Dieta balanceada
    # peletizada" (una sola L), no "pelletizada".
    text = "2. Descripcion del Producto\nDieta balanceada peletizada para camaron"
    fields = parser.parse_pdf_text(text)
    assert fields["tipo_presentacion"] == "Pellet"


def test_infer_etapa_from_description_full_range_stays_none():
    # Caso real Classic/Katal base (docs/historico/MEMORY.md): la ficha menciona el
    # marcador temprano ("post larva") Y el tardio ("tamaño de mercado") a
    # la vez -- el producto cubre todo el ciclo, no se fuerza una etapa.
    text = "desde post larva hasta tamaño de mercado"
    assert parser._infer_etapa_from_description(text) is None


def test_infer_etapa_from_description_only_early_marker_is_larva():
    assert parser._infer_etapa_from_description("alimento desde post larva") == "larva"


def test_infer_etapa_from_description_only_late_marker_is_engorde():
    assert parser._infer_etapa_from_description("hasta tamaño de mercado") == "engorde"


def test_infer_etapa_from_description_disease_marker_no_longer_returns_salud():
    # "salud" ya no es un valor de etapa (ver es_producto_de_salud abajo) -- sin
    # otro marcador de rango, el texto de enfermedad solo no resuelve etapa.
    assert parser._infer_etapa_from_description("tratamiento contra Vibrio spp") is None


def test_infer_etapa_from_description_keeps_stage_info_alongside_disease_marker():
    # Caso real que motivo el fix (usuario 2026-09-02): antes, el marcador
    # de enfermedad devolvia "salud" y cortaba el resto sin mirar si el
    # texto tambien describia una etapa real -- ahora si se resuelve.
    text = "tratamiento contra Vibrio spp hasta tamaño de mercado"
    assert parser._infer_etapa_from_description(text) == "engorde"


# La deteccion de es_producto_de_salud es compartida (schema.detect_es_producto_de_salud,
# probada en test_schema.py) -- ya no vive como funcion local de este parser.


class _FakePage:
    """Stub minimo de pagina pdfplumber -- solo expone extract_tables(),
    unico metodo que usa _extract_presentacion_pairs. Las tablas literales
    son las que devuelve pdfplumber de verdad contra las fichas reales
    (confirmado 2026-09-02, ver docs/historico/MEMORY.md bug tamano/proteina)."""

    def __init__(self, tables):
        self._tables = tables

    def extract_tables(self):
        return self._tables


class _FakePdf:
    def __init__(self, pages):
        self.pages = pages


# Tabla real de Classic AD: 28% agrupa solo 2.5mm, 35% agrupa 2.0 y 2.5mm --
# el mismo 2.5mm aparece bajo los dos %, por eso no es una lista 1 a 1.
_CLASSIC_AD_TABLE = [
    ["FORMATO", None, None, "", "Pellets", ""],
    [None, None, None, None, "(mm)", None],
    ["", "28%", "", "", "2.5", ""],
    ["35%", None, None, "2.0", None, None],
    [None, None, None, "2.5", None, None],
]

# Tabla real de Qualis: el texto de la seccion 3.a de esa misma ficha dice
# "25%", pero la tabla real (unica fuente que usa el parser) dice 22%.
_QUALIS_TABLE = [
    ["FORMATO", "", "DIAMETRO", ""],
    [None, None, "(mm)", None],
    ["35%", "2.0", None, None],
    [None, "2.5", None, None],
    ["28%", "2.0", None, None],
    [None, "2.5", None, None],
    ["22%", "2.0", None, None],
    [None, "2.5", None, None],
]

# Tabla real de Terap: los 4 tamanos de la fila 35% vienen en UNA sola celda
# combinada con saltos de linea, no en 4 filas separadas.
_TERAP_TABLE = [
    ["FORMATO", "", "DIAMETRO", ""],
    [None, None, "(mm)", None],
    ["40%", "0.8", None, None],
    ["35%", "0.8\n1.2\n2.0\n2.5", None, None],
]


def test_extract_presentacion_pairs_same_size_under_two_protein_tiers():
    pdf = _FakePdf([_FakePage([_CLASSIC_AD_TABLE])])
    assert parser._extract_presentacion_pairs(pdf) == [
        ("28", "2.5"),
        ("35", "2.0"),
        ("35", "2.5"),
    ]


def test_extract_presentacion_pairs_uses_table_value_not_summary_text():
    pdf = _FakePdf([_FakePage([_QUALIS_TABLE])])
    pairs = parser._extract_presentacion_pairs(pdf)
    assert ("22", "2.0") in pairs and ("22", "2.5") in pairs
    assert not any(p[0] == "25" for p in pairs)


def test_extract_presentacion_pairs_splits_merged_multiline_cell():
    pdf = _FakePdf([_FakePage([_TERAP_TABLE])])
    assert parser._extract_presentacion_pairs(pdf) == [
        ("40", "0.8"),
        ("35", "0.8"),
        ("35", "1.2"),
        ("35", "2.0"),
        ("35", "2.5"),
    ]


def test_extract_presentacion_pairs_searches_every_page():
    # Caso real Katal Post Transferencia: la tabla de composicion trae filas
    # extra (Calcio/Sal/Fosforo) que empujan "Presentacion Comercial" a la
    # pagina 2 -- si solo se mira pages[0] no se encuentra nada.
    composicion_table = [["FISICOQUIMICAS", None], ["Proteina (%)", "Minimo 38%"]]
    presentacion_table = [["FORMATO", "DIAMETRO (mm)"], ["38%", "1.2"]]
    pdf = _FakePdf(
        [_FakePage([composicion_table]), _FakePage([presentacion_table])]
    )
    assert parser._extract_presentacion_pairs(pdf) == [("38", "1.2")]


def test_extract_presentacion_pairs_no_matching_table_returns_empty():
    pdf = _FakePdf([_FakePage([[["FISICOQUIMICAS", None], ["Grasa (%)", "5%"]]])])
    assert parser._extract_presentacion_pairs(pdf) == []


def test_parse_product_returns_single_null_row_when_no_pdf():
    # Caso real: Katal Precria no tiene ficha PDF enlazada (docs/historico/MEMORY.md).
    records = parser.parse_product(
        "https://nicovita.com/productos/nicovita-katal-precria-ecuador/",
        html="",
        pdf_bytes=None,
    )
    assert len(records) == 1
    assert records[0]["tamano_pellet_mm"] is None
    assert records[0]["proteina_pct"] is None
    assert records[0]["nombre_producto"] == "Nicovita Katal Precría"


def test_parse_product_explodes_one_row_per_real_sku():
    pdf_path = ROOT / "data" / "raw" / "nicovita" / "FT-NICOVITA-CLASSIC-CAMARON-AD.pdf"
    if not pdf_path.exists():
        pytest.skip("PDF real no presente en este entorno (data/raw no poblado)")
    records = parser.parse_product(
        "https://nicovita.com/productos/nicovita-classic-ad-ecuador/",
        html="",
        pdf_bytes=pdf_path.read_bytes(),
    )
    pairs = {(r["proteina_pct"], r["tamano_pellet_mm"]) for r in records}
    assert pairs == {(28.0, "2.5"), (35.0, "2.0"), (35.0, "2.5")}
    # Los campos que no varian por SKU deben ser identicos en las 3 filas.
    assert {r["nombre_producto"] for r in records} == {"Nicovita Classic AD"}
    assert {r["empresa"] for r in records} == {"Nicovita"}


def test_parse_product_classic_etapa_skt_por_sku_con_1_6mm_pre_grower():
    # Caso real que motivo el fallback: la ficha de Classic dice "desde
    # post larva hasta tamano de mercado" (cubre el ciclo completo), asi
    # que ni el slug ni la descripcion resuelven etapa -- pero ahora que
    # cada fila trae un tamano puntual, se puede aplicar la banda de
    # negocio por fila. 1.6mm debe quedar sin resolver a proposito (ver
    # test_etapa_from_tamano_exactly_1_6mm_stays_none en test_schema.py).
    pdf_path = ROOT / "data" / "raw" / "nicovita" / "FT-NICOVITA-CLASSIC-CAMARON.pdf"
    if not pdf_path.exists():
        pytest.skip("PDF real no presente en este entorno (data/raw no poblado)")
    records = parser.parse_product(
        "https://nicovita.com/productos/nicovita-classic-ecuador/",
        html="",
        pdf_bytes=pdf_path.read_bytes(),
    )
    by_tamano = {r["tamano_pellet_mm"]: _skt(r) for r in records}
    assert by_tamano["0.5-1.0"] == "Nursery"
    assert by_tamano["1.2"] == "Nursery"
    assert by_tamano["1.6"] == "Pre Grower"
    assert by_tamano["2.0"] == "Grower"
    assert by_tamano["2.5"] == "Grower"


def test_parse_product_terap_keeps_stage_info_and_flags_salud():
    # Caso real que motivo el fix (usuario 2026-09-02): Terap es "salud"
    # (trata Vibrio) pero su ficha tambien dice "desde post larva hasta
    # tamano de mercado" -- antes se perdia esa info porque el marcador de
    # enfermedad devolvia "salud" y cortaba el resto. Ahora coexisten:
    # es_producto_de_salud=True en las 5 filas, y etapa resuelta por tamano
    # (mismo fallback que Classic/Katal base, ya que la descripcion
    # completa sigue siendo ambigua de rango completo).
    pdf_path = ROOT / "data" / "raw" / "nicovita" / "FT-NICOVITA-TERAP-CAMARON.pdf"
    if not pdf_path.exists():
        pytest.skip("PDF real no presente en este entorno (data/raw no poblado)")
    records = parser.parse_product(
        "https://nicovita.com/productos/nicovita-terap-ecuador/",
        html="",
        pdf_bytes=pdf_path.read_bytes(),
    )
    assert all(r["es_producto_de_salud"] is True for r in records)
    by_tamano = {r["tamano_pellet_mm"]: _skt(r) for r in records}
    assert by_tamano["0.8"] == "Nursery"
    assert by_tamano["1.2"] == "Nursery"
    assert by_tamano["2.0"] == "Grower"
    assert by_tamano["2.5"] == "Grower"


def test_slug_from_url_handles_other_countries():
    from paises._compartido import nicovita_parser as pr

    assert pr.slug_from_url("https://nicovita.com/productos/nicovita-katal-honduras/") == "katal"
    assert pr.slug_from_url("https://nicovita.com/productos/nicovita-classic-mexico-2/") == "classic"
    assert pr.slug_from_url("https://nicovita.com/productos/nicovita-classic-engorde-honduras/") == "classic-engorde"
    assert pr.slug_from_url("https://nicovita.com/productos/nicovita-katal-ecuador/") == "katal"


def test_manual_pages_recognized_by_canonical_url(tmp_path, monkeypatch):
    from paises._compartido import nicovita_scraper as sc

    folder = tmp_path / "honduras"
    folder.mkdir()
    (folder / "cualquier nombre (1).html").write_text(
        '<html><link rel="canonical" href="https://nicovita.com/productos/nicovita-katal-honduras/" /></html>',
        encoding="utf-8",
    )
    (folder / "listado.html").write_text(
        '<link rel="canonical" href="https://nicovita.com/categoria/camarones/" />', encoding="utf-8"
    )
    monkeypatch.setattr(sc, "MANUAL_DIR", tmp_path)
    pages = sc.manual_pages("honduras")
    assert list(pages) == ["https://nicovita.com/productos/nicovita-katal-honduras/"]
    assert sc.manual_pages("mexico") == {}


# --- R4.2: etapas desde el slug + la descripcion del PDF ---------------------

def _parse_raw(url, pdf_name, html_name=None):
    pdf_path = ROOT / "data" / "raw" / "nicovita" / pdf_name if pdf_name else None
    html_path = ROOT / "data" / "raw" / "nicovita_html" / html_name if html_name else None
    for path in (pdf_path, html_path):
        if path is not None and not path.exists():
            pytest.skip("dato real no presente en este entorno (data/raw no poblado)")
    html = html_path.read_text(encoding="utf-8", errors="ignore") if html_path else ""
    return parser.parse_product(url, html=html, pdf_bytes=pdf_path.read_bytes() if pdf_path else None)


def _etapas(record):
    return {c.removeprefix("etapa_") for c in schema.ETAPA_COLUMNS if record[c] is True}


def test_r42_req1_terap_marca_todo_el_rango_en_todas_las_filas():
    # PDF: "desde post larva hasta tamaño de mercado"
    records = _parse_raw("https://nicovita.com/productos/nicovita-terap-ecuador/",
                         "FT-NICOVITA-TERAP-CAMARON.pdf")
    assert len(records) > 1
    for r in records:
        assert r["_etapas_detectadas"] is True
        assert _etapas(r) == {"post_larva", "precria", "post_transferencia", "engorde"}
        assert r["etapa_larva"] is False and r["etapa_reproductores"] is False


def test_r42_req1_slug_y_pdf_se_suman():
    # Slug "classic-precria" + PDF "PL10 a 1 gramo, en sistemas de transferencia"
    records = _parse_raw("https://nicovita.com/productos/nicovita-classic-precria-ecuador/",
                         "FT-NICOVITA-CLASSIC-PRECRÍA-CAMARÓN-español.pdf")
    assert {frozenset(_etapas(r)) for r in records} == {frozenset({"post_larva", "precria"})}
    # Slug "classic-post-transferencia" + PDF "desde 1 hasta 3 gramos" (sin etapa)
    records = _parse_raw("https://nicovita.com/productos/nicovita-classic-post-transferencia-ecuador/",
                         "FT-NICOVITA-CLASSIC-CAMARÓN-POST-TRANSFERENCIA.pdf")
    assert {frozenset(_etapas(r)) for r in records} == {frozenset({"post_transferencia"})}


def test_r42_req1_web_solo_sin_pdf_y_sin_etiqueta_de_categoria():
    # Katal Precria no tiene PDF: se usa la web, sin su etiqueta "Pre engorde"
    # (que marcaria engorde). Dice "para precrías desde PL20 hasta 1 g".
    records = _parse_raw("https://nicovita.com/productos/nicovita-katal-precria-ecuador/", None,
                         "https_nicovita_com_productos_nicovita_katal_precria_ecuador.html")
    assert _etapas(records[0]) == {"post_larva", "precria"}
    # Con PDF, la web no suma: Classic AD dice "Engorde" en la web, el PDF
    # "desde los 3 gramos hasta tamaño de mercado".
    records = _parse_raw("https://nicovita.com/productos/nicovita-classic-ad-ecuador/",
                         "FT-NICOVITA-CLASSIC-CAMARON-AD.pdf",
                         "https_nicovita_com_productos_nicovita_classic_ad_ecuador.html")
    assert {frozenset(_etapas(r)) for r in records} == {frozenset({"engorde"})}


def test_r42_req1_sin_texto_de_etapa_quedan_vacias():
    records = parser.parse_product("https://nicovita.com/productos/nicovita-classic-ad-ecuador/",
                                   html="", pdf_bytes=None)
    assert records[0]["_etapas_detectadas"] is True
    assert all(records[0][c] is None for c in schema.ETAPA_COLUMNS)


# --- R4.2b: Classic Organico Engorde (Honduras) enlaza la ficha equivocada ---

_ORGANIC_ENGORDE_HN = "https://nicovita.com/productos/nicovita-classic-organic-engorde-honduras/"


def test_r42b_req1_corrige_solo_el_enlace_equivocado():
    from paises._compartido import nicovita_scraper as sc

    html_path = ROOT / "data" / "raw" / "nicovita_html" / \
        "https_nicovita_com_productos_nicovita_classic_organic_engorde_honduras.html"
    if not html_path.exists():
        pytest.skip("dato real no presente en este entorno (data/raw no poblado)")
    html = html_path.read_text(encoding="utf-8", errors="ignore")
    assert sc.find_pdf_url(html).endswith("FT-NICOVITA-ORIGIN-ORGANIC.pdf")
    assert sc.find_pdf_url(html, _ORGANIC_ENGORDE_HN).endswith("FT-NICOVITA-CLASSIC-ORGANIC-CAMARON-HO.pdf")
    # Otra pagina con la misma ficha de Origin Organico no se toca.
    origin = "https://nicovita.com/productos/nicovita-origin-organic-honduras/"
    assert sc.find_pdf_url(html, origin).endswith("FT-NICOVITA-ORIGIN-ORGANIC.pdf")
    # Si el sitio corrige (u otra ficha), se usa lo que publique.
    otro = html.replace("2020/07/FT-NICOVITA-ORIGIN-ORGANIC.pdf", "2024/01/FT-NUEVA.pdf")
    assert sc.find_pdf_url(otro, _ORGANIC_ENGORDE_HN).endswith("FT-NUEVA.pdf")


def test_r42b_req2_queda_como_alias_de_classic_organic(monkeypatch):
    from paises._compartido import nicovita_scraper as sc

    carpeta = ROOT / "data" / "raw" / "nicovita_html"
    paginas = {
        _ORGANIC_ENGORDE_HN: carpeta / "https_nicovita_com_productos_nicovita_classic_organic_engorde_honduras.html",
        "https://nicovita.com/productos/nicovita-classic-organic-honduras/":
            carpeta / "https_nicovita_com_productos_nicovita_classic_organic_honduras.html",
    }
    if not all(p.exists() for p in paginas.values()):
        pytest.skip("dato real no presente en este entorno (data/raw no poblado)")
    html = {u: p.read_text(encoding="utf-8", errors="ignore") for u, p in paginas.items()}
    monkeypatch.setattr(sc, "discover_product_urls", lambda session, pais_slug: sorted(html))
    monkeypatch.setattr(sc, "fetch", lambda u, session=None: html[u])
    monkeypatch.setattr(sc, "download_pdf", lambda pdf_url, session=None: b"%PDF")
    monkeypatch.setattr(sc, "save_pdf", lambda pdf_url, content: None)
    resultados = sc.scrape_all("honduras")
    assert len(resultados) == 1
    assert resultados[0]["pdf_url"].endswith("FT-NICOVITA-CLASSIC-ORGANIC-CAMARON-HO.pdf")
