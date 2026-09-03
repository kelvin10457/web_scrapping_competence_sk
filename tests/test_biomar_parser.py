from conftest import FIXTURES
from parsers import biomar as parser


def _load(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_exia_prime_multi_etapa_leaves_etapa_none():
    # Caso real (MEMORY.md): EXIA Prime publica DOS valores de Etapa en el
    # mismo <dd> ("De Engorde" y "De Alevinaje") -- el producto cubre mas
    # de una etapa, no se fuerza una sola.
    record = parser.parse_product(
        "https://www.biomar.com/.../exia-prime-shrimp", _load("biomar_exia_prime.html")
    )
    assert record["etapa"] is None
    assert record["nombre_producto"] == "EXIA Prime"


def test_inicio_focus_single_etapa_normalizes_to_post_transferencia():
    # INICIO Focus no tiene <dt>Producto</dt> en absoluto (uno de los 4
    # productos INICIO sin ese campo, ver MEMORY.md) -- nombre_producto
    # debe salir del <h1>, no del <dl>.
    record = parser.parse_product(
        "https://www.biomar.com/.../inicio-focus-shrimp", _load("biomar_inicio_focus.html")
    )
    assert record["etapa"] == "post_transferencia"
    assert record["nombre_producto"] == "INICIO Focus"


def test_smartcare_has_no_etapa_field_at_all():
    # SmartCare Balance H/P no tienen <dt>Etapa</dt> en absoluto -- None es
    # correcto, no una falla de parseo.
    record = parser.parse_product(
        "https://www.biomar.com/.../smartcare-balance-h-shrimp", _load("biomar_smartcare_h.html")
    )
    assert record["etapa"] is None
    assert record["nombre_producto"] == "SmartCare Balance H"


def test_biomar_never_invents_nutricional_data():
    record = parser.parse_product(
        "https://www.biomar.com/.../exia-prime-shrimp", _load("biomar_exia_prime.html")
    )
    assert record["proteina_pct"] is None
    assert record["grasa_pct"] is None
