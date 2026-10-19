import pandas as pd
import pytest

import merge_human
import schema

ROOT = merge_human.ROOT


def _human_row(**overrides) -> dict:
    row = {col: None for col in schema.SCHEMA_COLUMNS}
    row.update(overrides)
    return row


def _human_df(*rows) -> pd.DataFrame:
    return pd.DataFrame(list(rows), columns=schema.SCHEMA_COLUMNS)


def _master_row(**overrides) -> dict:
    row = {col: None for col in schema.SCHEMA_COLUMNS}
    row.update(overrides)
    return row


def _master_df(*rows) -> pd.DataFrame:
    return pd.DataFrame(list(rows), columns=schema.SCHEMA_COLUMNS)


# --- validate_headers ---------------------------------------------------


def test_validate_headers_detects_renamed_column():
    # Caso real: alguien renombra "empresa" a "compania" al editar el Excel
    # a mano -- debe detenerse antes de mirar ninguna fila.
    bad_columns = [c if c != "empresa" else "compania" for c in schema.SCHEMA_COLUMNS]
    df = pd.DataFrame(columns=bad_columns)
    errors = merge_human.validate_headers(df)
    assert any("Faltan columnas" in e and "empresa" in e for e in errors)
    assert any("Sobran columnas" in e and "compania" in e for e in errors)


def test_validate_headers_ok_when_exact_match_regardless_of_order():
    shuffled = list(reversed(schema.SCHEMA_COLUMNS))
    df = pd.DataFrame(columns=shuffled)
    assert merge_human.validate_headers(df) == []


# --- validate_rows -------------------------------------------------------


def test_validate_rows_detects_invalid_categorical_value():
    df = _human_df(
        _human_row(empresa="Nicovita", nombre_producto="X", etapa_competidor="Engordee"),
    )
    errors = merge_human.validate_rows(df)
    assert len(errors) == 1
    assert "fila 2, columna etapa_competidor" in errors[0]
    assert "Engordee" in errors[0]


def test_validate_rows_detects_non_numeric_value():
    df = _human_df(
        _human_row(empresa="Nicovita", nombre_producto="X", proteina_pct="alta"),
    )
    errors = merge_human.validate_rows(df)
    assert len(errors) == 1
    assert "fila 2, columna proteina_pct" in errors[0]


def test_validate_rows_requires_empresa_and_nombre_producto():
    df = _human_df(_human_row())
    errors = merge_human.validate_rows(df)
    assert any("columna empresa" in e for e in errors)
    assert any("columna nombre_producto" in e for e in errors)


def test_validate_rows_accumulates_all_errors_across_rows():
    # No debe detenerse en el primer error -- el reporte tiene que cubrir
    # el archivo completo de una sola pasada.
    df = _human_df(
        _human_row(empresa="Nicovita", nombre_producto="X", etapa_competidor="Engordee"),
        _human_row(empresa="Nicovita", nombre_producto="Y", proteina_pct="alta"),
    )
    errors = merge_human.validate_rows(df)
    assert len(errors) == 2


def test_validate_rows_accepts_valid_values_and_empty_cells():
    df = _human_df(
        _human_row(
            empresa="Nicovita",
            nombre_producto="X",
            etapa_competidor="engorde",
            tipo_presentacion="Pelletizado",
            etapa_skt="Grower",
            producto_salud=True,
            tamano_pellet_mm=2.0,
            proteina_pct=35,
            empaque_kg=25,
        ),
    )
    assert merge_human.validate_rows(df) == []


def test_validate_rows_accepts_boolean_as_0_1_float():
    # Hallazgo real: al guardar competencia_human.xlsx con pandas, una
    # columna booleana con alguna celda vacia se lee de vuelta como 0.0/1.0
    # en vez de True/False -- no es un error de captura del usuario.
    df = _human_df(
        _human_row(empresa="Nicovita", nombre_producto="X", producto_salud=0.0),
        _human_row(empresa="Nicovita", nombre_producto="Y", producto_salud=1.0),
    )
    assert merge_human.validate_rows(df) == []


# --- find_matches / apply_merge (master sintetico) ------------------------


def _synthetic_master():
    return _master_df(
        _master_row(
            empresa="Nicovita",
            nombre_producto="Nicovita Classic",
            etapa_competidor=None,
            producto_salud=None,
            tamano_pellet_mm="1.6",
            tipo_presentacion="Pelletizado",
            empaque_kg=25.0,
            proteina_pct=35.0,
            fuente_url="https://nicovita.com/productos/nicovita-classic-ecuador/",
            fecha_extraccion="2026-09-02",
        ),
        _master_row(
            empresa="Nicovita",
            nombre_producto="Nicovita Classic",
            etapa_competidor="engorde",
            producto_salud=None,
            tamano_pellet_mm="2.5",
            tipo_presentacion="Pelletizado",
            empaque_kg=25.0,
            proteina_pct=35.0,
            fuente_url="https://nicovita.com/productos/nicovita-classic-ecuador/",
            fecha_extraccion="2026-09-02",
        ),
        _master_row(
            empresa="Nicovita",
            nombre_producto="Nicovita Classic",
            etapa_competidor="engorde",
            producto_salud=None,
            tamano_pellet_mm="2.5",
            tipo_presentacion="Pelletizado",
            empaque_kg=25.0,
            proteina_pct=28.0,
            fuente_url="https://nicovita.com/productos/nicovita-classic-ecuador/",
            fecha_extraccion="2026-09-02",
        ),
    )


def test_apply_merge_new_product_has_zero_matches_and_gets_appended():
    master = _synthetic_master()
    human = _human_df(
        _human_row(
            empresa="Nicovita",
            nombre_producto="Nicovita Ultra",
            etapa_competidor="engorde",
            tamano_pellet_mm=2.2,
            tipo_presentacion="Pelletizado",
            empaque_kg=25,
            proteina_pct=32,
        )
    )
    updated, review, n_new, n_updated = merge_human.apply_merge(master, human)
    assert n_new == 1
    assert n_updated == 0
    assert review == []
    assert len(updated) == len(master) + 1
    new_row = updated.iloc[-1]
    assert new_row["nombre_producto"] == "Nicovita Ultra"
    assert new_row["proteina_pct"] == 32.0
    # etapa_skt se recalcula, nunca se deja vacia si se puede derivar.
    assert new_row["etapa_skt"] == "Grower"


def test_apply_merge_fills_null_field_on_single_match():
    master = _synthetic_master()
    human = _human_df(
        _human_row(
            empresa="Nicovita",
            nombre_producto="Nicovita Classic",
            tamano_pellet_mm=1.6,
            proteina_pct=35,
            etapa_competidor="precria",
        )
    )
    updated, review, n_new, n_updated = merge_human.apply_merge(master, human)
    assert n_new == 0
    assert n_updated == 1
    assert review == []
    row = updated.iloc[0]
    assert row["etapa_competidor"] == "precria"
    # etapa_skt se recalcula a partir del tamano ya corregido.
    assert row["etapa_skt"] == "Pre Grower"


def test_apply_merge_overwrites_incorrect_value_on_single_match():
    master = _synthetic_master()
    human = _human_df(
        _human_row(
            empresa="Nicovita",
            nombre_producto="Nicovita Classic",
            tamano_pellet_mm=2.5,
            proteina_pct=28,
            empaque_kg=20,
        )
    )
    updated, review, n_new, n_updated = merge_human.apply_merge(master, human)
    assert n_new == 0
    assert n_updated == 1
    row = updated.iloc[2]
    assert row["empaque_kg"] == 20.0
    # Las otras filas de Nicovita Classic no se tocan.
    assert updated.iloc[0]["empaque_kg"] == 25.0
    assert updated.iloc[1]["empaque_kg"] == 25.0


def test_apply_merge_leaves_master_untouched_when_ambiguous():
    master = _synthetic_master()
    human = _human_df(
        _human_row(
            empresa="Nicovita",
            nombre_producto="Nicovita Classic",
            tamano_pellet_mm=2.5,
            empaque_kg=99,
        )
    )
    updated, review, n_new, n_updated = merge_human.apply_merge(master, human)
    assert n_new == 0
    assert n_updated == 0
    assert len(review) == 1
    assert review[0]["cantidad_coincidencias"] == 2
    # Ninguna de las 2 filas candidatas se modifico.
    assert updated.iloc[1]["empaque_kg"] == 25.0
    assert updated.iloc[2]["empaque_kg"] == 25.0


def test_apply_merge_matching_is_case_and_whitespace_insensitive():
    master = _synthetic_master()
    human = _human_df(
        _human_row(
            empresa="  nicovita ",
            nombre_producto="NICOVITA CLASSIC",
            tamano_pellet_mm=1.6,
            proteina_pct=35,
            etapa_competidor="precria",
        )
    )
    updated, review, n_new, n_updated = merge_human.apply_merge(master, human)
    assert n_new == 0
    assert n_updated == 1


# --- integracion contra data/master.xlsx real ------------------------------


@pytest.fixture()
def real_master_df():
    path = ROOT / "data" / "master.xlsx"
    if not path.exists():
        pytest.skip("data/master.xlsx no existe en este checkout")
    return pd.read_excel(path)


def test_real_master_nicovita_classic_same_caliber_is_ambiguous_by_protein(real_master_df):
    # Caso real confirmado por el usuario: "Nicovita Classic" tiene 9 filas
    # con el mismo nombre que solo cambian en calibre y/o proteina -- 4 de
    # ellas comparten tamano_pellet_mm=2.5 con proteina distinta (35/30/28/25).
    # Sin proteina_pct, una fila humana con solo el calibre debe quedar
    # ambigua contra las 4, no matchear una al azar.
    human_row = pd.Series(
        _human_row(empresa="Nicovita", nombre_producto="Nicovita Classic", tamano_pellet_mm=2.5)
    )
    matches = merge_human.find_matches(real_master_df, human_row)
    assert len(matches) == 4
    proteinas = sorted(real_master_df.loc[matches, "proteina_pct"].tolist())
    assert proteinas == [25.0, 28.0, 30.0, 35.0]


def test_real_master_nicovita_classic_caliber_and_protein_resolves_single_match(real_master_df):
    human_row = pd.Series(
        _human_row(
            empresa="Nicovita",
            nombre_producto="Nicovita Classic",
            tamano_pellet_mm=2.5,
            proteina_pct=28,
        )
    )
    matches = merge_human.find_matches(real_master_df, human_row)
    assert len(matches) == 1


def test_real_master_end_to_end_merge_updates_only_the_matched_row(real_master_df):
    human = _human_df(
        _human_row(
            empresa="Nicovita",
            nombre_producto="Nicovita Classic",
            tamano_pellet_mm=2.5,
            proteina_pct=28,
            empaque_kg=20,
        ),
        _human_row(
            empresa="Nicovita",
            nombre_producto="Nicovita Producto Que No Existe",
            etapa_competidor="engorde",
            tamano_pellet_mm=2.2,
            tipo_presentacion="Pelletizado",
            empaque_kg=25,
            proteina_pct=32,
        ),
    )
    updated, review, n_new, n_updated = merge_human.apply_merge(real_master_df, human)
    assert n_new == 1
    assert n_updated == 1
    assert review == []
    corrected = updated[
        (updated.empresa == "Nicovita")
        & (updated.nombre_producto == "Nicovita Classic")
        & (updated.tamano_pellet_mm == "2.5")
        & (updated.proteina_pct == 28.0)
    ]
    assert len(corrected) == 1
    assert corrected.iloc[0]["empaque_kg"] == 20.0


# --- find_name_candidates / apply_merge_many (consolidacion multi-archivo) --


def test_find_name_candidates_ignores_tamano_and_proteina():
    master = _synthetic_master()
    candidates = merge_human.find_name_candidates(master, "Nicovita", "Nicovita Classic")
    assert len(candidates) == 3


def test_find_name_candidates_is_case_and_whitespace_insensitive():
    master = _synthetic_master()
    candidates = merge_human.find_name_candidates(master, "  NICOVITA ", "nicovita classic")
    assert len(candidates) == 3


def test_apply_merge_many_second_source_sees_first_sources_additions():
    # Simula 2 companeros agregando el mismo producto nuevo sin saberse --
    # el segundo archivo debe verlo como una correccion sobre lo que el
    # primero ya agrego, no como un duplicado.
    master = _synthetic_master()
    first = _human_df(
        _human_row(
            empresa="Nicovita",
            nombre_producto="Nicovita Ultra",
            etapa_competidor="engorde",
            tamano_pellet_mm=2.2,
            tipo_presentacion="Pelletizado",
            empaque_kg=25,
            proteina_pct=32,
        )
    )
    second = _human_df(
        _human_row(
            empresa="Nicovita",
            nombre_producto="Nicovita Ultra",
            tamano_pellet_mm=2.2,
            proteina_pct=32,
            empaque_kg=20,
        )
    )
    updated, review, n_new, n_updated = merge_human.apply_merge_many(master, [first, second])
    assert n_new == 1
    assert n_updated == 1
    assert review == []
    new_row = updated[updated.nombre_producto == "Nicovita Ultra"].iloc[0]
    assert new_row["empaque_kg"] == 20.0


def test_apply_merge_many_skips_empty_dataframes():
    master = _synthetic_master()
    empty = _human_df()
    updated, review, n_new, n_updated = merge_human.apply_merge_many(master, [empty])
    assert n_new == 0
    assert n_updated == 0
    assert review == []
    assert len(updated) == len(master)


# --- ensure_human_template / main (I/O real, aislado en tmp_path) --------


def test_ensure_human_template_creates_file_with_exact_headers(tmp_path, monkeypatch):
    human_path = tmp_path / "competencia_human.xlsx"
    monkeypatch.setattr(merge_human, "HUMAN_PATH", human_path)
    created = merge_human.ensure_human_template()
    assert created is True
    assert human_path.exists()
    df = pd.read_excel(human_path)
    assert list(df.columns) == schema.SCHEMA_COLUMNS
    assert len(df) == 0


def test_ensure_human_template_noop_if_file_already_exists(tmp_path, monkeypatch):
    human_path = tmp_path / "competencia_human.xlsx"
    pd.DataFrame(columns=schema.SCHEMA_COLUMNS).to_excel(human_path, index=False)
    monkeypatch.setattr(merge_human, "HUMAN_PATH", human_path)
    created = merge_human.ensure_human_template()
    assert created is False


def test_main_blocks_everything_when_any_row_is_invalid(tmp_path, monkeypatch):
    master_path = tmp_path / "master.xlsx"
    human_path = tmp_path / "competencia_human.xlsx"
    output_path = tmp_path / "master_prototipo.xlsx"

    _synthetic_master().to_excel(master_path, index=False)
    _human_df(
        _human_row(
            empresa="Nicovita",
            nombre_producto="Nicovita Ultra",
            etapa_competidor="engorde",
            tamano_pellet_mm=2.2,
            tipo_presentacion="Pelletizado",
            empaque_kg=25,
            proteina_pct=32,
        ),
        _human_row(empresa="Nicovita", nombre_producto="X", etapa_competidor="Engordee"),
    ).to_excel(human_path, index=False)

    monkeypatch.setattr(merge_human, "MASTER_PATH", master_path)
    monkeypatch.setattr(merge_human, "HUMAN_PATH", human_path)
    monkeypatch.setattr(merge_human, "OUTPUT_PATH", output_path)

    rc = merge_human.main()
    assert rc == 1
    assert not output_path.exists()


def test_main_writes_master_and_revisar_sheets_when_valid(tmp_path, monkeypatch):
    master_path = tmp_path / "master.xlsx"
    human_path = tmp_path / "competencia_human.xlsx"
    output_path = tmp_path / "master_prototipo.xlsx"

    _synthetic_master().to_excel(master_path, index=False)
    _human_df(
        _human_row(
            empresa="Nicovita",
            nombre_producto="Nicovita Classic",
            tamano_pellet_mm=1.6,
            proteina_pct=35,
            etapa_competidor="precria",
        ),
        _human_row(
            empresa="Nicovita", nombre_producto="Nicovita Classic", tamano_pellet_mm=2.5, empaque_kg=99
        ),
    ).to_excel(human_path, index=False)

    monkeypatch.setattr(merge_human, "MASTER_PATH", master_path)
    monkeypatch.setattr(merge_human, "HUMAN_PATH", human_path)
    monkeypatch.setattr(merge_human, "OUTPUT_PATH", output_path)

    rc = merge_human.main()
    assert rc == 0
    assert output_path.exists()

    master_sheet = pd.read_excel(output_path, sheet_name="master")
    revisar_sheet = pd.read_excel(output_path, sheet_name="revisar")
    assert list(master_sheet.columns) == schema.SCHEMA_COLUMNS
    assert len(revisar_sheet) == 1
