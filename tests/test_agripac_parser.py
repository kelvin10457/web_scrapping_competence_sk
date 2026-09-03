from conftest import FIXTURES
from parsers import agripac as parser


def _html(filename: str) -> str:
    return (FIXTURES / filename).read_text(encoding="utf-8")


def test_feedpac_35_premium_has_no_subtipo_tab_so_tamano_stays_none():
    # Caso real: Feedpac 35% Premium (linea base) no publica pestana
    # "Subtipo" ni menciona mm en ningun lado -- no se inventa un tamano.
    html = _html("agripac_feedpac_35_premium.html")
    record = parser.parse_product("https://agripac.com.ec/productos/feedpac-35-premium/", html)
    assert record["nombre_producto"] == "Feedpac 35% Premium"
    assert record["empresa"] == "Agripac"
    assert record["proteina_pct"] == "35"
    assert record["tamano_pellet_mm"] is None
    assert record["tipo_presentacion"] == "Pelletizado"
    assert record["empaque_kg"] == "25"


def test_tamano_pellet_mm_reads_from_subtipo_tab():
    html = _html("agripac_feedpac_35_ultra_micropellet_1_2mm.html")
    record = parser.parse_product(
        "https://agripac.com.ec/productos/feedpac-35-ultra-micropellet-1-2mm/", html
    )
    assert record["tamano_pellet_mm"] == "1.2"
    assert record["proteina_pct"] == "35"
    assert record["tipo_presentacion"] == "Pelletizado"


def test_tamano_pellet_mm_falls_back_to_title_when_subtipo_tab_is_missing():
    # Caso real: "35% Premium Micropellet Agua Dulce 1.5mm" no tiene pestana
    # "Subtipo" (a diferencia de la mayoria de productos con tamano), pero
    # el mm si esta en el titulo -- no hay que dejarlo en None cuando el
    # dato esta a la vista en otro lado de la misma pagina.
    html = _html("agripac_35_premium_micropellet_agua_dulce_1_5mm.html")
    record = parser.parse_product(
        "https://agripac.com.ec/productos/35-premium-micropellet-agua-dulce-1-5mm/", html
    )
    assert record["tamano_pellet_mm"] == "1.5"


def test_tipo_presentacion_none_for_polvo_despite_description_saying_pelletizado():
    # Ficha internamente inconsistente (confirmado 2026-09-03): la pestana
    # dedicada "Tipo" dice "Polvo" pero la "Descripcion" de marketing dice
    # "pelletizado". Se confia en el campo dedicado, no en la descripcion --
    # y "Polvo" es una 3ra categoria fuera de Extruido/Pelletizado, asi que
    # tipo_presentacion queda en None (no se fuerza a Pelletizado).
    html = _html("agripac_35_premium_micropellet_agua_dulce_1_5mm.html")
    record = parser.parse_product(
        "https://agripac.com.ec/productos/35-premium-micropellet-agua-dulce-1-5mm/", html
    )
    assert record["tipo_presentacion"] is None


def test_proteina_pct_falls_back_to_ingredientes_nucleo_when_title_has_no_percent():
    # Caso real: "Premium Agua Dulce" no trae "%" en el titulo (a diferencia
    # del resto del catalogo) -- el 35% solo aparece en el texto de
    # Ingredientes ("nucleo 35% Premium agua dulce").
    html = _html("agripac_premium_agua_dulce.html")
    record = parser.parse_product("https://agripac.com.ec/productos/premium-agua-dulce/", html)
    assert record["nombre_producto"] == "Premium Agua Dulce"
    assert record["proteina_pct"] == "35"


def test_tamano_pellet_mm_handles_comma_decimal_separator():
    # El sitio usa "," como separador decimal en algunos productos (ej.
    # "Subtipo 1,8 Mm") en vez de "." -- debe normalizarse igual.
    html = _html("agripac_feedpac_35_ultra_gregarinas_18mm.html")
    record = parser.parse_product(
        "https://agripac.com.ec/productos/feedpac-35-ultra-gregarinas-18-mm/", html
    )
    assert record["tamano_pellet_mm"] == "1.8"


def test_etapa_falls_back_to_tamano_when_text_is_generic_for_all_products():
    # "Modo de uso" es el mismo texto generico ("camarones adultos y
    # juveniles") en casi todo el catalogo -- no resuelve etapa por si solo,
    # asi que se cae al tamano de pellet real (>= 1.8mm Pelletizado -> engorde).
    html = _html("agripac_feedpac_35_ultra_gregarinas_18mm.html")
    record = parser.parse_product(
        "https://agripac.com.ec/productos/feedpac-35-ultra-gregarinas-18-mm/", html
    )
    assert record["etapa"] == "engorde"


def test_parse_listing_tags_all_records_as_agripac():
    html = _html("agripac_feedpac_35_premium.html")
    records = parser.parse_listing(
        [{"url": "https://agripac.com.ec/productos/feedpac-35-premium/", "html": html}]
    )
    assert len(records) == 1
    assert records[0]["empresa"] == "Agripac"
