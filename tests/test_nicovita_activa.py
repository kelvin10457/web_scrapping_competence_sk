"""R6.3: Nicovita activa en los 3 paises."""
import fuentes


def test_nicovita_activa_en_los_tres_paises():
    activas = fuentes.listar(solo_activas=True)
    for pais in ("ecuador", "honduras", "mexico"):
        assert (pais, "nicovita") in activas
    assert not any(e == "nicovita" for _, e in fuentes.INACTIVAS)
