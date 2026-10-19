"""Fase 0 (PLAN_REGIONAL.md): el master de Ecuador regenerado con el pipeline
por pais debe tener las mismas filas que el de antes del refactor, ignorando
`pais` y `fecha_extraccion`. El baseline es una copia del master.csv previo."""
import pandas as pd

from conftest import FIXTURES, ROOT

IGNORAR = ["pais", "fecha_extraccion"]


def _cargar(path):
    df = pd.read_csv(path, dtype=str, keep_default_na=False, na_values=[""])
    df = df.drop(columns=[c for c in IGNORAR if c in df.columns])
    cols = sorted(df.columns)
    return df[cols].sort_values(cols).reset_index(drop=True)


def test_master_ecuador_matches_pre_refactor_baseline():
    actual = pd.read_csv(ROOT / "data" / "master.csv", dtype=str, keep_default_na=False, na_values=[""])
    ecuador = actual[actual["pais"] == "ecuador"]
    ecuador.to_csv(FIXTURES.parent / "_ecuador_tmp.csv", index=False)
    try:
        got = _cargar(FIXTURES.parent / "_ecuador_tmp.csv")
    finally:
        (FIXTURES.parent / "_ecuador_tmp.csv").unlink()
    expected = _cargar(FIXTURES / "master_ecuador_baseline.csv")
    pd.testing.assert_frame_equal(got, expected)
