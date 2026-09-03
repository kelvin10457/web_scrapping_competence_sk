import pytest

import schema
from conftest import ROOT
from parsers import haid as parser

# Texto real (recortado) de la ficha "Speed Pellet" -- ver MEMORY.md: el
# encabezado dice PELLETIZADO (coincide con el nombre del producto) pero la
# descripcion dice, por error propio de la ficha, "elaborado por proceso de
# extruido".
SPEED_TEXT = """FICHA TÉCNICA DEL PRODUCTO

SPEED PELLET

ALIMENTO BALANCEADO PELLETIZADO PARA CAMARÓN

Nombre del producto

SPEED PELLET

Descripción del producto

Alimento balanceado para camarón Litopenaeus
vannamei, elaborado por proceso de extruido.
"""

# Plantilla Shrimpy (Happiness/Fitness): no tiene el encabezado "ALIMENTO
# BALANCEADO X PARA CAMARON", la tecnologia solo aparece en la descripcion.
SHRIMPY_TEXT = """FICHA TECNICA
SHRIMPY HAPPINESS 35% pellet
ALIMENTO BALANCEADO PARA CAMARONES
DESCRIPCIÓN DEL PRODUCTO:
Alimento balanceado pelletizado para camarones juveniles y de engorde que
proporciona los nutrientes esenciales para el camarón.
"""


def test_speed_pellet_contradiction_resolves_to_pelletizado():
    assert schema.detect_tecnologia(SPEED_TEXT) == "Pelletizado"


def test_shrimpy_template_reads_tecnologia_from_description():
    assert schema.detect_tecnologia(SHRIMPY_TEXT) == "Pelletizado"


def test_line_number_extracts_first_number_on_matching_line():
    text = "Humedad 12% Max\nProteina 35% Min\nGrasa 4% Min"
    assert parser._line_number(text, r"prote[ií]na") == 35.0
    assert parser._line_number(text, r"grasa") == 4.0
    assert parser._line_number(text, r"vitamina") is None


def test_extract_pellet_mm_dedupes_and_sorts():
    text = "Presentacion en 2.0 mm y 1.2 mm, tambien 2.0 mm"
    assert parser._extract_pellet_mm(text) == "1.2,2.0"


def test_extract_pellet_mm_no_match_returns_none():
    assert parser._extract_pellet_mm("sin datos de calibre") is None


def test_extract_empaque_kg():
    text = (
        "Empaque\nSacos de polipropileno laminado en presentacion de 25 kg\n"
        "Condiciones de almacenamiento: lugar fresco y seco."
    )
    assert parser._extract_empaque_kg(text) == "25"


def test_infer_etapa_pl10_is_precria():
    assert (
        parser._infer_etapa("starter-pro", "distribuido a partir de PL 10 hasta talla de siembra")
        == "precria"
    )


def test_infer_etapa_disease_marker_no_longer_returns_salud():
    # "salud" ya no es un valor de etapa (ver producto_salud abajo) -- sin
    # otro marcador de rango, el texto de enfermedad solo no resuelve etapa.
    assert parser._infer_etapa("x", "previene enfermedades en el intestino del camaron por Vibrio") is None


def test_infer_etapa_keeps_stage_info_alongside_disease_marker():
    # Caso real que motivo el fix (usuario 2026-09-02): antes, el marcador
    # de enfermedad devolvia "salud" y cortaba el resto sin mirar si el
    # texto tambien describia una etapa real -- ahora si se resuelve.
    text = "previene enfermedades por Vibrio, alimento hasta tamaño de mercado"
    assert parser._infer_etapa("x", text) == "engorde"


# La deteccion de producto_salud es compartida (schema.detect_producto_salud,
# probada en test_schema.py) -- ya no vive como funcion local de este parser.


def test_infer_etapa_starter_slug_fallback():
    # Unico caso sin marcador textual (MEMORY.md): la ficha de "Starter"
    # describe el rango en gramos (1 a 3 g) sin mencionar PL ni tamano de
    # mercado -- se resuelve a mano a precria por el propio agrupamiento
    # del sitio (tab "Iniciadores" junto a Starter Pro).
    assert parser._infer_etapa("starter", "de 1 a 3 gramos de peso") == "precria"


def test_infer_etapa_late_marker_without_pl10_is_engorde():
    assert parser._infer_etapa("speed", "alimento hasta tamaño de mercado") == "engorde"


def test_parse_product_explodes_one_row_per_tamano_repeating_shared_fields():
    # Caso real Speed/Happiness/Fitness (MEMORY.md): un solo % de proteina
    # para los 3 calibres, asi que el fan-out debe repetir ese valor tal
    # cual en cada fila, no inventar una variacion que la ficha no publica.
    html = (
        '<html><head><meta property="og:title" content="Speed Pellet"></head>'
        "<body>Tamaños: 1.2 mm, 1.6 mm, 2.0 mm</body></html>"
    )
    records = parser.parse_product("https://www.haid.com.ec/speed/", html, pdf_bytes=None)
    assert [r["tamano_pellet_mm"] for r in records] == ["1.2", "1.6", "2.0"]
    assert {r["nombre_producto"] for r in records} == {"HAID Speed Pellet"}
    assert {r["empresa"] for r in records} == {"HAID"}
    assert {r["fuente_url"] for r in records} == {"https://www.haid.com.ec/speed/"}


def test_parse_product_single_tamano_returns_one_row():
    html = "<html><body>Tamaño: 0.8 mm</body></html>"
    records = parser.parse_product("https://www.haid.com.ec/starter/", html, pdf_bytes=None)
    assert len(records) == 1
    assert records[0]["tamano_pellet_mm"] == "0.8"


def test_parse_product_no_tamano_returns_single_null_row():
    records = parser.parse_product("https://www.haid.com.ec/unknown/", html="", pdf_bytes=None)
    assert len(records) == 1
    assert records[0]["tamano_pellet_mm"] is None


# Texto real extraido (incluye ruido de OCR: "#0"/"#1"/"#2" salen como
# "++0"/"+1"/"+2") de la ficha Starter Pro -- caso real que motivo el fix:
# 10kg para los calibres chicos, 25kg para el grande, dentro del MISMO
# producto. Ver MEMORY.md.
STARTER_PRO_EMPAQUE_TEXT = (
    "Empaque\n\nY” Sacos de polipropileno laminado en presentación de\n"
    "10kg para los diámetros ++0 - 0.3mm, +1 - 0.5 mm.\n\n"
    "Y” Sacos de polipropileno laminado en presentación de\n"
    "25 kg para el diámetro +2 - 0.8 mm.\n\n"
)

# Texto real de Speed: un solo kg (25) para 3 diametros -- incluye el mismo
# giro de frase ("para los diametros") pero SIN desglose real de peso.
SPEED_EMPAQUE_TEXT = (
    "Empaque\n\nSacos de polipropileno laminado en presentación de\n"
    "25kg para los diámetros +t3 - 1.2mm, ++4 - 1.6 mm,\nH5 - 2.0 mm.\n\n"
)


def test_extract_empaque_pairs_splits_kg_by_diametro():
    pairs = parser._extract_empaque_pairs(STARTER_PRO_EMPAQUE_TEXT)
    assert pairs == {0.3: "10", 0.5: "10", 0.8: "25"}


def test_extract_empaque_pairs_single_kg_for_all_diametros():
    # No cambia nada respecto a _extract_empaque_kg -- las 3 llaves
    # apuntan al mismo valor, igual que el comportamiento actual.
    pairs = parser._extract_empaque_pairs(SPEED_EMPAQUE_TEXT)
    assert pairs == {1.2: "25", 1.6: "25", 2.0: "25"}


def test_extract_empaque_pairs_no_diametro_phrase_returns_empty():
    # Caso real Happiness/Fitness (plantilla Shrimpy): "Presentacion 25kg"
    # sin desglose por diametro -- el llamador debe caer a
    # _extract_empaque_kg(), no inventar un desglose que no existe.
    text = "EMPAQUE\nSacos de polipropileno\nPresentación 25kg\n"
    assert parser._extract_empaque_pairs(text) == {}


def test_parse_product_starter_pro_assigns_correct_kg_per_tamano():
    pdf_path = ROOT / "data" / "raw" / "haid" / "Ficha-tecnica-Starter-pro-45_-Ext.pdf"
    if not pdf_path.exists():
        pytest.skip("PDF real no presente en este entorno (data/raw no poblado)")
    records = parser.parse_product(
        "https://www.haid.com.ec/starter-pro/",
        html="",
        pdf_bytes=pdf_path.read_bytes(),
    )
    by_tamano = {r["tamano_pellet_mm"]: r["empaque_kg"] for r in records}
    assert by_tamano == {"0.3": "10", "0.5": "10", "0.8": "25"}


def test_parse_product_fitness_keeps_stage_info_and_flags_salud():
    # Caso real que motivo el fix (usuario 2026-09-02): Fitness es "salud"
    # (previene enfermedades) pero su ficha tambien dice "camarones
    # juveniles y engorde" -- antes se perdia esa info porque el marcador
    # de enfermedad devolvia "salud" y cortaba el resto.
    pdf_path = ROOT / "data" / "raw" / "haid" / "Ficha-tecnica-Shrimpy-fitness-35-pellet.pdf"
    if not pdf_path.exists():
        pytest.skip("PDF real no presente en este entorno (data/raw no poblado)")
    records = parser.parse_product(
        "https://www.haid.com.ec/fitness/",
        html="",
        pdf_bytes=pdf_path.read_bytes(),
    )
    assert all(r["producto_salud"] is True for r in records)
    assert all(r["etapa"] == "engorde" for r in records)
