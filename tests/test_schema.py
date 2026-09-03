import schema


def test_normalize_etapa_maps_known_labels():
    assert schema.normalize_etapa("Inicio") == "precria"
    assert schema.normalize_etapa("TRANSICIÓN") == "post_transferencia"
    assert schema.normalize_etapa("Crecimiento") == "engorde"
    assert schema.normalize_etapa("De Alevinaje") == "post_transferencia"
    assert schema.normalize_etapa("Para Hatchery") == "larva"


def test_normalize_etapa_no_match_returns_none():
    assert schema.normalize_etapa(None) is None
    assert schema.normalize_etapa("") is None
    assert schema.normalize_etapa("texto sin relacion al ciclo del camaron") is None


def test_normalize_etapa_no_longer_maps_salud_related_terms():
    # "salud" se saco de ETAPA_VALUES/_ETAPA_RULES 2026-09-02 -- un producto
    # con funcion terapeutica no tiene una etapa de ciclo de vida propia
    # (ver producto_salud en cada parser). Sin otro marcador de etapa real,
    # estos terminos ya no deben resolver a nada.
    assert schema.normalize_etapa("Fitness") is None
    assert schema.normalize_etapa("Tratamiento") is None
    assert "salud" not in schema.ETAPA_VALUES


def test_detect_tecnologia_prefers_first_mention_in_text():
    # Caso real: ficha HAID "Speed Pellet" -- el encabezado dice
    # "PELLETIZADO" (coincide con el nombre del producto) pero el parrafo
    # de descripcion dice, por error de la propia ficha, "elaborado por
    # proceso de extruido". La primera mencion en el texto (el encabezado)
    # debe ganar. Ver MEMORY.md.
    text = (
        "SPEED PELLET\nALIMENTO BALANCEADO PELLETIZADO PARA CAMARON\n"
        "Descripcion del producto\nAlimento balanceado... elaborado por "
        "proceso de extruido."
    )
    assert schema.detect_tecnologia(text) == "Pelletizado"


def test_detect_tecnologia_tolerates_single_l_spelling():
    # Nicovita a veces escribe "peletizada" con una sola L (no "pelletizada").
    assert schema.detect_tecnologia("Dieta balanceada peletizada para camaron") == "Pelletizado"


def test_detect_tecnologia_extruido():
    assert schema.detect_tecnologia("Alimento balanceado extruido para camaron") == "Extruido"


def test_detect_tecnologia_no_mention_returns_none():
    assert schema.detect_tecnologia("Alimento balanceado para camaron") is None
    assert schema.detect_tecnologia(None) is None
    assert schema.detect_tecnologia("") is None


def test_empty_record_has_all_columns_none_except_empresa():
    record = schema.empty_record("Nicovita")
    assert record["empresa"] == "Nicovita"
    assert all(v is None for k, v in record.items() if k != "empresa")
    assert set(record.keys()) == set(schema.SCHEMA_COLUMNS)


def test_etapa_from_tamano_below_1_6mm_is_precria():
    assert schema.etapa_from_tamano("0.8", "Extruido") == "precria"
    assert schema.etapa_from_tamano("1.2", "Pelletizado") == "precria"


def test_etapa_from_tamano_handles_range_string():
    # Caso real Nicovita Classic: la ficha publica "0.5-1.0" como un solo
    # calibre comercial, no dos numeros sueltos.
    assert schema.etapa_from_tamano("0.5-1.0", "Pelletizado") == "precria"


def test_etapa_from_tamano_exactly_1_6mm_stays_none():
    # Limite real (MEMORY.md / conversacion con el usuario): la definicion
    # de negocio da 1.6mm como techo de Nursery Y como tamano tipico de Pre
    # Grower a la vez -- no hay Pre Grower en el esquema actual, y elegir
    # Nursery o Grower para este caso puntual seria inventar dato sin que
    # el usuario lo haya confirmado.
    assert schema.etapa_from_tamano("1.6", "Pelletizado") is None
    assert schema.etapa_from_tamano("1.6", "Extruido") is None


def test_etapa_from_tamano_gap_between_1_6_and_grower_threshold_stays_none():
    assert schema.etapa_from_tamano("1.7", "Pelletizado") is None


def test_etapa_from_tamano_grower_threshold_depends_on_tipo_presentacion():
    # Grower arranca en 1.8mm para Pelletizado pero 1.9mm para Extruido.
    assert schema.etapa_from_tamano("1.8", "Pelletizado") == "engorde"
    assert schema.etapa_from_tamano("1.8", "Extruido") is None
    assert schema.etapa_from_tamano("1.9", "Extruido") == "engorde"
    assert schema.etapa_from_tamano("2.5", "Pelletizado") == "engorde"


def test_etapa_from_tamano_unknown_tipo_presentacion_stays_none_at_grower_size():
    assert schema.etapa_from_tamano("2.5", None) is None


def test_etapa_from_tamano_empty_input_stays_none():
    assert schema.etapa_from_tamano(None, "Pelletizado") is None
    assert schema.etapa_from_tamano("", "Pelletizado") is None


def test_etapa_camaron_larva_overrides_to_hatchery_regardless_of_tamano():
    # Caso real: Nicovita Origin es "larva" con tamanos 0.3-0.8mm, que por
    # tamano solo hubieran caido en Nursery -- la jefa define Hatchery por
    # tipo de producto (laboratorio larvario), no por banda de mm.
    assert schema.etapa_camaron_from_row("larva", "0.3", "Extruido") == "Hatchery"
    assert schema.etapa_camaron_from_row("larva", None, None) == "Hatchery"


def test_etapa_camaron_below_1_6mm_is_nursery():
    assert schema.etapa_camaron_from_row("precria", "0.8", "Extruido") == "Nursery"
    assert schema.etapa_camaron_from_row(None, "1.2", "Pelletizado") == "Nursery"


def test_etapa_camaron_handles_range_string():
    assert schema.etapa_camaron_from_row("precria", "0.5-1.0", "Pelletizado") == "Nursery"


def test_etapa_camaron_exactly_1_6mm_is_pre_grower():
    # A diferencia de etapa_from_tamano (que deja este caso en None porque
    # reusa las 6 categorias viejas), aca la columna es dedicada a los 4
    # terminos de la jefa y ella asocio 1.6mm especificamente a Pre Grower.
    assert schema.etapa_camaron_from_row("engorde", "1.6", "Pelletizado") == "Pre Grower"
    assert schema.etapa_camaron_from_row(None, "1.6", "Extruido") == "Pre Grower"


def test_etapa_camaron_grower_threshold_depends_on_tipo_presentacion():
    assert schema.etapa_camaron_from_row("engorde", "1.8", "Pelletizado") == "Grower"
    assert schema.etapa_camaron_from_row("engorde", "1.8", "Extruido") is None
    assert schema.etapa_camaron_from_row("engorde", "1.9", "Extruido") == "Grower"
    assert schema.etapa_camaron_from_row("engorde", "2.5", "Pelletizado") == "Grower"


def test_etapa_camaron_gap_between_1_6_and_grower_threshold_stays_none():
    assert schema.etapa_camaron_from_row("engorde", "1.7", "Pelletizado") is None


def test_etapa_camaron_unknown_tipo_presentacion_at_grower_size_stays_none():
    assert schema.etapa_camaron_from_row("engorde", "2.5", None) is None


def test_etapa_camaron_empty_tamano_stays_none():
    assert schema.etapa_camaron_from_row("engorde", None, "Pelletizado") is None
    assert schema.etapa_camaron_from_row("salud", "", "Pelletizado") is None


def test_detect_producto_salud_true_for_disease_marker():
    assert schema.detect_producto_salud("tratamiento contra Vibrio spp") is True
    # Caso real Aquaxcel Adapt Shock (usuario 2026-09-02): "vibriosis" debe
    # matchear via la raiz "vibrio", igual que "Vibrio spp" en Nicovita/HAID.
    assert schema.detect_producto_salud("combatir eventos bacterianos como la vibriosis") is True


def test_detect_producto_salud_true_for_profilactic_marker():
    # Caso real Agripac (2026-09-03): la "Linea Profilactica" (Ultra,
    # Ultrapro, Premium Profilactico) no menciona vibrio/tratamiento/
    # antibacterian, pero si describe un reclamo especifico de prevencion
    # ("resistencia a problemas de bacterias, virus y parasitos") -- mismo
    # nivel de especificidad que "tratamiento anti-Vibrio", no generico como
    # "promover la salud" (ver test de abajo).
    text = (
        "Linea Profilactica: disenada para el fortalecimiento del sistema "
        "inmune del camaron logrando una mejor resistencia a problemas de "
        "bacterias, virus y parasitos"
    )
    assert schema.detect_producto_salud(text) is True
    assert schema.detect_producto_salud("Feedpac 35% Premium Profilactico") is True


def test_detect_producto_salud_false_when_text_present_without_marker():
    assert schema.detect_producto_salud("alimento para camaron desde post larva") is False
    # Mencion generica de "salud" en marketing (ej. Aquaxcel Maxima: "promover
    # la salud del camaron") NO es lo mismo que un reclamo especifico de
    # tratamiento -- la palabra "salud" sola nunca estuvo en este regex.
    assert schema.detect_producto_salud("ingredientes para promover la salud del camaron") is False


def test_detect_producto_salud_none_when_no_text():
    assert schema.detect_producto_salud("") is None
    assert schema.detect_producto_salud(None) is None


def test_parse_particula_range_single_value_sets_min_equal_to_max():
    # Caso mas comun: un solo calibre, sin rango que partir -- min y max
    # deben ser el mismo numero para que la fila siga siendo promediable
    # junto con las que si son rango.
    assert schema.parse_particula_range("2.5") == (2.5, 2.5)
    assert schema.parse_particula_range("2") == (2.0, 2.0)


def test_parse_particula_range_splits_range_string():
    # Caso real Nicovita Classic: "0.5-1.0" es un solo calibre comercial
    # publicado como rango, no dos numeros sueltos.
    assert schema.parse_particula_range("0.5-1.0") == (0.5, 1.0)
    assert schema.parse_particula_range("0.25-0.375") == (0.25, 0.375)


def test_parse_particula_range_empty_input_returns_none_pair():
    assert schema.parse_particula_range(None) == (None, None)
    assert schema.parse_particula_range("") == (None, None)


def test_schema_no_longer_includes_unpublished_fields():
    # energia_kcal_kg y velocidad_hundimiento se sacaron del esquema
    # (2026-09-01); fibra_pct/ceniza_pct/humedad_pct/estabilidad_agua_min y
    # los claims cualitativos se sacaron despues (2026-09-02) a pedido del
    # usuario -- el esquema se redujo a los atributos de negocio priorizados
    # (competidor/marca vive en nombre_producto, etapa, tecnologia, tamano,
    # empaque, proteina, grasa).
    assert "energia_kcal_kg" not in schema.SCHEMA_COLUMNS
    assert "velocidad_hundimiento" not in schema.SCHEMA_COLUMNS
    assert "estabilidad_agua_min" not in schema.SCHEMA_COLUMNS
    assert "fibra_pct" not in schema.SCHEMA_COLUMNS
    assert "ceniza_pct" not in schema.SCHEMA_COLUMNS
    assert "humedad_pct" not in schema.SCHEMA_COLUMNS
    assert "claims_texto_libre" not in schema.SCHEMA_COLUMNS
