import pandas as pd
import pytest

import manual_store
import schema


def test_fetch_all_on_missing_file_returns_empty_df(tmp_path):
    db_path = tmp_path / "no_existe.db"
    df = manual_store.fetch_all(db_path)
    assert df.empty
    assert list(df.columns) == schema.SCHEMA_COLUMNS


def test_ensure_db_creates_file_and_table(tmp_path):
    db_path = tmp_path / "manual.db"
    manual_store.ensure_db(db_path)
    assert db_path.exists()
    df = manual_store.fetch_all(db_path)
    assert list(df.columns) == schema.SCHEMA_COLUMNS
    assert df.empty


def test_insert_record_then_fetch_all_roundtrips(tmp_path):
    db_path = tmp_path / "manual.db"
    record = {col: None for col in schema.SCHEMA_COLUMNS}
    record.update(empresa="Nicovita", nombre_producto="Producto X", tamano_pellet_mm="2.0")
    rowid = manual_store.insert_record(record, db_path)
    assert rowid == 1
    df = manual_store.fetch_all(db_path)
    assert len(df) == 1
    assert df.iloc[0]["empresa"] == "Nicovita"
    assert df.iloc[0]["nombre_producto"] == "Producto X"
    assert df.iloc[0]["tamano_pellet_mm"] == "2.0"


def test_insert_multiple_records_preserves_insertion_order(tmp_path):
    db_path = tmp_path / "manual.db"
    for nombre in ["A", "B", "C"]:
        record = {col: None for col in schema.SCHEMA_COLUMNS}
        record.update(empresa="Nicovita", nombre_producto=nombre)
        manual_store.insert_record(record, db_path)
    df = manual_store.fetch_all(db_path)
    assert list(df["nombre_producto"]) == ["A", "B", "C"]


def test_fetch_all_on_non_database_file_raises_value_error(tmp_path):
    bad_path = tmp_path / "not_a_db.db"
    bad_path.write_text("esto no es una base de datos sqlite")
    with pytest.raises(ValueError):
        manual_store.fetch_all(bad_path)
