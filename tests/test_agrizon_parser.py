import json

from conftest import FIXTURES
from parsers import agrizon as parser


def _load_products() -> list[dict]:
    return json.loads((FIXTURES / "agrizon_biomar_products.json").read_text(encoding="utf-8"))


def _find(products: list[dict], handle: str) -> dict:
    return next(p for p in products if p["handle"] == handle)


def test_line_name_uses_agrizon_capitalization_as_is():
    # Ya no se fuerza a la capitalizacion de marca de biomar.com (ej. "EXIA
    # Prime" en vez de "Exia Prime") -- decision del usuario 2026-09-03: al
    # quedarse solo con Agrizon como fuente, no hay un segundo nombre con el
    # que "hacer juego", asi que mapear ese caso especial ya no aporta nada
    # funcional (nombre_producto no se usa para comparar/unir en ningun
    # lado) y se elimino por ser complejidad de mas.
    products = _load_products()
    record = parser.parse_product(_find(products, "exia-prime-35-2-0mm-25-kg-alimento-pelletizado"))
    assert record["nombre_producto"] == "Exia Prime"


def test_line_name_keeps_generic_name_when_sub_linea_is_unknown():
    # Agrizon no dice a que INICIO (Focus/Maxio/Prime/Pro) corresponde
    # "Exia Start" -- forzar una equivalencia seria inventar dato.
    products = _load_products()
    record = parser.parse_product(_find(products, "exia-start-38-0-9-1-2-mm-10-kg-dieta-para-larvas"))
    assert record["nombre_producto"] == "Exia Start"


def test_proteina_pct_reads_from_title_not_body_html():
    # Exia Prime 35% Precria: el titulo dice 35%, confirmado con el usuario
    # como el dato correcto (2026-09-03).
    products = _load_products()
    record = parser.parse_product(_find(products, "exia-prime-35-precria-0-6-0-9-mm-25-kg"))
    assert record["proteina_pct"] == "35"


def test_tamano_mm_preserves_range_as_text():
    products = _load_products()
    record = parser.parse_product(_find(products, "exia-prime-35-precria-0-6-0-9-mm-25-kg"))
    assert record["tamano_pellet_mm"] == "0.6-0.9"


def test_tamano_microns_converts_to_mm():
    # Larviva se publica en micras, no mm -- la columna del schema es mm.
    products = _load_products()
    record = parser.parse_product(_find(products, "larviva-55-250-375-micras-1-kg"))
    assert record["tamano_pellet_mm"] == "0.25-0.375"


def test_empaque_kg_from_variant_grams():
    products = _load_products()
    record = parser.parse_product(_find(products, "exia-start-38-0-9-1-2-mm-10-kg-dieta-para-larvas"))
    assert record["empaque_kg"] == "10"


def test_tipo_presentacion_reads_english_title_when_tag_is_missing():
    # EXIA Perform/Pro: el tag en espanol "Pelletizado" no esta presente,
    # pero el titulo dice "Pelletized" (ingles) -- debe detectarse igual.
    products = _load_products()
    record = parser.parse_product(_find(products, "exia-perform-35-2-0-mm-25-kg"))
    assert record["tipo_presentacion"] == "Pelletizado"


def test_tipo_presentacion_recognizes_extrusado_tag():
    # "Extrusado" (Larviva) es una variante que el regex original de
    # schema.detect_tecnologia no reconocia (solo "extrui.../pelletiza...").
    products = _load_products()
    record = parser.parse_product(_find(products, "larviva-55-250-375-micras-1-kg"))
    assert record["tipo_presentacion"] == "Extruido"


def test_tipo_presentacion_none_for_microgranulado_only():
    # Microgranulado es una 3ra categoria fuera de la dicotomia Extruido/
    # Pelletizado del schema -- no se fuerza a ninguna de las dos.
    products = _load_products()
    record = parser.parse_product(_find(products, "exia-prime-35-precria-0-6-0-9-mm-25-kg"))
    assert record["tipo_presentacion"] is None


def test_etapa_falls_back_to_tamano_when_tags_are_ambiguous():
    # Exia Prime 1.2mm trae "engorde" Y "Iniciadores" (precria) en el mismo
    # set de tags -- ambiguo, se resuelve por tamano de pellet (< 1.6 -> precria).
    products = _load_products()
    record = parser.parse_product(_find(products, "exia-prime-35-1-2-mm-25-kg"))
    assert record["etapa"] == "precria"


def test_etapa_larva_from_unambiguous_tags_not_derivable_from_tamano():
    # etapa_from_tamano nunca devuelve "larva" (solo precria/engorde/None);
    # Larviva SOLO se puede resolver via tags ("larvas"/"Post-larva").
    products = _load_products()
    record = parser.parse_product(_find(products, "larviva-55-250-375-micras-1-kg"))
    assert record["etapa"] == "larva"
    assert record["etapa_camaron"] is None  # se calcula despues, en pipeline.write_csv


def test_etapa_1_6mm_boundary_stays_none():
    # Limite documentado en schema.etapa_from_tamano: 1.6mm es ambiguo por
    # diseno (techo de Nursery y tamano tipico de Pre Grower a la vez).
    products = _load_products()
    record = parser.parse_product(_find(products, "exia-prime-35-1-6-mm-25-kg"))
    assert record["etapa"] is None


def test_grasa_pct_always_none():
    # Agrizon tampoco publica grasa -- sigue siendo un hueco real, no un
    # bug del parser.
    products = _load_products()
    for product in products:
        record = parser.parse_product(product)
        assert record["grasa_pct"] is None


def test_parse_listing_tags_all_records_as_biomar():
    products = _load_products()
    records = parser.parse_listing(products)
    assert len(records) == len(products)
    assert all(r["empresa"] == "BioMar" for r in records)
