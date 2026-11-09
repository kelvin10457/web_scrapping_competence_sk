import schema
from conftest import FIXTURES
from paises.ecuador import agripac_parser as parser


def _html(filename: str) -> str:
    return (FIXTURES / filename).read_text(encoding="utf-8")


def test_feedpac_35_premium_has_no_subtipo_tab_so_tamano_stays_none():
    # Caso real: Feedpac 35% Premium (linea base) no publica pestana
    # "Subtipo" ni menciona mm en ningun lado -- no se inventa un tamano.
    html = _html("agripac_feedpac_35_premium.html")
    record = parser.parse_product("https://agripac.com.ec/productos/feedpac-35-premium/", html)
    assert record["nombre_producto"] == "Feedpac 35% Premium"
    assert record["empresa"] == "Agripac"
    assert record["proteina_pct"] == 35.0
    assert record["tamano_pellet_mm"] is None
    assert record["tipo_presentacion"] == "Pellet"
    assert record["empaque_kg"] == "25"


def test_tamano_pellet_mm_reads_from_subtipo_tab():
    html = _html("agripac_feedpac_35_ultra_micropellet_1_2mm.html")
    record = parser.parse_product(
        "https://agripac.com.ec/productos/feedpac-35-ultra-micropellet-1-2mm/", html
    )
    assert record["tamano_pellet_mm"] == "1.2"
    assert record["proteina_pct"] == 35.0
    assert record["tipo_presentacion"] == "Pellet"


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


def test_tipo_presentacion_polvo_despite_description_saying_pelletizado():
    # Ficha internamente inconsistente (confirmado 2026-09-03): la pestana
    # dedicada "Tipo" dice "Polvo" pero la "Descripcion" de marketing dice
    # "pelletizado". Se confia en el campo dedicado, no en la descripcion.
    # Hasta 2026-09-06 "Polvo" quedaba en None (3ra categoria fuera de
    # Extruido/Pelletizado); desde 2026-09-07 es un valor propio de
    # tipo_presentacion (ver schema.detect_tecnologia), a pedido del
    # usuario tras encontrar Artemia Cysts/Mpex/Royal Pepper Protein en la
    # division Larvicultura.
    html = _html("agripac_35_premium_micropellet_agua_dulce_1_5mm.html")
    record = parser.parse_product(
        "https://agripac.com.ec/productos/35-premium-micropellet-agua-dulce-1-5mm/", html
    )
    assert record["tipo_presentacion"] == "Polvo"


def test_es_larvicultura_flag_forces_etapa_skt_hatchery_in_pipeline():
    # El parser solo marca el registro (record["_es_larvicultura"]); quien
    # decide Hatchery es schema.etapa_skt_from_row, llamado
    # centralizado desde pipeline.write_csv() -- ver test_pipeline.py para
    # el caso end-to-end. Aca solo se verifica que parse_product/parse_listing
    # propagan el flag que les llega del scraper.
    html = _html("agripac_35_premium_micropellet_agua_dulce_1_5mm.html")
    record = parser.parse_product(
        "https://agripac.com.ec/productos/35-premium-micropellet-agua-dulce-1-5mm/",
        html,
        es_larvicultura=True,
    )
    assert record["_es_larvicultura"] is True

    records = parser.parse_listing(
        [{"url": "https://agripac.com.ec/productos/x/", "html": html, "es_larvicultura": True}]
    )
    assert records[0]["_es_larvicultura"] is True


def test_proteina_pct_falls_back_to_ingredientes_nucleo_when_title_has_no_percent():
    # Caso real: "Premium Agua Dulce" no trae "%" en el titulo (a diferencia
    # del resto del catalogo) -- el 35% solo aparece en el texto de
    # Ingredientes ("nucleo 35% Premium agua dulce").
    html = _html("agripac_premium_agua_dulce.html")
    record = parser.parse_product("https://agripac.com.ec/productos/premium-agua-dulce/", html)
    assert record["nombre_producto"] == "Premium Agua Dulce"
    assert record["proteina_pct"] == 35.0


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
    assert record["etapa_engorde"] is True


def test_parse_listing_tags_all_records_as_agripac():
    html = _html("agripac_feedpac_35_premium.html")
    records = parser.parse_listing(
        [{"url": "https://agripac.com.ec/productos/feedpac-35-premium/", "html": html}]
    )
    assert len(records) == 1
    assert records[0]["empresa"] == "Agripac"


def test_tipo_presentacion_microextruido_desde_la_pestana_tipo():
    # R3.3 REQ-3: MeM dice "Microextruido" (valor oficial); antes se colapsaba a Extruido.
    html = _html("agripac_mem_300_500.html")
    record = parser.parse_product("https://agripac.com.ec/productos/mem-300-500/", html, es_larvicultura=True)
    assert record["tipo_presentacion"] == "Microextruido"


def _etapas_true(record: dict) -> set[str]:
    return {e for e in schema.ETAPAS if record[f"etapa_{e}"] is True}


def _parse(slug: str, filename: str, es_larvicultura: bool = False) -> dict:
    return parser.parse_product(
        f"https://agripac.com.ec/productos/{slug}/", _html(filename), es_larvicultura
    )


def test_r46_req1_descripcion_marca_todas_las_etapas():
    # "larvas y post-larvas de camaron"
    larfeed = _parse("larfeed", "agripac_larfeed.html", True)
    assert _etapas_true(larfeed) == {"larva", "post_larva"}
    # "ideal para zoea 3 - mysis 3" + "larvas y post larvas"
    vitellus = _parse("vitellus-small", "agripac_vitellus_small.html", True)
    assert _etapas_true(vitellus) == {"larva", "post_larva"}
    # "postlarvas", "PL1 a PL6"
    mpex = _parse("mpex-100-200", "agripac_mpex_100_200.html", True)
    assert _etapas_true(mpex) == {"post_larva"}
    assert mpex["etapa_larva"] is False
    oyster = _parse("new-royal-oyster", "agripac_new_royal_oyster.html", True)
    assert _etapas_true(oyster) == {"reproductores"}
    assert all(r["_etapas_detectadas"] for r in (larfeed, vitellus, mpex, oyster))


def test_r46_req2_sin_termino_de_etapa_usa_el_tamano_de_pellet():
    micro = _parse("feedpac-35-ultra-micropellet-1-2mm", "agripac_feedpac_35_ultra_micropellet_1_2mm.html")
    assert _etapas_true(micro) == {"precria"}
    gregarinas = _parse("feedpac-35-ultra-gregarinas-18-mm", "agripac_feedpac_35_ultra_gregarinas_18mm.html")
    assert _etapas_true(gregarinas) == {"engorde"}
    # sin tamano en la ficha: vacio
    premium = _parse("feedpac-35-premium", "agripac_feedpac_35_premium.html")
    assert all(premium[f"etapa_{e}"] is None for e in schema.ETAPAS)
    assert premium["_etapas_detectadas"] is True


def test_r46_req3_royal_pepper_protein_queda_vacio():
    record = _parse("royal-pepper-protein", "agripac_royal_pepper_protein.html", True)
    assert all(record[f"etapa_{e}"] is None for e in schema.ETAPAS)
    assert record["_etapas_detectadas"] is True
