"""R8.9: MIDA Panama (PDF nacional y PGA) como registro oficial complementario."""
import datetime

import pandas as pd

import registros_oficiales as ro
from conftest import FIXTURES

NACIONAL = FIXTURES / "mida" / "Alimentos-nacionales-vigentes-2026-1.pdf"
PGA = FIXTURES / "mida" / "Alimentos-registrados-en-PGA.pdf"
CORTE = datetime.date(2026, 11, 9)


def _por_registro(filas):
    return {f["registro"]: f for f in filas}


def test_req1_nacional_una_fila_por_registro():
    filas = ro.parse_mida_nacional(NACIONAL)
    regs = _por_registro(filas)
    assert len(regs) == len(filas) > 100  # sin encabezados repetidos ni duplicados
    assert regs["RA-2278-25"]["nombre_producto"] == "AQUANASA 25"
    assert regs["RA-2278-25"]["empresa_registro"] == "NUTRICIÓN ANIMAL, S.A."
    assert regs["RA-2278-25"]["vigencia"] == "2030-05-30"
    assert regs["RA-2447-23"]["nombre_producto"] == "EXCELLENT CAMARÓN"
    assert regs["RA-2447-23"]["vigencia"] == "2028-04-10"
    assert {"RA-2279-25", "RA-2280-25"} <= set(regs)


def test_req2_pga_celdas_de_varias_lineas():
    regs = _por_registro(ro.parse_mida_pga(PGA))
    m = regs["RA-2550-25"]
    assert m["nombre_producto"] == "MATEMAX"
    assert m["empresa_registro"] == "FARALLON AQUACULTURE,"
    assert m["vigencia"] == "2030-12-09"
    assert regs["RA-2494-23"]["nombre_producto"] == "CHICKEN WINGS"
    # celdas alineadas abajo: la linea de arriba va al registro de abajo
    assert regs["RA-2496-24"]["nombre_producto"] == "HARINA CARNE Y HUESO DE POLLO REDEPROSA"
    assert all(r.startswith("RA") for r in regs)
    # celdas de 3 lineas: cada fragmento queda en su registro (revision Codex)
    assert regs["RA-2502-25"]["nombre_producto"] == "SAL MINERAL NUTRIPAC GANADO ENGORDE"
    assert regs["RA-2502-25"]["empresa_registro"] == "NUTRIPAC S.A."
    assert regs["RA-2503-25"]["nombre_producto"] == "ALIMENTO BALANCEADO PARA POLLO EN CRECIMIENTO."
    assert regs["RA-2503-25"]["empresa_registro"] == "COOPERATIVA AGROPECUARIA DE SERVICIOS"
    assert regs["RA-2548-25"]["empresa_registro"] == "EMPRESAS MELO, S.A. (029)"
    assert regs["RA-2497-24"]["empresa_registro"] == "PANCHO’S KITCHEN S.A."


def test_req3_solo_camaron_explicito_o_curado():
    filas = (ro.parse_mida_nacional(NACIONAL) + ro.parse_mida_pga(PGA))
    nombres = sorted(r["nombre_producto"] for r in ro.registros_mida(filas, hoy=CORTE))
    assert nombres == ["AQUANASA 25", "AQUANASA 30", "AQUANASA 35", "EXCELLENT CAMARÓN", "MATEMAX"]


def test_req4_vigencia_vencida_fuera_e_ilegible_vacia():
    base = {"nombre_producto": "ALIMENTO CAMARON X", "clasificacion": "ALIMENTO BALANCEADO",
            "empresa_registro": "E", "fuente_url": "u"}
    filas = [dict(base, registro="R1", vigencia="2026-01-01"),
             dict(base, registro="R2", vigencia=None),
             dict(base, registro="R3", vigencia="2027-01-01")]
    out = _por_registro(ro.registros_mida(filas, hoy=CORTE))
    assert set(out) == {"R2", "R3"}
    assert out["R2"]["vigencia"] is None
    assert ro._fecha_es("30 DE MAYO DE 2025.") == "2025-05-30"
    assert ro._fecha_es("31 DE FEBRERITO DE 2025") is None


def test_req5_campos_tecnicos_vacios_y_fuente():
    filas = ro.parse_mida_nacional(NACIONAL)
    out = ro.registros_mida(filas, hoy=CORTE)
    assert out
    for r in out:
        assert r["fuente"] == "mida" and r["pais"] == "panama" and r["empresa"] is None
        assert r["proteina_pct"] is None and r["tamano_pellet_mm"] is None and r["empaque_kg"] is None
        assert set(r) == set(ro.REGISTRO_COLUMNS)


def test_req6_actualizar_mida_falla_sin_copia_y_senasica_sigue(tmp_path, monkeypatch):
    monkeypatch.setattr(ro, "MIDA_DIR", tmp_path / "mida")
    monkeypatch.setattr(ro, "_registros_senasica_eaduana",
                        lambda s, max_dias: [{"fuente": "senasica", "nombre_producto": "X"}])

    def falla(*a, **k):
        raise ConnectionError("dns")
    monkeypatch.setattr(ro.netutil, "get", falla)
    destino = tmp_path / "reg.csv"
    assert ro.actualizar(destino) == 1
    assert pd.read_csv(destino)["fuente"].tolist() == ["senasica"]


def test_req6_actualizar_usa_copia_de_mida_sin_red(tmp_path, monkeypatch):
    d = tmp_path / "mida"
    d.mkdir()
    for f in (NACIONAL, PGA):
        (d / f.name).write_bytes(f.read_bytes())
    monkeypatch.setattr(ro, "MIDA_DIR", d)
    monkeypatch.setattr(ro, "_registros_senasica_eaduana", lambda s, max_dias: [])
    llamadas = []
    monkeypatch.setattr(ro.netutil, "get", lambda *a, **k: llamadas.append(a))
    destino = tmp_path / "reg.csv"
    assert ro.actualizar(destino, max_dias=10**6) >= 5
    assert llamadas == []
    assert set(pd.read_csv(destino, dtype=str)["fuente"]) == {"mida"}


class _Resp:
    def __init__(self, content):
        self.content = content

    def raise_for_status(self):
        pass


def test_req6_descarga_con_ua_de_navegador(tmp_path, monkeypatch):
    monkeypatch.setattr(ro, "MIDA_DIR", tmp_path / "mida")
    monkeypatch.setattr(ro, "_registros_senasica_eaduana", lambda s, max_dias: [])
    enviados = []

    def get(session, url, **kw):
        enviados.append(kw["headers"]["User-Agent"])
        return _Resp((NACIONAL if "nacionales" in url else PGA).read_bytes())
    monkeypatch.setattr(ro.netutil, "get", get)
    assert ro.actualizar(tmp_path / "reg.csv", max_dias=0) == 5
    assert len(enviados) == 2 and all(ua.startswith("Mozilla/5.0 (Windows") for ua in enviados)


def test_req6_pdf_truncado_no_tumba_senasica_ni_pisa_la_copia(tmp_path, monkeypatch):
    d = tmp_path / "mida"
    d.mkdir()
    (d / NACIONAL.name).write_bytes(NACIONAL.read_bytes())
    monkeypatch.setattr(ro, "MIDA_DIR", d)
    monkeypatch.setattr(ro, "_registros_senasica_eaduana",
                        lambda s, max_dias: [{"fuente": "senasica", "nombre_producto": "X"}])
    monkeypatch.setattr(ro.netutil, "get", lambda *a, **k: _Resp(b"%PDF-1.5 truncado"))
    destino = tmp_path / "reg.csv"
    assert ro.actualizar(destino, max_dias=0) == 1 + 4  # senasica + la copia nacional
    assert (d / NACIONAL.name).read_bytes() == NACIONAL.read_bytes()
    assert not list(d.glob("*.nuevo.pdf"))


def test_req3_filtro_descarta_premezclas_y_poliquetos():
    assert ro._es_camaron_mida("ALIMENTO CAMARON 35", "ALIMENTO BALANCEADO")
    assert not ro._es_camaron_mida("PREMEZCLA PARA CAMARON", "PREMEZCLA")
    assert not ro._es_camaron_mida("POLIQUETOS PARA CAMARON", "POLIQUETOS CONGELADOS")
    assert not ro._es_camaron_mida("MICROMIX VITAMINAS CAMARÓN", "ALIMENTO")
    assert not ro._es_camaron_mida("AQUANASA 25", "ADITIVO ALIMENTARIO")
