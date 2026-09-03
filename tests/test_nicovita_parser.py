import pytest

from conftest import FIXTURES, ROOT
from parsers import nicovita as parser


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
    assert fields["grasa_pct"] == 5.0


def test_parse_pdf_text_detects_single_l_peletizada_spelling():
    # Ver captura del usuario: la ficha de Térap dice "Dieta balanceada
    # peletizada" (una sola L), no "pelletizada".
    text = "2. Descripcion del Producto\nDieta balanceada peletizada para camaron"
    fields = parser.parse_pdf_text(text)
    assert fields["tipo_presentacion"] == "Pelletizado"


def test_infer_etapa_from_description_full_range_stays_none():
    # Caso real Classic/Katal base (MEMORY.md): la ficha menciona el
    # marcador temprano ("post larva") Y el tardio ("tamaño de mercado") a
    # la vez -- el producto cubre todo el ciclo, no se fuerza una etapa.
    text = "desde post larva hasta tamaño de mercado"
    assert parser._infer_etapa_from_description(text) is None


def test_infer_etapa_from_description_only_early_marker_is_larva():
    assert parser._infer_etapa_from_description("alimento desde post larva") == "larva"


def test_infer_etapa_from_description_only_late_marker_is_engorde():
    assert parser._infer_etapa_from_description("hasta tamaño de mercado") == "engorde"


def test_infer_etapa_from_description_disease_marker_no_longer_returns_salud():
    # "salud" ya no es un valor de etapa (ver producto_salud abajo) -- sin
    # otro marcador de rango, el texto de enfermedad solo no resuelve etapa.
    assert parser._infer_etapa_from_description("tratamiento contra Vibrio spp") is None


def test_infer_etapa_from_description_keeps_stage_info_alongside_disease_marker():
    # Caso real que motivo el fix (usuario 2026-09-02): antes, el marcador
    # de enfermedad devolvia "salud" y cortaba el resto sin mirar si el
    # texto tambien describia una etapa real -- ahora si se resuelve.
    text = "tratamiento contra Vibrio spp hasta tamaño de mercado"
    assert parser._infer_etapa_from_description(text) == "engorde"


# La deteccion de producto_salud es compartida (schema.detect_producto_salud,
# probada en test_schema.py) -- ya no vive como funcion local de este parser.


class _FakePage:
    """Stub minimo de pagina pdfplumber -- solo expone extract_tables(),
    unico metodo que usa _extract_presentacion_pairs. Las tablas literales
    son las que devuelve pdfplumber de verdad contra las fichas reales
    (confirmado 2026-09-02, ver MEMORY.md bug tamano/proteina)."""

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
    # Caso real: Katal Precria no tiene ficha PDF enlazada (MEMORY.md).
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
    assert pairs == {("28", "2.5"), ("35", "2.0"), ("35", "2.5")}
    # Los campos que no varian por SKU deben ser identicos en las 3 filas.
    assert {r["nombre_producto"] for r in records} == {"Nicovita Classic AD"}
    assert {r["empresa"] for r in records} == {"Nicovita"}


def test_parse_product_classic_fills_etapa_per_sku_leaving_1_6mm_ambiguous():
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
    by_tamano = {r["tamano_pellet_mm"]: r["etapa"] for r in records}
    assert by_tamano["0.5-1.0"] == "precria"
    assert by_tamano["1.2"] == "precria"
    assert by_tamano["1.6"] is None
    assert by_tamano["2.0"] == "engorde"
    assert by_tamano["2.5"] == "engorde"


def test_parse_product_terap_keeps_stage_info_and_flags_salud():
    # Caso real que motivo el fix (usuario 2026-09-02): Terap es "salud"
    # (trata Vibrio) pero su ficha tambien dice "desde post larva hasta
    # tamano de mercado" -- antes se perdia esa info porque el marcador de
    # enfermedad devolvia "salud" y cortaba el resto. Ahora coexisten:
    # producto_salud=True en las 5 filas, y etapa resuelta por tamano
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
    assert all(r["producto_salud"] is True for r in records)
    by_tamano = {r["tamano_pellet_mm"]: r["etapa"] for r in records}
    assert by_tamano["0.8"] == "precria"
    assert by_tamano["1.2"] == "precria"
    assert by_tamano["2.0"] == "engorde"
    assert by_tamano["2.5"] == "engorde"
