import pipeline


def test_format_value_strips_trailing_zero_from_whole_float():
    # Hallazgo del usuario 2026-09-02: proteina_pct de HAID y Aquaxcel
    # salia como float crudo (35.0) mientras tamano_pellet_mm/empaque_kg ya
    # se limpiaban con :g -- un visor de CSV con locale en español puede
    # leer el "." como separador de miles y mostrar 350.
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
            "etapa_engorde": True,
            "tamano_pellet_mm": "1.2",
            "tipo_presentacion": "Pelletizado",
            "empaque_kg": "25",
            "proteina_pct": 37.0,
            "fuente_url": "https://www.haid.com.ec/speed/",
            "fecha_extraccion": "2026-09-02",
        }
    ]
    path = tmp_path / "haid.csv"
    pipeline.write_csv(records, path)
    content = path.read_text(encoding="utf-8-sig")
    assert "37.0" not in content
    assert "37" in content


def test_write_csv_computes_etapa_skt_per_record(tmp_path):
    records = [
        {
            "empresa": "Nicovita",
            "nombre_producto": "Nicovita Origin",
            "etapa_larva": True,
            "tamano_pellet_mm": "0.3",
            "tipo_presentacion": "Extruido",
            "empaque_kg": "10,20",
            "proteina_pct": "45",
            "fuente_url": "https://nicovita.com/productos/nicovita-origin-ecuador/",
            "fecha_extraccion": "2026-09-02",
        },
        {
            "empresa": "Nicovita",
            "nombre_producto": "Nicovita Classic AD",
            "etapa_engorde": True,
            "tamano_pellet_mm": "2.0",
            "tipo_presentacion": "Pelletizado",
            "empaque_kg": "25",
            "proteina_pct": "35",
            "fuente_url": "https://nicovita.com/productos/nicovita-classic-ad-ecuador/",
            "fecha_extraccion": "2026-09-02",
        },
    ]
    path = tmp_path / "nicovita.csv"
    pipeline.write_csv(records, path)
    import pandas as pd

    df = pd.read_csv(path, dtype=str, keep_default_na=False, na_values=[""])
    assert df.loc[0, "etapa_skt"] == "Hatchery"
    assert df.loc[1, "etapa_skt"] == "Grower"


def test_write_csv_computes_particula_min_max_per_record(tmp_path):
    records = [
        {
            "empresa": "Nicovita",
            "nombre_producto": "Nicovita Classic",
            "etapa_precria": True,
            "tamano_pellet_mm": "0.5-1.0",
            "tipo_presentacion": "Pelletizado",
            "empaque_kg": "25",
            "proteina_pct": "35",
            "fuente_url": "https://nicovita.com/productos/nicovita-classic-ecuador/",
            "fecha_extraccion": "2026-09-03",
        },
        {
            "empresa": "HAID",
            "nombre_producto": "HAID Speed",
            "etapa_engorde": True,
            "tamano_pellet_mm": "2.0",
            "tipo_presentacion": "Pelletizado",
            "empaque_kg": "25",
            "proteina_pct": "37",
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
            "etapa_precria": True,
            "tamano_pellet_mm": "0.9-1.2",
            "tipo_presentacion": None,
            "empaque_kg": "10",
            "proteina_pct": "38",
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


def test_build_master_also_writes_one_master_per_pais(tmp_path, monkeypatch):
    import pandas as pd
    import schema

    monkeypatch.setattr(pipeline, "PROCESSED_DIR", tmp_path / "processed")
    monkeypatch.setattr(pipeline, "MASTER_PATH", tmp_path / "master.csv")
    # sin esto build_master pisaba el data/conflictos.csv real con uno vacio
    monkeypatch.setattr(pipeline, "CONFLICTOS_PATH", tmp_path / "conflictos.csv")
    monkeypatch.setattr(pipeline, "PRESENTACIONES_NUEVAS_PATH", tmp_path / "presentaciones_nuevas.csv")
    for pais in ("ecuador", "mexico"):
        rec = {c: None for c in schema.SCHEMA_COLUMNS}
        rec.update(pais=pais, empresa="Nicovita", nombre_producto=f"Nicovita {pais}")
        pipeline.write_csv([rec], pipeline.processed_path(pais, "nicovita"))
    pipeline.build_master()
    assert len(pd.read_csv(tmp_path / "master.csv")) == 2
    for pais in ("ecuador", "mexico"):
        df = pd.read_csv(tmp_path / "processed" / pais / f"master_{pais}.csv")
        assert list(df["pais"]) == [pais]


def test_netutil_pause_schedule_is_random_and_long_every_6_to_10(monkeypatch):
    import netutil

    slept = []
    monkeypatch.setattr(netutil, "ENABLED", True)
    monkeypatch.setattr(netutil.time, "sleep", slept.append)
    monkeypatch.delenv("SCRAPER_NO_PAUSE", raising=False)
    netutil._state.update(n=0, next_long=4)
    for _ in range(4):
        netutil.pause()
    assert all(0.5 <= s <= 2.5 for s in slept[:3])  # R6.1
    assert 5.0 <= slept[3] <= 12.0
    assert 6 <= netutil._state["next_long"] <= 10


def test_netutil_backoff_has_jitter_and_respects_retry_after():
    import netutil

    esperas = [netutil._backoff(0) for _ in range(50)]
    assert all(5.0 <= e <= 7.5 for e in esperas)
    assert len(set(esperas)) > 1
    assert all(60.0 <= netutil._backoff(0, 60) <= 90.0 for _ in range(50))


def test_netutil_blocked_response_raises_and_saves_page(tmp_path, monkeypatch):
    import netutil
    import pytest

    class Resp:
        url = "https://validate.perfdrive.com/?ssa=1"
        status_code = 200
        text = "<html>captcha</html>"
        headers = {}

    class Sess:
        def get(self, url, **kw):
            return Resp()

    monkeypatch.setattr(netutil, "BLOQUEOS_DIR", tmp_path)
    netutil.reset_blocked()
    with pytest.raises(netutil.BlockedError) as exc:
        netutil.get(Sess(), "https://nicovita.com/x")
    assert exc.value.saved.exists()
    assert netutil.blocked_events()[0]["captcha_url"].startswith("https://validate.perfdrive.com")


def test_netutil_pause_only_applies_to_paced_hosts(monkeypatch):
    import netutil

    slept = []
    monkeypatch.setattr(netutil, "ENABLED", True)
    monkeypatch.setattr(netutil.time, "sleep", slept.append)
    monkeypatch.delenv("SCRAPER_NO_PAUSE", raising=False)
    netutil.pause("https://agripac.com.ec/x")
    netutil.pause("https://vimifos.com/producto/xtrudix")
    assert slept == []
    netutil.pause("https://nicovita.com/categoria/camarones/")
    assert len(slept) == 1


def test_conflictos_por_pais_y_consolidado_sin_entrar_al_master(tmp_path, monkeypatch):
    import pipeline
    import pandas as pd
    import schema
    monkeypatch.setattr(pipeline, "PROCESSED_DIR", tmp_path / "processed")
    monkeypatch.setattr(pipeline, "MASTER_PATH", tmp_path / "master.csv")
    monkeypatch.setattr(pipeline, "CONFLICTOS_PATH", tmp_path / "conflictos.csv")
    monkeypatch.setattr(pipeline, "PRESENTACIONES_NUEVAS_PATH", tmp_path / "presentaciones_nuevas.csv")
    monkeypatch.setattr(pipeline.fuentes, "listar", lambda *a, **k: [("mexico", "apiaba")])
    record = schema.empty_record("Api-Aba")
    record.update(pais="mexico", nombre_producto="Dorado 35%", proteina_pct="35")
    schema.registrar_conflicto(record, "proteina_pct", "35", "nombre_comercial", [("40", "analisis"), ("35", "titulo")])
    pipeline.write_csv([record], pipeline.processed_path("mexico", "apiaba"))
    assert pipeline.write_conflictos([record], "mexico", "apiaba") == 1
    assert pipeline.write_conflictos([record], "mexico", "apiaba") == 1  # re-correr no duplica
    pipeline.build_master()
    conf = pd.read_csv(tmp_path / "conflictos.csv", dtype=str)
    assert len(conf) == 1 and conf.loc[0, "regla"] == "nombre_comercial"
    master = pd.read_csv(tmp_path / "master.csv", dtype=str)
    assert len(master) == 1 and "regla" not in master.columns


def test_write_presentaciones_nuevas_escribe_csv_del_master(tmp_path):
    from test_schema import _master_r34
    path = tmp_path / "presentaciones_nuevas.csv"
    pipeline.write_presentaciones_nuevas(_master_r34(), path)
    import pandas as pd
    df = pd.read_csv(path, dtype=str, encoding="utf-8-sig")
    assert df["valor"].tolist() == ["Hojuela", "Pelletizado"]


def test_write_presentaciones_nuevas_sin_valores_deja_solo_encabezado(tmp_path):
    from test_schema import _master_r34
    master = _master_r34()
    master = master[master["tipo_presentacion"].isin(["Pellet", "Líquido"])]
    path = tmp_path / "presentaciones_nuevas.csv"
    pipeline.write_presentaciones_nuevas(master, path)
    assert path.read_text(encoding="utf-8-sig").strip() == "pais,empresa,producto,valor,url"


def test_reportar_presentaciones_nuevas_resume_por_valor(tmp_path, capsys):
    from test_schema import _master_r34
    path = tmp_path / "presentaciones_nuevas.csv"
    pipeline.write_presentaciones_nuevas(_master_r34(), path)
    pipeline.reportar_presentaciones_nuevas(path)
    out = capsys.readouterr().out
    assert "Hojuela: 1" in out
    assert "Pelletizado: 1" in out
    assert str(path) in out


def test_reportar_presentaciones_nuevas_calla_si_no_hay(tmp_path, capsys):
    path = tmp_path / "presentaciones_nuevas.csv"
    path.write_text("pais,empresa,producto,valor,url\n", encoding="utf-8-sig")
    pipeline.reportar_presentaciones_nuevas(path)
    assert capsys.readouterr().out == ""


def test_write_csv_completa_etapas_booleanas(tmp_path):
    import pandas as pd

    records = [
        {"empresa": "Nicovita", "nombre_producto": "Nicovita Classic AD", "etapa_engorde": True,
         "etapa_precria": False, "tamano_pellet_mm": "2.5", "tipo_presentacion": "Pellet",
         "fuente_url": "https://nicovita.com/productos/nicovita-classic-ad-ecuador/"},
        {"empresa": "Cargill", "nombre_producto": "Sin etapa"},
    ]
    path = tmp_path / "nicovita.csv"
    pipeline.write_csv(records, path)
    df = pd.read_csv(path, dtype=str, keep_default_na=False, na_values=[""])
    assert df.loc[0, "etapa_engorde"] == "True"
    assert df.loc[0, "etapa_precria"] == "False"
    assert df.loc[1, ["etapa_engorde", "etapa_larva"]].isna().all()


def test_build_master_deriva_etapas_de_csv_viejos(tmp_path, monkeypatch):
    import pandas as pd
    import schema

    monkeypatch.setattr(pipeline, "PROCESSED_DIR", tmp_path / "processed")
    monkeypatch.setattr(pipeline, "MASTER_PATH", tmp_path / "master.csv")
    monkeypatch.setattr(pipeline, "CONFLICTOS_PATH", tmp_path / "conflictos.csv")
    monkeypatch.setattr(pipeline, "PRESENTACIONES_NUEVAS_PATH", tmp_path / "presentaciones_nuevas.csv")
    # CSV de Honduras escrito antes de R3.5: sin columnas etapa_*
    viejo = pipeline.processed_path("honduras", "nicovita")
    viejo.parent.mkdir(parents=True)
    fila = {c: None for c in schema.SCHEMA_COLUMNS if c not in schema.ETAPA_COLUMNS}
    fila.update(pais="honduras", empresa="Nicovita", nombre_producto="Nicovita Classic Engorde",
                etapa_competidor="engorde")
    pd.DataFrame([fila]).to_csv(viejo, index=False)
    pipeline.build_master()
    master = pd.read_csv(tmp_path / "master.csv", dtype=str)
    assert master.loc[0, "etapa_engorde"] == "True" and master.loc[0, "etapa_larva"] == "False"


def test_write_csv_respeta_etapas_del_parser(tmp_path):
    # R4.2 REQ-2: un parser migrado (_etapas_detectadas) manda sobre el puente,
    # aunque sus etapas queden vacias.
    import pandas as pd
    import schema

    marcadas = {"empresa": "Nicovita", "nombre_producto": "Nicovita Classic", "etapa_engorde": True,
                "_etapas_detectadas": True, **schema.columnas_etapa({"post_larva", "engorde"})}
    vacias = {"empresa": "Nicovita", "nombre_producto": "Sin texto", "etapa_engorde": True,
              "_etapas_detectadas": True, **schema.columnas_etapa(set())}
    path = tmp_path / "nicovita.csv"
    pipeline.write_csv([marcadas, vacias], path)
    df = pd.read_csv(path, dtype=str, keep_default_na=False, na_values=[""])
    assert df.loc[0, "etapa_post_larva"] == "True"
    assert df.loc[0, "etapa_engorde"] == "True"
    assert df.loc[0, "etapa_precria"] == "False"
    assert df.loc[1, schema.ETAPA_COLUMNS].isna().all()
