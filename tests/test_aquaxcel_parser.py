from bs4 import BeautifulSoup

from conftest import FIXTURES
from parsers import aquaxcel as parser


def _load_html() -> str:
    return (FIXTURES / "aquaxcel_listing.html").read_text(encoding="utf-8")


def test_parse_listing_finds_all_portfolio_lines():
    # El sitio trae 6 bloques "Portafolio {LINEA}" (Maxima, Rapid, Advance,
    # Active, Adapt Shock, Adapt Osmo) construidos con <div class="row"> de
    # Bootstrap -- no son <table>, por eso el parser viejo (que buscaba
    # solo el primer <table class="table">) los ignoraba por completo.
    records = parser.parse_listing(_load_html())
    lineas = {r["nombre_producto"].split()[1] for r in records}
    assert lineas >= {"MAXIMA", "RAPID", "ADVANCE", "ACTIVE", "ADAPT"}
    # 37 SKUs reales confirmados el 2026-09-01; tolera que el sitio agregue
    # productos nuevos sin que el test se rompa por un numero exacto.
    assert len(records) >= 30


def test_active_sku_has_full_identification_and_nutricional_data():
    records = parser.parse_listing(_load_html())
    active = next(r for r in records if r["nombre_producto"] == "AQUAXCEL ACTIVE 35% 2.0")
    assert active["empresa"] == "Cargill"
    assert active["etapa"] == "engorde"
    assert active["tamano_pellet_mm"] == "2"
    assert active["tipo_presentacion"] == "Extruido"
    assert active["empaque_kg"] == "25"
    assert active["proteina_pct"] == 35.0
    assert active["grasa_pct"] == 5.0


def test_portfolio_blocks_only_use_inicio_and_engorde():
    # Confirmado 2026-09-01: a diferencia de la vieja tabla comparativa
    # (que tenia un grupo "TRANSICION"), los bloques "Portafolio" solo usan
    # INICIO/ENGORDE -- normalize_etapa los mapea a precria/engorde.
    records = parser.parse_listing(_load_html())
    etapas = {r["etapa"] for r in records}
    assert etapas <= {"precria", "engorde", None}


def test_parse_listing_empty_html_returns_no_records():
    assert parser.parse_listing("<html><body>nada aqui</body></html>") == []


def test_adapt_shock_line_flagged_producto_salud_true():
    # Caso real que motivo el fix (usuario 2026-09-02): a diferencia de
    # Nicovita/HAID, Aquaxcel no tiene descripcion de producto por SKU --
    # el reclamo de salud vive en texto de marketing aparte de las tablas
    # "Portafolio", bajo el h2 "Adapt Shock": "Para combatir eventos
    # bacterianos extra celulares como la vibriosis". Confirmado real: 5
    # SKUs "ADAPT SH*" (linea Adapt Shock).
    records = parser.parse_listing(_load_html())
    adapt_shock = [r for r in records if "ADAPT SH" in r["nombre_producto"]]
    assert len(adapt_shock) == 5
    assert all(r["producto_salud"] is True for r in adapt_shock)


def test_other_lines_confirmed_false_not_none():
    # Las otras 5 lineas (Maxima/Rapid/Advance/Active/Adapt Osmo) SI tienen
    # texto de marketing propio, pero ninguna hace un reclamo especifico de
    # salud/tratamiento -- por eso deben quedar False (confirmado, no
    # None). Ver test_detect_producto_salud_false... en test_schema.py:
    # mencionar "salud" de forma generica (ej. Maxima) no cuenta.
    records = parser.parse_listing(_load_html())
    active = next(r for r in records if r["nombre_producto"] == "AQUAXCEL ACTIVE 35% 2.0")
    assert active["producto_salud"] is False
    adapt_osmo = [r for r in records if "ADAPT OSM" in r["nombre_producto"]]
    assert adapt_osmo and all(r["producto_salud"] is False for r in adapt_osmo)


def test_line_descriptions_finds_adapt_shock_vibriosis_text():
    soup = BeautifulSoup(_load_html(), "html.parser")
    descriptions = parser._line_descriptions(soup)
    assert "vibriosis" in descriptions["ADAPT SHOCK"].lower()
    assert "PORTAFOLIO" not in descriptions  # nunca captura los propios headings de tabla


def test_parse_listing_all_records_have_producto_salud_resolved():
    # Con el fix, ninguna de las 37 filas deberia quedar en None -- todas
    # las lineas tienen texto de marketing propio que se puede leer.
    records = parser.parse_listing(_load_html())
    assert all(r["producto_salud"] is not None for r in records)
