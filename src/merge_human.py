"""Fusiona data/competencia_human.xlsx (curado a mano) con data/master.xlsx
(scrapeado) -> data/master_prototipo.xlsx.

Uso: python src/merge_human.py

Prototipo: valida y fusiona por fuera de la GUI (src/gui.py), que no se toca
aca. No escribe nunca sobre data/master.xlsx -- la salida siempre es
data/master_prototipo.xlsx, con dos pestañas ("master" y "revisar").

Regla de matching (empresa + nombre_producto + los atributos que la fila
humana traiga rellenos): 0 coincidencias -> fila nueva; exactamente 1 ->
los campos no vacios de la fila humana sobrescriben esa fila; 2+ -> no se
aplica nada, se registra en la pestaña "revisar". Si el archivo humano no
pasa validacion (encabezados o valores), no se aplica NINGUN cambio -- ni
siquiera el de las filas que si estaban bien -- hasta que se corrija.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pipeline  # noqa: E402 (reusa _format_value para formatear numeros igual que el resto del pipeline)
import schema  # noqa: E402

if getattr(sys, "frozen", False):
    # Empaquetado con PyInstaller: __file__ apunta a la carpeta temporal
    # (_MEIxxxxx) que se borra al cerrar el .exe -- mismo ajuste que ya
    # tiene pipeline.py (ver ese modulo), necesario aca tambien porque el
    # formulario manual de gui.py depende de que estas rutas apunten a la
    # carpeta real junto al .exe, no a la temporal.
    ROOT = Path(sys.executable).resolve().parent
else:
    ROOT = Path(__file__).resolve().parent.parent
MASTER_PATH = ROOT / "data" / "master.xlsx"
HUMAN_PATH = ROOT / "data" / "competencia_human.xlsx"
OUTPUT_PATH = ROOT / "data" / "master_prototipo.xlsx"

# Columnas categoricas: solo valores ya definidos en schema.py, o vacio.
CATEGORICAL_COLUMNS = {
    "pais": set(schema.PAIS_VALUES),
    "etapa_competidor": schema.ETAPA_VALUES,
    "tipo_presentacion": schema.TIPO_PRESENTACION_VALUES,
    "etapa_skt": schema.ETAPA_SKT_VALUES,
}
BOOLEAN_COLUMNS = ["producto_salud"]
# Columnas numericas (deben ser numero o vacio en el archivo humano) -- a
# diferencia de schema.NUMERIC_COLUMNS, que es sobre los CSV/XLSX ya
# escritos por el pipeline (incluye particula_min_mm/max, no tamano_pellet_mm
# porque ahi tamano_pellet_mm sigue siendo texto libre que a veces es un
# rango). Aca tamano_pellet_mm SI debe ser un numero puntual: el archivo
# humano identifica un calibre especifico, no publica un rango de ficha.
NUMERIC_VALIDATE_COLUMNS = ["tamano_pellet_mm", "proteina_pct", "empaque_kg"]
REQUIRED_COLUMNS = ["empresa", "nombre_producto"]
# etapa_skt/particula_min_mm/particula_max_mm son siempre derivadas (igual
# que en pipeline.write_csv()) -- nunca se toma el valor que haya escrito el
# humano ahi, se recalculan desde tamano_pellet_mm/tipo_presentacion/
# etapa_competidor despues de aplicar la fusion. Se siguen exigiendo como
# encabezado (mismas columnas exactas que schema.SCHEMA_COLUMNS) pero su
# contenido no se valida ni se usa.
DERIVED_COLUMNS = ["etapa_skt", "particula_min_mm", "particula_max_mm"]


def _is_empty(value) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and pd.isna(value):
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return False


def _excel_row(df_index: int) -> int:
    """Indice de pandas -> numero de fila tal cual se ve en Excel (fila 1 es
    el encabezado, la primera fila de datos es la 2)."""
    return df_index + 2


def ensure_human_template() -> bool:
    """Crea competencia_human.xlsx vacio (solo encabezados) si no existe.
    Devuelve True si tuvo que crearlo -- en ese caso el caller debe avisar
    y terminar sin intentar fusionar nada."""
    if HUMAN_PATH.exists():
        return False
    HUMAN_PATH.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(columns=schema.SCHEMA_COLUMNS).to_excel(HUMAN_PATH, index=False)
    return True


def _with_default_pais(df: pd.DataFrame) -> pd.DataFrame:
    """Compatibilidad hacia atras: sin columna 'pais' (o celda vacia) -> 'ecuador'."""
    df = df.copy()
    if "pais" not in df.columns:
        df["pais"] = "ecuador"
    else:
        df["pais"] = df["pais"].where(df["pais"].notna(), "ecuador")
    return df


def validate_headers(df: pd.DataFrame) -> list[str]:
    """Encabezados deben ser EXACTAMENTE schema.SCHEMA_COLUMNS -- ni de mas
    ni de menos (el orden no importa, se reindexa despues)."""
    actual = list(df.columns)
    # 'pais' es opcional en archivos viejos (PLAN_REGIONAL.md 2.5): se asume ecuador.
    if "pais" not in actual:
        actual.append("pais")
    expected = set(schema.SCHEMA_COLUMNS)
    actual_set = set(actual)
    missing = [c for c in schema.SCHEMA_COLUMNS if c not in actual_set]
    extra = [c for c in actual if c not in expected]
    errors = []
    if missing:
        errors.append(f"Faltan columnas: {', '.join(missing)}")
    if extra:
        errors.append(f"Sobran columnas (no existen en schema.SCHEMA_COLUMNS): {', '.join(extra)}")
    return errors


def _drop_fully_empty_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Descarta filas donde TODAS las celdas estan vacias -- artefacto comun
    de guardar un Excel a mano (fila en blanco al final), no un error real
    que valga la pena reportar. Conserva el indice original para que
    _excel_row() siga apuntando a la fila correcta de las filas que quedan."""
    mask = df.apply(lambda row: not all(_is_empty(v) for v in row), axis=1)
    return df[mask]


def validate_rows(df: pd.DataFrame) -> list[str]:
    """Valida el contenido fila por fila (encabezados ya confirmados
    correctos). Acumula TODOS los errores encontrados -- no se detiene en
    el primero -- para que el reporte cubra el archivo completo de una sola
    pasada, tal como pide la tarea."""
    errors = []
    for idx, row in df.iterrows():
        fila = _excel_row(idx)
        for col in REQUIRED_COLUMNS:
            if _is_empty(row[col]):
                errors.append(
                    f"fila {fila}, columna {col}: no puede estar vacio "
                    "(obligatorio para poder buscar coincidencias en master)"
                )
        for col, valid_values in CATEGORICAL_COLUMNS.items():
            value = row.get(col)
            if _is_empty(value):
                continue
            text = str(value).strip()
            if text not in valid_values:
                opciones = "/".join(sorted(valid_values))
                errors.append(f"fila {fila}, columna {col}: '{text}' no es valido (opciones: {opciones})")
        for col in BOOLEAN_COLUMNS:
            value = row[col]
            if _is_empty(value):
                continue
            if isinstance(value, bool):
                continue
            if isinstance(value, (int, float)) and value in (0, 1):
                # Excel/pandas coercionan una columna booleana a 0.0/1.0
                # apenas mezcla alguna celda vacia (confirmado con
                # competencia_human.xlsx real) -- no es un error del usuario.
                continue
            text = str(value).strip().lower()
            if text not in {"true", "false", "verdadero", "falso", "1", "0"}:
                errors.append(f"fila {fila}, columna {col}: '{value}' no es un booleano valido (true/false)")
        for col in NUMERIC_VALIDATE_COLUMNS:
            value = row[col]
            if _is_empty(value):
                continue
            try:
                float(str(value).strip())
            except ValueError:
                errors.append(f"fila {fila}, columna {col}: '{value}' no es un numero")
    return errors


def _to_float(value) -> float | None:
    if _is_empty(value):
        return None
    return float(str(value).strip())


def _typed_value(col: str, raw_value):
    """Convierte el valor crudo de una celda humana al tipo que usa esa
    columna en master. Asume que ya paso validate_rows() (no puede fallar).
    None si la celda esta vacia -- el caller decide que hacer con eso (fila
    nueva: la columna queda en None; fila existente: no se toca)."""
    if _is_empty(raw_value):
        return None
    if col == "tamano_pellet_mm":
        # Texto formateado igual que el resto del pipeline (sin ".0" de mas),
        # no el float crudo -- master guarda esta columna como texto porque
        # a veces es un rango (ver NUMERIC_VALIDATE_COLUMNS arriba).
        return pipeline._format_value(float(str(raw_value).strip()))
    if col in ("proteina_pct", "empaque_kg"):
        return float(str(raw_value).strip())
    if col == "producto_salud":
        if isinstance(raw_value, bool):
            return raw_value
        if isinstance(raw_value, (int, float)) and raw_value in (0, 1):
            return bool(raw_value)
        return str(raw_value).strip().lower() in {"true", "verdadero", "1"}
    return str(raw_value).strip()


def _normalize_key(value) -> str:
    return "" if _is_empty(value) else str(value).strip().casefold()


def _master_tamano_as_float(text) -> float | None:
    """Lee tamano_pellet_mm de master como un solo numero. Si es un rango
    (ej. '0.5-1.0') o no tiene numero reconocible, devuelve None -- una fila
    humana con un calibre puntual no debe matchear por casualidad una fila
    de master que en realidad es un rango de ficha."""
    if _is_empty(text):
        return None
    text = str(text).strip()
    if "-" in text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def find_name_candidates(master_df: pd.DataFrame, empresa, nombre_producto, pais=None) -> pd.Index:
    """Filas de master_df cuya empresa+nombre_producto normalizados
    coinciden, SIN filtrar aun por tamano/proteina -- a diferencia de
    find_matches(), que ya angosta automaticamente con esos atributos si la
    fila humana los trae. Se separo para el formulario manual de la GUI (ver
    gui.py, ManualRecordDialog): el nombre puede repetirse entre variantes
    que solo cambian de etapa/tamano (hallazgo del usuario, 2026-09-16), asi
    que el formulario le muestra al humano TODOS los productos con ese
    nombre -- aunque tamano/proteina ya alcancen para distinguirlos -- para
    que confirme a ojo cual es, en vez de que el sistema elija solo."""
    empresa_key = _normalize_key(empresa)
    nombre_key = _normalize_key(nombre_producto)
    mask = (master_df["empresa"].map(_normalize_key) == empresa_key) & (
        master_df["nombre_producto"].map(_normalize_key) == nombre_key
    )
    if not _is_empty(pais):
        # pais forma parte de la identidad (PLAN_REGIONAL.md 2.5).
        mask &= master_df["pais"].map(_normalize_key) == _normalize_key(pais)
    return master_df.index[mask]


def find_matches(master_df: pd.DataFrame, human_row: pd.Series) -> pd.Index:
    """Indices de master_df que coinciden con esta fila humana: empresa +
    nombre_producto normalizados, mas tamano_pellet_mm/proteina_pct SOLO si
    la fila humana los trae rellenos (son los atributos que distinguen
    variantes con el mismo nombre, ej. Nicovita Classic)."""
    candidates = find_name_candidates(
        master_df, human_row["empresa"], human_row["nombre_producto"], human_row.get("pais")
    )
    mask = pd.Series(master_df.index.isin(candidates), index=master_df.index)
    tamano = _to_float(human_row["tamano_pellet_mm"])
    if tamano is not None:
        mask &= master_df["tamano_pellet_mm"].map(_master_tamano_as_float) == tamano
    proteina = _to_float(human_row["proteina_pct"])
    if proteina is not None:
        mask &= master_df["proteina_pct"] == proteina
    return master_df.index[mask]


def _recompute_derived(df: pd.DataFrame, idx) -> None:
    """Recalcula etapa_skt/particula_min_mm/particula_max_mm para una fila,
    mismo mecanismo que pipeline.write_csv() usa para los 4 CSV scrapeados
    -- se ignora a proposito cualquier valor que el humano haya escrito en
    esas 3 columnas (son derivadas, nunca dato primario)."""
    etapa_competidor = df.at[idx, "etapa_competidor"]
    tamano = df.at[idx, "tamano_pellet_mm"]
    tipo = df.at[idx, "tipo_presentacion"]
    df.at[idx, "etapa_skt"] = schema.etapa_skt_from_row(etapa_competidor, tamano, tipo)
    pmin, pmax = schema.parse_particula_range(tamano)
    df.at[idx, "particula_min_mm"] = pmin
    df.at[idx, "particula_max_mm"] = pmax


def _normalize_master_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """pandas infiere el dtype de cada columna de un .xlsx por su contenido:
    una columna que en esta tanda de datos resulta ser 100% numerica (ej.
    tamano_pellet_mm sin ningun rango presente) o 100% vacia (ej. etapa_skt/
    producto_salud si el master de prueba no trae ninguna) se lee como
    float64 -- confirmado con un master.xlsx sintetico de pocas filas.
    Escribirle despues un texto o un booleano a esa columna via .at[]
    revienta con TypeError. Se normalizan a texto/objeto todas las columnas
    que NO son estrictamente numericas (deja intactas
    schema.NUMERIC_COLUMNS, que si deben seguir siendo float real) para no
    depender de que dtype le toque adivinar a pandas en cada corrida."""
    df = _with_default_pais(df)
    for col in schema.SCHEMA_COLUMNS:
        if col in schema.NUMERIC_COLUMNS:
            continue
        if col == "tamano_pellet_mm":
            df[col] = df[col].map(
                lambda v: None if pd.isna(v) else (pipeline._format_value(v) if isinstance(v, float) else str(v))
            )
        elif col == "producto_salud":
            df[col] = df[col].map(lambda v: None if pd.isna(v) else bool(v))
        else:
            df[col] = df[col].astype(object).where(df[col].notna(), None)
    return df


def apply_merge(master_df: pd.DataFrame, human_df: pd.DataFrame) -> tuple[pd.DataFrame, list[dict], int, int]:
    """Aplica la fusion fila por fila. Devuelve (master_actualizado,
    filas_ambiguas, cantidad_nuevas, cantidad_corregidas). Asume que
    human_df ya paso validate_headers()/validate_rows()."""
    master_df = _normalize_master_dtypes(master_df)
    human_df = _with_default_pais(human_df)
    review_rows: list[dict] = []
    new_records: list[dict] = []
    n_updated = 0

    for h_idx, human_row in human_df.iterrows():
        matches = find_matches(master_df, human_row)

        if len(matches) == 0:
            record = {}
            for col in schema.SCHEMA_COLUMNS:
                record[col] = None if col in DERIVED_COLUMNS else _typed_value(col, human_row[col])
            record["etapa_skt"] = schema.etapa_skt_from_row(
                record["etapa_competidor"], record["tamano_pellet_mm"], record["tipo_presentacion"]
            )
            record["particula_min_mm"], record["particula_max_mm"] = schema.parse_particula_range(
                record["tamano_pellet_mm"]
            )
            new_records.append(record)
            continue

        if len(matches) == 1:
            idx = matches[0]
            for col in schema.SCHEMA_COLUMNS:
                if col in DERIVED_COLUMNS:
                    continue
                value = _typed_value(col, human_row[col])
                if value is not None:
                    master_df.at[idx, col] = value
            _recompute_derived(master_df, idx)
            n_updated += 1
            continue

        candidatos = [
            f"tamano={master_df.at[m, 'tamano_pellet_mm']}, proteina={master_df.at[m, 'proteina_pct']}"
            for m in matches
        ]
        review_rows.append(
            {
                "fila_humana": _excel_row(h_idx),
                "pais": human_row["pais"],
                "empresa": human_row["empresa"],
                "nombre_producto": human_row["nombre_producto"],
                "tamano_pellet_mm_humano": human_row["tamano_pellet_mm"],
                "proteina_pct_humano": human_row["proteina_pct"],
                "cantidad_coincidencias": len(matches),
                "candidatos_en_master": "; ".join(candidatos),
            }
        )

    if new_records:
        new_df = pd.DataFrame(new_records, columns=schema.SCHEMA_COLUMNS)
        master_df = pd.concat([master_df, new_df], ignore_index=True)

    return master_df, review_rows, len(new_records), n_updated


def apply_merge_many(
    master_df: pd.DataFrame, human_dfs: list[pd.DataFrame]
) -> tuple[pd.DataFrame, list[dict], int, int]:
    """Aplica varios archivos humanos en secuencia sobre el mismo master,
    cada uno viendo ya lo que el anterior aplico. Existe para consolidar el
    trabajo de varios companeros -- cada uno con su propio
    data/competencia_manual.db (ver src/manual_store.py), sin servidor
    compartido -- sin que el segundo archivo duplique un producto que el
    primero ya agrego (conversacion con el usuario, 2026-09-16). Asume que
    cada df en human_dfs ya paso validate_rows()."""
    total_new = 0
    total_updated = 0
    all_review: list[dict] = []
    for human_df in human_dfs:
        if human_df.empty:
            continue
        master_df, review_rows, n_new, n_updated = apply_merge(master_df, human_df)
        total_new += n_new
        total_updated += n_updated
        all_review.extend(review_rows)
    return master_df, all_review, total_new, total_updated


REVIEW_COLUMNS = [
    "fila_humana",
    "pais",
    "empresa",
    "nombre_producto",
    "tamano_pellet_mm_humano",
    "proteina_pct_humano",
    "cantidad_coincidencias",
    "candidatos_en_master",
]


def write_output(master_df: pd.DataFrame, review_rows: list[dict]) -> None:
    master_df = master_df[schema.SCHEMA_COLUMNS]
    review_df = pd.DataFrame(review_rows, columns=REVIEW_COLUMNS)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(OUTPUT_PATH, engine="openpyxl") as writer:
        master_df.to_excel(writer, sheet_name="master", index=False)
        review_df.to_excel(writer, sheet_name="revisar", index=False)


def main() -> int:
    if not MASTER_PATH.exists():
        print(f"No existe {MASTER_PATH} -- corre primero 'python src/pipeline.py'.")
        return 1

    if ensure_human_template():
        print(f"No existia {HUMAN_PATH} -- se creo vacio con los encabezados correctos.")
        print("Llenalo con los datos de competencia curados a mano y corre este script de nuevo.")
        return 0

    human_df = pd.read_excel(HUMAN_PATH)

    header_errors = validate_headers(human_df)
    if header_errors:
        print(f"Encabezados invalidos en {HUMAN_PATH}:")
        for error in header_errors:
            print(f"  - {error}")
        print("Corrige los encabezados y corre de nuevo. No se aplico ningun cambio.")
        return 1

    human_df = _with_default_pais(human_df)[schema.SCHEMA_COLUMNS]
    human_df = _drop_fully_empty_rows(human_df)

    if human_df.empty:
        print(f"{HUMAN_PATH} no tiene filas -- llenalo antes de correr este script.")
        return 0

    row_errors = validate_rows(human_df)
    if row_errors:
        print(f"{len(row_errors)} error(es) de validacion en {HUMAN_PATH}:")
        for error in row_errors:
            print(f"  - {error}")
        print("Corrige el archivo y corre de nuevo. No se aplico ningun cambio, ni siquiera el de las filas correctas.")
        return 1

    master_df = _with_default_pais(pd.read_excel(MASTER_PATH))
    master_df, review_rows, n_new, n_updated = apply_merge(master_df, human_df)
    write_output(master_df, review_rows)

    print(f"OK: {n_new} fila(s) nueva(s), {n_updated} fila(s) corregida(s), {len(review_rows)} ambigua(s).")
    print(f"Escrito {OUTPUT_PATH} (pestañas 'master' y 'revisar'). data/master.xlsx no fue modificado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
