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
    # (ver es_producto_de_salud en cada parser). Sin otro marcador de etapa real,
    # estos terminos ya no deben resolver a nada.
    assert schema.normalize_etapa("Fitness") is None
    assert schema.normalize_etapa("Tratamiento") is None
    assert "salud" not in schema.ETAPA_VALUES


def test_detect_tecnologia_prefers_first_mention_in_text():
    # Caso real: ficha HAID "Speed Pellet" -- el encabezado dice
    # "PELLETIZADO" (coincide con el nombre del producto) pero el parrafo
    # de descripcion dice, por error de la propia ficha, "elaborado por
    # proceso de extruido". La primera mencion en el texto (el encabezado)
    # debe ganar. Ver docs/historico/MEMORY.md.
    text = (
        "SPEED PELLET\nALIMENTO BALANCEADO PELLETIZADO PARA CAMARON\n"
        "Descripcion del producto\nAlimento balanceado... elaborado por "
        "proceso de extruido."
    )
    assert schema.detect_tecnologia(text) == "Pellet"


def test_detect_tecnologia_tolerates_single_l_spelling():
    # Nicovita a veces escribe "peletizada" con una sola L (no "pelletizada").
    assert schema.detect_tecnologia("Dieta balanceada peletizada para camaron") == "Pellet"


def test_detect_tecnologia_extruido():
    assert schema.detect_tecnologia("Alimento balanceado extruido para camaron") == "Extruido"


def test_detect_tecnologia_no_mention_returns_none():
    assert schema.detect_tecnologia("Alimento balanceado para camaron") is None
    assert schema.detect_tecnologia(None) is None
    assert schema.detect_tecnologia("") is None


def test_detect_tecnologia_microextruido_resolves_to_extruido():
    # "Microextruido" contiene "extrui" y resuelve a "Extruido". Desde R3.3
    # Agripac (MeM) ya no pasa por aca: usa normalize_presentacion y guarda
    # "Microextruido", que es valor oficial.
    assert schema.detect_tecnologia("Tipo Microextruido") == "Extruido"


def test_detect_tecnologia_polvo():
    # Caso real: Artemia Cysts (Agripac, division Larvicultura). Agregado
    # 2026-09-07 a pedido del usuario -- antes quedaba en None junto con
    # "Microparticulado"/"Liquido" (3ra categoria fuera de la dicotomia).
    assert schema.detect_tecnologia("Tipo Polvo") == "Polvo"


def test_detect_tecnologia_microparticulado():
    # Caso real: Mpex (Agripac, division Larvicultura).
    assert schema.detect_tecnologia("Tipo Microparticulado") == "Microparticulado"


def test_detect_tecnologia_liquido():
    # Caso real: Royal Pepper Protein (Agripac, division Larvicultura) --
    # su pestana "Tipo" dice literalmente "Liquidos" (con tilde, plural).
    assert schema.detect_tecnologia("Tipo Líquidos") == "Líquido"
    assert schema.detect_tecnologia("Tipo Liquido") == "Líquido"


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
    # Limite real (docs/historico/MEMORY.md / conversacion con el usuario): la definicion
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


def test_etapa_skt_larva_overrides_to_hatchery_regardless_of_tamano():
    # REQ-4. Caso real: Nicovita Origin es "larva" con tamanos 0.3-0.8mm, que
    # por tamano hubieran caido en Nursery (decision del usuario 2026-10-29).
    assert schema.etapa_skt_from_row({"larva"}, "0.3-0.8") == "Hatchery"
    assert schema.etapa_skt_from_row({"larva"}, None) == "Hatchery"


def test_etapa_skt_es_larvicultura_overrides_to_hatchery_regardless_of_tamano():
    # REQ-4. Toda la division Larvicultura de Agripac es Hatchery, aunque su
    # etapa no sea "larva" (ej. Mpex, "PL1 a PL6") y su tamano sea Nursery.
    assert schema.etapa_skt_from_row({"precria"}, "0.3", es_larvicultura=True) == "Hatchery"
    assert schema.etapa_skt_from_row(set(), None, es_larvicultura=True) == "Hatchery"
    assert schema.etapa_skt_from_row({"engorde"}, "2.5", es_larvicultura=True) == "Hatchery"


def test_etapa_skt_cortes_por_tamano_sin_importar_presentacion():
    # REQ-1. El tamano manda sobre la etapa del competidor.
    assert schema.etapa_skt_from_row({"engorde"}, "0.8") == "Nursery"
    assert schema.etapa_skt_from_row(set(), "1.2") == "Nursery"
    assert schema.etapa_skt_from_row({"engorde"}, "1.6") == "Pre Grower"
    assert schema.etapa_skt_from_row({"precria"}, "1.7") == "Grower"
    assert schema.etapa_skt_from_row(set(), "1.8") == "Grower"
    assert schema.etapa_skt_from_row(set(), "2.5") == "Grower"


def test_etapa_skt_rango_usa_el_minimo():
    # REQ-2
    assert schema.etapa_skt_from_row({"engorde"}, "1.4-2.0") == "Nursery"
    assert schema.etapa_skt_from_row({"engorde"}, "2.0-1.4") == "Nursery"
    assert schema.etapa_skt_from_row(set(), "1.6 - 2.4") == "Pre Grower"
    assert schema.etapa_skt_from_row(set(), "1.8-2.2") == "Grower"


def test_etapa_skt_sin_tamano_usa_etapa_del_competidor():
    # REQ-3 (decision del usuario 2026-10-29)
    assert schema.etapa_skt_from_row({"precria"}, None) == "Nursery"
    assert schema.etapa_skt_from_row({"post_transferencia"}, "") == "Pre Grower"
    assert schema.etapa_skt_from_row({"engorde"}, None) == "Grower"
    assert schema.etapa_skt_from_row({"engorde"}, "s/d") == "Grower"


def test_etapa_skt_sin_tamano_ni_etapa_conocida_queda_vacio():
    # REQ-3
    assert schema.etapa_skt_from_row({"reproductores"}, None) is None
    assert schema.etapa_skt_from_row({"salud"}, "") is None
    assert schema.etapa_skt_from_row(set(), None) is None


def test_detect_es_producto_de_salud_true_for_disease_marker():
    assert schema.detect_es_producto_de_salud("tratamiento contra Vibrio spp") is True
    # Caso real Aquaxcel Adapt Shock (usuario 2026-09-02): "vibriosis" debe
    # matchear via la raiz "vibrio", igual que "Vibrio spp" en Nicovita/HAID.
    assert schema.detect_es_producto_de_salud("combatir eventos bacterianos como la vibriosis") is True


def test_detect_es_producto_de_salud_true_for_profilactic_marker():
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
    assert schema.detect_es_producto_de_salud(text) is True
    assert schema.detect_es_producto_de_salud("Feedpac 35% Premium Profilactico") is True


def test_detect_es_producto_de_salud_false_when_text_present_without_marker():
    assert schema.detect_es_producto_de_salud("alimento para camaron desde post larva") is False
    # Mencion generica de "salud" en marketing (ej. Aquaxcel Maxima: "promover
    # la salud del camaron") NO es lo mismo que un reclamo especifico de
    # tratamiento -- la palabra "salud" sola nunca estuvo en este regex.
    assert schema.detect_es_producto_de_salud("ingredientes para promover la salud del camaron") is False


def test_detect_es_producto_de_salud_none_when_no_text():
    assert schema.detect_es_producto_de_salud("") is None
    assert schema.detect_es_producto_de_salud(None) is None


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
    # usuario; grasa_pct se saco el 2026-09-15 (tambien a pedido del
    # usuario) -- el esquema se redujo a los atributos de negocio
    # priorizados (competidor/marca vive en nombre_producto, etapa,
    # tecnologia, tamano, empaque, proteina).
    assert "energia_kcal_kg" not in schema.SCHEMA_COLUMNS
    assert "velocidad_hundimiento" not in schema.SCHEMA_COLUMNS
    assert "estabilidad_agua_min" not in schema.SCHEMA_COLUMNS
    assert "fibra_pct" not in schema.SCHEMA_COLUMNS
    assert "ceniza_pct" not in schema.SCHEMA_COLUMNS
    assert "humedad_pct" not in schema.SCHEMA_COLUMNS
    assert "claims_texto_libre" not in schema.SCHEMA_COLUMNS
    assert "grasa_pct" not in schema.SCHEMA_COLUMNS


def test_schema_renames_etapa_and_clasificacion_camaron():
    # 2026-09-15, a pedido del usuario: "etapa" (la etapa tal como la
    # publica el propio competidor) paso a llamarse "etapa_competidor", y
    # "clasificacion_camaron" (la clasificacion de 4 casillas que definio la
    # jefa del usuario) paso a llamarse "etapa_skt" -- para que el par de
    # columnas quede claramente distinguible por sufijo (_competidor vs.
    # _skt) en vez de dos nombres sin relacion aparente entre si.
    assert "etapa" not in schema.SCHEMA_COLUMNS
    assert "clasificacion_camaron" not in schema.SCHEMA_COLUMNS
    assert "etapa_competidor" not in schema.SCHEMA_COLUMNS  # R4.10: quitada
    assert "etapa_skt" in schema.SCHEMA_COLUMNS


def test_pais_is_first_column_and_values_are_defined():
    assert schema.SCHEMA_COLUMNS[0] == "pais"
    assert set(schema.PAIS_VALUES) == {"ecuador", "honduras", "nicaragua", "panama", "mexico"}


def test_resolver_campo_aplica_reglas_en_orden():
    reglas = [schema.regla_coincidencia, schema.regla_preferir("titulo", "nombre_comercial")]
    assert schema.resolver_campo([], reglas) == (None, None)
    assert schema.resolver_campo([("35", "titulo")], reglas) == ("35", "unico")
    assert schema.resolver_campo([("35", "titulo"), ("35,0", "tabla")], reglas) == ("35", "unico")
    assert schema.resolver_campo([("40", "analisis"), ("35", "titulo"), ("40", "tabla")], reglas) == ("40", "coincidencia")
    assert schema.resolver_campo([("40", "analisis"), ("35", "titulo")], reglas) == ("35", "nombre_comercial")
    assert schema.resolver_campo([("40", "analisis"), ("35", "otro")], reglas) == (None, "sin_regla")


def test_conflictos_de_arma_filas_con_columnas_fijas():
    record = schema.empty_record("Api-Aba")
    record.update(pais="mexico", nombre_producto="Dorado 35%", fuente_url="u", fecha_extraccion="2026-10-19")
    schema.registrar_conflicto(record, "proteina_pct", "35", "nombre_comercial", [("40", "analisis"), ("35", "titulo")])
    (fila,) = schema.conflictos_de([record])
    assert list(fila) == schema.CONFLICTO_COLUMNS
    assert fila["candidatos"] == "40 (analisis) | 35 (titulo)" and fila["empresa"] == "Api-Aba"


# --- R3.2: normalize_presentacion ---

def test_tipo_presentacion_oficial_es_la_lista_de_tech_stack():
    assert schema.TIPO_PRESENTACION_OFICIAL == {
        "Extruido", "Granulado", "Líquido", "Microencapsulado", "Microextruido",
        "Microparticulado", "Nauplios de artemia", "Otro", "Pellet", "Polvo",
        "Quistes de artemia", "Suspensión",
    }


def test_normalize_presentacion_valor_oficial_con_grafia_oficial():
    # Valores reales del master.csv actual
    assert schema.normalize_presentacion("Extruido") == "Extruido"
    assert schema.normalize_presentacion("Microparticulado") == "Microparticulado"
    assert schema.normalize_presentacion("líquido ") == "Líquido"
    assert schema.normalize_presentacion("LIQUIDO") == "Líquido"
    assert schema.normalize_presentacion("quistes de ARTEMIA") == "Quistes de artemia"
    assert schema.normalize_presentacion("Suspension") == "Suspensión"


def test_normalize_presentacion_pelletizado_pasa_a_pellet():
    assert schema.normalize_presentacion("Pelletizado") == "Pellet"
    assert schema.normalize_presentacion("PELLETIZADA") == "Pellet"
    assert schema.normalize_presentacion("Peletizado") == "Pellet"
    assert schema.normalize_presentacion("pellet") == "Pellet"


def test_normalize_presentacion_desconocido_se_conserva():
    assert schema.normalize_presentacion("Microgranulado") == "Microgranulado"
    assert schema.normalize_presentacion("  Crumble ") == "Crumble"


def test_normalize_presentacion_vacio_es_none():
    assert schema.normalize_presentacion(None) is None
    assert schema.normalize_presentacion("") is None
    assert schema.normalize_presentacion("   ") is None


# --- R3.3: los parsers usan normalize_presentacion ---

def test_detect_tecnologia_devuelve_la_lista_oficial():
    # REQ-1: textos reales (HAID, Agrizon, Agripac) -> grafia oficial
    assert schema.detect_tecnologia("ALIMENTO BALANCEADO PELLETIZADO PARA CAMARON") == "Pellet"
    assert schema.detect_tecnologia("Exia Perform 35% Pelletized 2.0 mm") == "Pellet"
    assert schema.detect_tecnologia("Larviva Extrusado") == "Extruido"
    assert schema.detect_tecnologia("Tipo Polvo") == "Polvo"
    assert schema.detect_tecnologia("Tipo Micro particulado") == "Microparticulado"
    assert schema.detect_tecnologia("Tipo Líquidos") == "Líquido"
    for valor in ("Pellet", "Extruido", "Polvo", "Microparticulado", "Líquido"):
        assert valor in schema.TIPO_PRESENTACION_OFICIAL


def test_umbral_grower_de_pellet_acepta_pellet_y_pelletizado():
    # REQ-2: la grafia nueva no rompe el umbral de 1.8 mm (etapa_skt ya no
    # depende de tipo_presentacion desde R3.6)
    for tipo in ("Pellet", "Pelletizado"):
        assert schema.etapa_from_tamano("1.8", tipo) == "engorde"


def test_normalize_presentacion_alias_de_agripac():
    # REQ-3: grafias reales de la pestana "Tipo" de Agripac
    assert schema.normalize_presentacion("Micro particulado") == "Microparticulado"
    assert schema.normalize_presentacion("Líquidos") == "Líquido"


def _master_r34():
    # Filas reales del master (2026-10-29): Agrizon Microgranulado y Honduras sin regenerar.
    import pandas as pd
    return pd.DataFrame([
        {"pais": "ecuador", "empresa": "BioMar", "nombre_producto": "Exia Prime",
         "tipo_presentacion": "Microgranulado",
         "fuente_url": "https://agrizon.com/en/products/exia-prime-35-precria-0-6-0-9-mm-25-kg"},
        {"pais": "ecuador", "empresa": "Nicovita", "nombre_producto": "Nicovita Classic AD",
         "tipo_presentacion": "Pellet",
         "fuente_url": "https://nicovita.com/productos/nicovita-classic-ad-ecuador/"},
        {"pais": "ecuador", "empresa": "Agripac", "nombre_producto": "Royal Pepper Protein",
         "tipo_presentacion": "Líquido",
         "fuente_url": "https://agripac.com.ec/productos/royal-pepper-protein/"},
        {"pais": "honduras", "empresa": "Nicovita", "nombre_producto": "Nicovita Classic Engorde",
         "tipo_presentacion": "Pelletizado",
         "fuente_url": "https://nicovita.com/productos/nicovita-classic-engorde-honduras/"},
        {"pais": "mexico", "empresa": "Vimifos", "nombre_producto": "Sin tipo",
         "tipo_presentacion": None, "fuente_url": "https://example.invalid/"},
    ])


def test_presentaciones_nuevas_solo_valores_fuera_de_la_lista_oficial():
    nuevas = schema.presentaciones_nuevas(_master_r34())
    assert list(nuevas.columns) == ["pais", "empresa", "producto", "valor", "url"]
    assert nuevas.to_dict("records") == [
        {"pais": "ecuador", "empresa": "BioMar", "producto": "Exia Prime", "valor": "Microgranulado",
         "url": "https://agrizon.com/en/products/exia-prime-35-precria-0-6-0-9-mm-25-kg"},
        {"pais": "honduras", "empresa": "Nicovita", "producto": "Nicovita Classic Engorde",
         "valor": "Pelletizado",
         "url": "https://nicovita.com/productos/nicovita-classic-engorde-honduras/"},
    ]


# --- R3.5: etapa_* booleanas desde etapa_competidor ------------------------


def test_etapas_desde_competidor_marca_una_true_y_las_demas_false():
    # Nicovita Classic Precria (master Ecuador): etapa_competidor = precria
    etapas = schema.etapas_desde_competidor("precria")
    assert etapas == {
        "etapa_reproductores": False,
        "etapa_larva": False,
        "etapa_post_larva": False,
        "etapa_precria": True,
        "etapa_post_transferencia": False,
        "etapa_engorde": False,
    }
    assert schema.etapas_desde_competidor("post_transferencia")["etapa_post_transferencia"] is True


def test_etapas_desde_competidor_vacio_deja_las_cinco_vacias():
    for etapa in (None, "", "salud"):
        assert schema.etapas_desde_competidor(etapa) == {c: None for c in schema.ETAPA_COLUMNS}


def test_schema_columns_incluye_etapas_despues_de_salud():
    i = schema.SCHEMA_COLUMNS.index("es_producto_de_salud")
    assert schema.SCHEMA_COLUMNS[i + 1:i + 1 + len(schema.ETAPA_COLUMNS)] == schema.ETAPA_COLUMNS
    assert "etapa_competidor" not in schema.SCHEMA_COLUMNS  # R4.10


# --- R4.1: detectar_etapas y etapa_post_larva -------------------------------
# Frases reales de las fuentes (tests/fixtures/ y la ficha de Nicovita Terap).


def test_req1_etapa_post_larva_entre_larva_y_precria():
    cols = schema.ETAPA_COLUMNS
    assert cols.index("etapa_post_larva") == cols.index("etapa_larva") + 1
    assert cols.index("etapa_precria") == cols.index("etapa_post_larva") + 1
    assert "etapa_post_larva" in schema.SCHEMA_COLUMNS
    assert schema.etapas_desde_competidor("larva")["etapa_post_larva"] is False
    assert schema.etapas_desde_competidor(None)["etapa_post_larva"] is None


def test_req2_detectar_etapas_devuelve_todas_las_explicitas():
    # Aquaxcel Mexico (listing): post-larva y precrias en la misma ficha
    texto = ("Alimento completo con 45% de proteína para la etapa de post-larva en sistemas "
             "semi-intensivos y en raceways o precrías hasta los 0.20g de peso vivo.")
    assert schema.detectar_etapas(texto) == {"post_larva", "precria"}
    assert schema.detectar_etapas("Reproductores / maduración") == {"reproductores"}
    assert schema.detectar_etapas(None) == set()
    assert schema.detectar_etapas("") == set()
    assert set().union(*(schema.detectar_etapas(e) for e in ("larva", "engorde"))) <= set(schema.ETAPAS)


def test_req3_post_larva_no_es_larva():
    # Nutrimar: "para post larvas hasta 1.0g"; Api-Aba: "fase postlarval hasta 3-4 g"
    assert schema.detectar_etapas(
        "Alimento balanceado extruido de alta densidad nutricional para post larvas hasta 1.0g de peso vivo."
    ) == {"post_larva"}
    assert schema.detectar_etapas(
        "diseñado para camarón en fase postlarval hasta 3–4 g de peso.") == {"post_larva"}
    assert schema.detectar_etapas("Formulado para camarón en etapa de postlarva") == {"post_larva"}
    assert schema.detectar_etapas("Nicovita Origin PL") == {"post_larva"}
    assert schema.detectar_etapas("Alimento para larvas en hatchery, mysis y zoea") == {"larva"}


def test_req4_palabras_genericas_no_marcan_etapa():
    # Api-Aba: "Favorece el crecimiento rapido"
    assert schema.detectar_etapas(
        "Favorece el crecimiento rápido, la sobrevivencia y el desarrollo inmunológico") == set()
    assert schema.detectar_etapas("Ideal para el inicio del ciclo") == set()


def test_req5_rango_marca_extremos_e_intermedias():
    # Nicovita Terap: "post larva hasta tamaño de mercado"
    assert schema.detectar_etapas("Desde post larva hasta tamaño de mercado") == {
        "post_larva", "precria", "post_transferencia", "engorde"}
    # Nicovita Classic/Katal base: "post-larva a mercado"
    assert schema.detectar_etapas("cubre post-larva a mercado") == {
        "post_larva", "precria", "post_transferencia", "engorde"}
    # Nutrimar: transicion hacia engorde
    assert schema.detectar_etapas(
        "durante la etapa de transición hacia la fase de engorde hasta los 12g de peso vivo."
    ) == {"post_transferencia", "engorde"}
    assert schema.detectar_etapas("desde precría hasta engorde") == {
        "precria", "post_transferencia", "engorde"}
    # Sin conector de rango, solo las mencionadas
    assert schema.detectar_etapas("Larva y engorde") == {"larva", "engorde"}
    # reproductores nunca se rellena
    assert schema.detectar_etapas("reproductores hasta engorde") == {"reproductores", "engorde"}


def test_req6_columnas_etapa():
    cols = schema.columnas_etapa({"precria", "engorde"})
    assert set(cols) == set(schema.ETAPA_COLUMNS)
    assert cols["etapa_precria"] is True and cols["etapa_engorde"] is True
    assert cols["etapa_larva"] is False and cols["etapa_post_larva"] is False
    assert schema.columnas_etapa(set()) == {c: None for c in schema.ETAPA_COLUMNS}


def test_req7_respaldo_skt_post_larva_es_nursery():
    assert schema.etapa_skt_from_row({"post_larva"}, None) == "Nursery"


# --- R4.2: reglas nuevas de detectar_etapas (fichas de Nicovita) -----------

def test_r42_req3_cosecha_es_engorde():
    # Nicovita Katal AD (PDF): "desde 1 gramo de peso vivo hasta tamaño de cosecha"
    assert schema.detectar_etapas(
        "desde 1 gramo de peso vivo hasta tamaño de cosecha.") == {"engorde"}
    # Nicovita Finalis Honduras (web): "hasta peso de cosecha"
    assert schema.detectar_etapas("desde los 3.0 gramos de peso hasta peso de cosecha") == {"engorde"}
    # Nicovita Finalis Proterra (web): "desde los 3 gramos hasta la cosecha"
    assert schema.detectar_etapas("desde los 3 gramos hasta la cosecha") == {"engorde"}


def test_r42_req4_transferencia_suelta_no_es_post_transferencia():
    # Nicovita Classic/Origin Precria (PDF)
    assert schema.detectar_etapas(
        "Dieta balanceada extruida para alimentar Post Larvas de Camarones de Mar o Langostinos "
        "(Litopenaeus vannamei) en estadios de PL10 a 1 gramo de peso, en sistemas de transferencia."
    ) == {"post_larva"}
    assert schema.detectar_etapas("classic post transferencia") == {"post_transferencia"}
    assert schema.detectar_etapas("post-transferencia") == {"post_transferencia"}
    assert schema.detectar_etapas("etapa de transición") == {"post_transferencia"}


def test_r42_req5_pl_con_numero_es_post_larva():
    # Nicovita Katal Precria (web): "para precrías desde PL20 hasta 1 g"
    assert schema.detectar_etapas("para precrías desde PL20 hasta 1 g") == {"precria", "post_larva"}
    assert schema.detectar_etapas("en estadios de PL 4 a 1g") == {"post_larva"}
    assert schema.detectar_etapas("explora y plantea") == set()


# --- R3.7: normalize_proteina ---

def test_normalize_proteina_acepta_numero_texto_y_coma_decimal():
    assert schema.normalize_proteina(35) == 35.0
    assert schema.normalize_proteina("35") == 35.0
    assert schema.normalize_proteina("37.5") == 37.5
    assert schema.normalize_proteina("37,5") == 37.5
    assert schema.normalize_proteina(" 35 % ") == 35.0
    assert type(schema.normalize_proteina("35")) is float


def test_normalize_proteina_ambiguo_o_fuera_de_rango_queda_vacio():
    for valor in (None, "", "s/d", "30%, 35%", 0.375, "0,375", 0, 120):
        assert schema.normalize_proteina(valor) is None, valor
