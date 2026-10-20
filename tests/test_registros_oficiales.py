"""Fase 5: registros oficiales (SENASICA / eaduana) solo completan celdas vacias."""
import pandas as pd

import registros_oficiales as ro
from conftest import FIXTURES

FFFD = "�"  # asi viene la i acentuada en muchas filas del xlsx de SENASICA


def _senasica(*filas):
    cols = ["nombre", "empresa", "ingredientes", "formula", "uso", "dosis", "retiro",
            "registro", "clasificacion", "fecha_registro", "vigencia"]
    return pd.DataFrame([dict(zip(cols, f)) for f in filas], columns=cols)


def test_proteina_de_formula_formatos_reales():
    assert ro.proteina_de_formula(f"Prote{FFFD}na cruda, m{FFFD}n ?..30% Grasa cruda") == 30
    assert ro.proteina_de_formula(f"PROTE{FFFD}NA CRUDA 40.00 % M{FFFD}N GRASA CRUDA 9.00 %") == 40
    assert ro.proteina_de_formula("Humedad max: 11% Proteina mín: 45% Grasa min: 9%") == 45
    # ingrediente, no analisis garantizado
    assert ro.proteina_de_formula("proteinas de origen marino 68%; subproductos 18%") is None
    assert ro.proteina_de_formula(f"Cerelaes 34%;prote{FFFD}nas marinas 18%; prote{FFFD}na animal 13%") is None


def test_registros_senasica_solo_alimentos_de_camaron_y_mapea_empresa():
    df = _senasica(
        ["XTRU-DIX 2", "VIMIFOS, S.A. DE C.V.", "", f"Prote{FFFD}na cruda, min. 35%", "Alimento para camarón",
         "", "", "A-1", "ALIMENTO", "2021-01-01", "2024-11-13"],
        ["Aditivo X", "VIMIFOS, S.A. DE C.V.", "", "", "Para camarón", "", "", "A-2", "ADITIVO", "", ""],
        ["Tilapia 32", "VIMIFOS, S.A. DE C.V.", "", "Proteina cruda min. 32%", "Alimento para tilapia",
         "", "", "A-3", "ALIMENTO", "", ""],
    )
    regs = ro.registros_senasica(df)
    assert len(regs) == 1
    assert regs[0]["empresa"] == "Vimifos" and regs[0]["proteina_pct"] == 35
    assert regs[0]["vigencia"] == "2024-11-13" and regs[0]["pais"] == "mexico"


def test_parse_eaduana_ficha_real():
    exia = ro.parse_eaduana((FIXTURES / "eaduana_exia-prime-35.html").read_text(encoding="utf-8"))
    assert exia["nombre_producto"] == "Exia Prime 35"
    assert exia["proteina_pct"] == 35 and exia["tamano_pellet_mm"] == "2" and exia["empaque_kg"] == "25"
    assert exia["fuente_url"] == "https://www.eaduana.com/fracciones-arancelarias/exia-prime-35"
    # "3 mm (3000 micras)" es un solo calibre
    oyster = ro.parse_eaduana((FIXTURES / "eaduana_royal-oyster-black.html").read_text(encoding="utf-8"))
    assert oyster["tamano_pellet_mm"] == "3" and oyster["empaque_kg"] == "5"
    # Omega 35 es aceite de pescado: no es alimento para camaron
    assert ro.parse_eaduana((FIXTURES / "eaduana_omega-35.html").read_text(encoding="utf-8")) is None


def _master(*filas):
    cols = ["pais", "empresa", "nombre_producto", "proteina_pct", "tamano_pellet_mm", "empaque_kg"]
    return pd.DataFrame([dict(zip(cols, f)) for f in filas], columns=cols)


def _registros(*filas):
    return pd.DataFrame([{**dict.fromkeys(ro.REGISTRO_COLUMNS), **f} for f in filas],
                        columns=ro.REGISTRO_COLUMNS)


def test_aplicar_completa_solo_vacios_y_no_crea_filas():
    master = _master(["mexico", "Vimifos", "Xtrudix 2", "38", None, None],
                     ["mexico", "Nutrimar", "Intensivo", None, None, None])
    regs = _registros(
        {"fuente": "senasica", "pais": "mexico", "empresa": "Vimifos", "nombre_producto": "XTRU-DIX 2",
         "proteina_pct": "35.0", "registro": "A-1", "fuente_url": "u1"},
        {"fuente": "senasica", "pais": "mexico", "empresa": "Nutrimar", "nombre_producto": "INTENSIVO",
         "proteina_pct": "35.0", "registro": "A-2", "fuente_url": "u2"},
        {"fuente": "senasica", "pais": "mexico", "empresa": None, "nombre_producto": "Aquatec 35%",
         "proteina_pct": "40.0", "fuente_url": "u3"},
    )
    out, revisar, conflictos = ro.aplicar(master, regs)
    assert len(out) == 2
    assert out.loc[0, "proteina_pct"] == "38"  # el dato del sitio no se toca
    assert out.loc[1, "proteina_pct"] == "35"  # vacio completado
    assert list(revisar["estado"]) == ["difiere", "completa_nulo", "sin_match"]
    assert len(conflictos) == 1
    c = conflictos[0]
    assert (c["nombre_producto"], c["campo"], c["valor_elegido"], c["regla"]) == (
        "Intensivo", "proteina_pct", "35", "registro_oficial:senasica")
    assert "A-2" in c["candidatos"]


def test_aplicar_registros_repetidos_iguales_no_son_ambiguos_pero_distintos_si():
    master = _master(["mexico", "Api-Aba", "APICAMARÓN Dorado 35% 20Kg", None, None, None])
    dorado = {"fuente": "senasica", "pais": "mexico", "empresa": "Api-Aba",
              "nombre_producto": "APICAMARON DORADO 35 %", "proteina_pct": "35.0", "fuente_url": "u"}
    out, revisar, _ = ro.aplicar(master, _registros(dorado, {**dorado, "nombre_producto": "Apicamarón dorado 35%"}))
    assert out.loc[0, "proteina_pct"] == "35"
    out, revisar, conflictos = ro.aplicar(master, _registros(dorado, {**dorado, "proteina_pct": "40.0"}))
    assert pd.isna(out.loc[0, "proteina_pct"]) and not conflictos
    assert set(revisar["estado"]) == {"ambiguo"}


def test_build_master_aplica_registros_y_escribe_revision(tmp_path, monkeypatch):
    import pipeline
    import schema

    monkeypatch.setattr(pipeline, "PROCESSED_DIR", tmp_path / "processed")
    monkeypatch.setattr(pipeline, "MASTER_PATH", tmp_path / "master.csv")
    monkeypatch.setattr(pipeline, "CONFLICTOS_PATH", tmp_path / "conflictos.csv")
    monkeypatch.setattr(pipeline.fuentes, "listar", lambda *a, **k: [("mexico", "nutrimar")])
    rec = schema.empty_record("Nutrimar")
    rec.update(pais="mexico", nombre_producto="Intensivo")
    pipeline.write_csv([rec], pipeline.processed_path("mexico", "nutrimar"))
    _registros({"fuente": "senasica", "pais": "mexico", "empresa": "Nutrimar", "nombre_producto": "Intensivo",
                "proteina_pct": "35.0", "fuente_url": "u"}).to_csv(pipeline.registros_path(), index=False)

    pipeline.build_master()
    master = pd.read_csv(tmp_path / "master.csv")
    assert len(master) == 1 and master.loc[0, "proteina_pct"] == 35
    assert pd.read_csv(tmp_path / "conflictos.csv")["regla"].tolist() == ["registro_oficial:senasica"]
    assert pd.read_csv(tmp_path / "registros_oficiales.csv")["estado"].tolist() == ["completa_nulo"]
