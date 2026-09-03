import pipeline


def test_format_value_strips_trailing_zero_from_whole_float():
    # Hallazgo del usuario 2026-09-02: proteina_pct/grasa_pct de HAID y
    # Aquaxcel salian como float crudo (35.0) mientras tamano_pellet_mm/
    # empaque_kg ya se limpiaban con :g -- un visor de CSV con locale en
    # español puede leer el "." como separador de miles y mostrar 350.
    assert pipeline._format_value(35.0) == "35"
    assert pipeline._format_value(4.0) == "4"


def test_format_value_keeps_real_decimals():
    assert pipeline._format_value(35.5) == "35.5"


def test_format_value_passes_through_non_float():
    assert pipeline._format_value("35") == "35"
    assert pipeline._format_value("0.5-1.0") == "0.5-1.0"
    assert pipeline._format_value(None) is None


def test_write_csv_output_has_no_trailing_zero_floats(tmp_path):
    records = [
        {
            "empresa": "HAID",
            "nombre_producto": "HAID Speed",
            "etapa": "engorde",
            "tamano_pellet_mm": "1.2",
            "tipo_presentacion": "Pelletizado",
            "empaque_kg": "25",
            "proteina_pct": 37.0,
            "grasa_pct": 5.0,
            "fuente_url": "https://www.haid.com.ec/speed/",
            "fecha_extraccion": "2026-09-02",
        }
    ]
    path = tmp_path / "haid.csv"
    pipeline.write_csv(records, path)
    content = path.read_text(encoding="utf-8-sig")
    assert "37.0" not in content
    assert "5.0" not in content
    assert "37" in content
    assert "5" in content


def test_write_csv_computes_etapa_camaron_per_record(tmp_path):
    records = [
        {
            "empresa": "Nicovita",
            "nombre_producto": "Nicovita Origin",
            "etapa": "larva",
            "tamano_pellet_mm": "0.3",
            "tipo_presentacion": "Extruido",
            "empaque_kg": "10,20",
            "proteina_pct": "45",
            "grasa_pct": 10.0,
            "fuente_url": "https://nicovita.com/productos/nicovita-origin-ecuador/",
            "fecha_extraccion": "2026-09-02",
        },
        {
            "empresa": "Nicovita",
            "nombre_producto": "Nicovita Classic AD",
            "etapa": "engorde",
            "tamano_pellet_mm": "2.0",
            "tipo_presentacion": "Pelletizado",
            "empaque_kg": "25",
            "proteina_pct": "35",
            "grasa_pct": 5.0,
            "fuente_url": "https://nicovita.com/productos/nicovita-classic-ad-ecuador/",
            "fecha_extraccion": "2026-09-02",
        },
    ]
    path = tmp_path / "nicovita.csv"
    pipeline.write_csv(records, path)
    import pandas as pd

    df = pd.read_csv(path, dtype=str, keep_default_na=False, na_values=[""])
    assert df.loc[0, "etapa_camaron"] == "Hatchery"
    assert df.loc[1, "etapa_camaron"] == "Grower"


def test_write_csv_computes_particula_min_max_per_record(tmp_path):
    records = [
        {
            "empresa": "Nicovita",
            "nombre_producto": "Nicovita Classic",
            "etapa": "precria",
            "tamano_pellet_mm": "0.5-1.0",
            "tipo_presentacion": "Pelletizado",
            "empaque_kg": "25",
            "proteina_pct": "35",
            "grasa_pct": 5.0,
            "fuente_url": "https://nicovita.com/productos/nicovita-classic-ecuador/",
            "fecha_extraccion": "2026-09-03",
        },
        {
            "empresa": "HAID",
            "nombre_producto": "HAID Speed",
            "etapa": "engorde",
            "tamano_pellet_mm": "2.0",
            "tipo_presentacion": "Pelletizado",
            "empaque_kg": "25",
            "proteina_pct": "37",
            "grasa_pct": 5.0,
            "fuente_url": "https://www.haid.com.ec/speed/",
            "fecha_extraccion": "2026-09-03",
        },
    ]
    path = tmp_path / "particula.csv"
    pipeline.write_csv(records, path)
    import pandas as pd

    df = pd.read_csv(path, dtype=str, keep_default_na=False, na_values=[""])
    assert df.loc[0, "particula_min_mm"] == "0.5"
    assert df.loc[0, "particula_max_mm"] == "1"
    # Sin rango: min y max deben ser el mismo numero, no uno de los dos None.
    assert df.loc[1, "particula_min_mm"] == "2"
    assert df.loc[1, "particula_max_mm"] == "2"


def test_write_csv_also_writes_xlsx_with_real_numeric_dtype(tmp_path):
    # Hallazgo del usuario 2026-09-03: un valor como "0.9" en el CSV se lee
    # como 9 al abrirlo en Excel con configuracion regional en espanol (el
    # punto se interpreta como separador de miles y se descarta). El .xlsx
    # evita esto guardando el numero real (float), no texto que Excel tenga
    # que reinterpretar.
    records = [
        {
            "empresa": "BioMar",
            "nombre_producto": "Exia Start",
            "etapa": "precria",
            "tamano_pellet_mm": "0.9-1.2",
            "tipo_presentacion": None,
            "empaque_kg": "10",
            "proteina_pct": "38",
            "grasa_pct": None,
            "fuente_url": "https://agrizon.com/en/products/exia-start-38-0-9-1-2-mm-10-kg-dieta-para-larvas",
            "fecha_extraccion": "2026-09-03",
        }
    ]
    path = tmp_path / "biomar.csv"
    pipeline.write_csv(records, path)
    xlsx_path = path.with_suffix(".xlsx")
    assert xlsx_path.exists()

    import pandas as pd

    df = pd.read_excel(xlsx_path)
    assert df.loc[0, "particula_min_mm"] == 0.9
    assert df.loc[0, "particula_max_mm"] == 1.2
    assert pd.api.types.is_float_dtype(df["particula_min_mm"])
    # proteina_pct sin decimales ("38") cae en int64, no float64 -- sigue
    # siendo un numero real (lo que importa), no texto que Excel deba
    # reinterpretar.
    assert pd.api.types.is_numeric_dtype(df["proteina_pct"])
