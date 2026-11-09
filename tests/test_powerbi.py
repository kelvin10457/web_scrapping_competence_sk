"""R5.1 / R5.2: Excel por país y empresa para Power BI (contrato de columnas y tipos)."""
import pandas as pd
import pytest
from openpyxl import load_workbook

import powerbi


def _master_fila(**kw):
    base = {c: None for c in powerbi.POWERBI_COLUMNS}
    base.update({"pais": "ecuador", "empresa": "Nicovita", "nombre_producto": "Nicovita Classic"})
    base.update(kw)
    return base


def test_columnas_son_las_16_del_contrato_en_orden():
    # REQ-1: tabla "Excel para Power BI" de tech-stack.md
    assert powerbi.POWERBI_COLUMNS == [
        "pais", "empresa", "nombre_producto",
        "es_producto_de_salud", "etapa_reproductores", "etapa_larva", "etapa_post_larva",
        "etapa_precria", "etapa_post_transferencia", "etapa_engorde", "etapa_skt",
        "tamano_pellet_mm", "particula_min_mm", "particula_max_mm", "tipo_presentacion",
        "proteina_pct",
    ]


def test_etapa_competidor_y_metadata_quedan_fuera():
    for col in ["etapa_competidor", "empaque_kg", "fuente_url", "fecha_extraccion"]:
        assert col not in powerbi.POWERBI_COLUMNS


def test_booleanos_desde_texto_del_master():
    df = powerbi.a_contrato(pd.DataFrame([_master_fila(etapa_engorde="True", etapa_larva="False", etapa_precria="")]))
    assert df.loc[0, "etapa_engorde"] is True
    assert df.loc[0, "etapa_larva"] is False
    assert df.loc[0, "etapa_precria"] is None


def test_decimales_y_texto_tipados():
    df = powerbi.a_contrato(pd.DataFrame([_master_fila(
        particula_min_mm="0.5", particula_max_mm="1", proteina_pct="37.5", tamano_pellet_mm="0.5-1.0",
        tipo_presentacion="Pellet")]))
    assert df.loc[0, "particula_min_mm"] == 0.5
    assert df.loc[0, "particula_max_mm"] == 1.0
    assert df.loc[0, "proteina_pct"] == 37.5
    assert df.loc[0, "tamano_pellet_mm"] == "0.5-1.0"
    assert df.loc[0, "tipo_presentacion"] == "Pellet"


def test_vacio_no_se_inventa(tmp_path):
    df = powerbi.a_contrato(pd.DataFrame([_master_fila(proteina_pct="", tipo_presentacion="")]))
    assert df.loc[0, "proteina_pct"] is None or pd.isna(df.loc[0, "proteina_pct"])
    assert df.loc[0, "tipo_presentacion"] is None


def test_escribir_por_pais_y_empresa(tmp_path):
    master = pd.DataFrame([
        _master_fila(pais="ecuador", empresa="Nicovita", etapa_engorde="True"),
        _master_fila(pais="mexico", empresa="Vimifos", nombre_producto="Vimifos X", etapa_larva="True"),
    ])
    powerbi.escribir_todo(master, tmp_path / "powerbi", human_path=None)
    assert (tmp_path / "powerbi" / "ecuador" / "Nicovita.xlsx").exists()
    assert (tmp_path / "powerbi" / "mexico" / "Vimifos.xlsx").exists()


def test_contrato_de_columnas_y_tipos_en_el_xlsx(tmp_path):
    # REQ-2 y REQ-4: encabezados y tipos de celda idénticos en todos los Excel
    master = pd.DataFrame([
        _master_fila(pais="ecuador", empresa="Nicovita", etapa_engorde="True", proteina_pct="35",
                     particula_min_mm="1.2", particula_max_mm="1.2", tamano_pellet_mm="1.2"),
        _master_fila(pais="mexico", empresa="Vimifos", nombre_producto="Vimifos X", etapa_larva="False",
                     proteina_pct="", tipo_presentacion="Extruido"),
    ])
    root = tmp_path / "powerbi"
    powerbi.escribir_todo(master, root, human_path=None)
    tipos_por_archivo = []
    for archivo in sorted(root.glob("*/*.xlsx")):
        ws = load_workbook(archivo, read_only=True).active
        filas = list(ws.iter_rows(values_only=True))
        assert list(filas[0]) == powerbi.POWERBI_COLUMNS
        tipos = []
        for col_idx, col in enumerate(powerbi.POWERBI_COLUMNS):
            valor = next((r[col_idx] for r in filas[1:] if r[col_idx] is not None), None)
            tipos.append((col, type(valor).__name__ if valor is not None else None))
        tipos_por_archivo.append(tipos)
    assert len(tipos_por_archivo) == 2
    assert tipos_por_archivo[0] == tipos_por_archivo[1] or all(
        t1 == t2 or None in (t1[1], t2[1]) for t1, t2 in zip(tipos_por_archivo[0], tipos_por_archivo[1]))


def test_tipos_esperados_por_columna(tmp_path):
    master = pd.DataFrame([_master_fila(etapa_engorde="True", proteina_pct="35", particula_min_mm="1.2",
                                        particula_max_mm="1.2", tamano_pellet_mm="1.2")])
    powerbi.escribir_todo(master, tmp_path / "powerbi", human_path=None)
    ws = load_workbook(tmp_path / "powerbi" / "ecuador" / "Nicovita.xlsx", read_only=True).active
    fila = dict(zip(powerbi.POWERBI_COLUMNS, list(ws.iter_rows(values_only=True))[1]))
    assert fila["etapa_engorde"] is True
    assert isinstance(fila["proteina_pct"], (int, float))
    assert isinstance(fila["particula_min_mm"], (int, float))
    assert isinstance(fila["tamano_pellet_mm"], str)
    assert isinstance(fila["nombre_producto"], str)


def test_filas_humanas_sin_pais_se_asumen_ecuador(tmp_path):
    # R5.2 + regla existente de merge_human (PLAN_REGIONAL 2.5)
    humano = tmp_path / "humano.xlsx"
    pd.DataFrame([{
        "empresa": "HAID", "nombre_producto": "HAID Ultra", "etapa_precria": True,
        "tamano_pellet_mm": 1.0, "tipo_presentacion": "Extruido", "proteina_pct": 40,
    }]).to_excel(humano, index=False)
    df = powerbi.filas_humanas(humano)
    assert df.loc[0, "pais"] == "ecuador"
    assert bool(df.loc[0, "etapa_precria"]) is True
    assert df.loc[0, "etapa_skt"] is not None


def test_filas_humanas_usan_booleanos_no_etapa_competidor(tmp_path):
    # Revision Codex 2026-11-09: etapa_competidor (legado) no se usa; etapa_skt sale de etapa_*.
    humano = tmp_path / "humano.xlsx"
    pd.DataFrame([
        {"empresa": "Nicovita", "nombre_producto": "A", "etapa_competidor": "larva", "tamano_pellet_mm": 0.3},
        {"empresa": "Nicovita", "nombre_producto": "B", "etapa_larva": True, "tamano_pellet_mm": 0.3},
    ]).to_excel(humano, index=False)
    df = powerbi.filas_humanas(humano).set_index("nombre_producto")
    assert df.loc["A", "etapa_skt"] == "Nursery"
    assert df.loc["B", "etapa_skt"] == "Hatchery"


def test_filas_humanas_van_a_su_pais_y_empresa(tmp_path):
    humano = tmp_path / "humano.xlsx"
    pd.DataFrame([{
        "pais": "mexico", "empresa": "Vimifos", "nombre_producto": "Vimifos Humano",
        "tamano_pellet_mm": 1.6, "proteina_pct": 35,
    }]).to_excel(humano, index=False)
    master = pd.DataFrame([_master_fila(pais="mexico", empresa="Vimifos", nombre_producto="Vimifos X")])
    powerbi.escribir_todo(master, tmp_path / "powerbi", human_path=humano)
    ws = load_workbook(tmp_path / "powerbi" / "mexico" / "Vimifos.xlsx", read_only=True).active
    nombres = [r[2] for r in list(ws.iter_rows(values_only=True))[1:]]
    assert nombres == ["Vimifos X", "Vimifos Humano"]


def test_valor_no_convertible_queda_vacio_y_se_avisa():
    # Revisión Codex 2026-11-09: un valor no vacío que no se puede tipar no se pierde en silencio.
    powerbi.AVISOS.clear()
    df = powerbi.a_contrato(pd.DataFrame([_master_fila(proteina_pct="35%", etapa_larva="quizas")]))
    assert df.loc[0, "proteina_pct"] is None
    assert df.loc[0, "etapa_larva"] is None
    assert any("35%" in a for a in powerbi.AVISOS)
    assert any("quizas" in a for a in powerbi.AVISOS)


def test_reasignar_pais_no_deja_archivo_viejo(tmp_path):
    # Revisión Codex 2026-11-09: si un par (pais, empresa) desaparece, su Excel viejo se borra.
    humano = tmp_path / "humano.xlsx"
    pd.DataFrame([{"pais": "ecuador", "empresa": "Vimifos", "nombre_producto": "Vimifos H"}]).to_excel(humano, index=False)
    root = tmp_path / "powerbi"
    vacio = pd.DataFrame(columns=powerbi.POWERBI_COLUMNS)
    powerbi.escribir_todo(vacio, root, human_path=humano)
    assert (root / "ecuador" / "Vimifos.xlsx").exists()
    pd.DataFrame([{"pais": "mexico", "empresa": "Vimifos", "nombre_producto": "Vimifos H"}]).to_excel(humano, index=False)
    powerbi.escribir_todo(vacio, root, human_path=humano)
    assert not (root / "ecuador" / "Vimifos.xlsx").exists()
    assert (root / "mexico" / "Vimifos.xlsx").exists()
