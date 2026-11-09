"""R5.3: contrato de los Excel de Power BI (data/powerbi/<pais>/<empresa>.xlsx).

Todos los archivos deben tener las mismas columnas, en el mismo orden, y cada
columna debe tener un solo tipo de celda (booleano, número o texto)."""
from pathlib import Path

import pytest
from openpyxl import load_workbook

import powerbi

ROOT = Path(__file__).resolve().parent.parent
ARCHIVOS = sorted((ROOT / "data" / "powerbi").glob("*/*.xlsx"))


@pytest.mark.skipif(not ARCHIVOS, reason="aún no se generaron los Excel de Power BI")
def test_todos_los_excel_tienen_las_mismas_columnas_en_el_mismo_orden():
    for archivo in ARCHIVOS:
        ws = load_workbook(archivo, read_only=True).active
        encabezado = list(next(ws.iter_rows(values_only=True)))
        assert encabezado == powerbi.POWERBI_COLUMNS, archivo.name


@pytest.mark.skipif(not ARCHIVOS, reason="aún no se generaron los Excel de Power BI")
def test_cada_columna_tiene_un_solo_tipo_de_celda_en_todos_los_excel():
    tipos_por_columna: dict[str, set[str]] = {c: set() for c in powerbi.POWERBI_COLUMNS}
    for archivo in ARCHIVOS:
        filas = list(load_workbook(archivo, read_only=True).active.iter_rows(values_only=True))
        for fila in filas[1:]:
            for col, valor in zip(powerbi.POWERBI_COLUMNS, fila):
                if valor is None:
                    continue
                tipos_por_columna[col].add("booleano" if isinstance(valor, bool) else
                                           "numero" if isinstance(valor, (int, float)) else "texto")
    for col, tipos in tipos_por_columna.items():
        assert len(tipos) <= 1, f"{col}: {tipos}"
        if col in powerbi.BOOLEAN_COLUMNS:
            assert tipos <= {"booleano"}, col
        if col in powerbi.DECIMAL_COLUMNS:
            assert tipos <= {"numero"}, col
        if col in powerbi.TEXT_COLUMNS:
            assert tipos <= {"texto"}, col
