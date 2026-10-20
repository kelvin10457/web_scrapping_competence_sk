"""Almacenamiento local (SQLite) para productos agregados/corregidos a mano
desde la GUI (ver gui.py, ManualRecordDialog).

Reemplaza a data/competencia_human.xlsx como via de ENTRADA del formulario
manual -- un .db no se "abre en Excel" ni bloquea la escritura si alguien lo
tiene abierto (ver el PermissionError que gui.py ya maneja al escribir los
.xlsx), y soporta insertar fila por fila sin reescribir el archivo completo.
competencia_human.xlsx se sigue leyendo si existe (ver gui.py
_recolectar_fuentes_humanas) para no perder captura previa a este cambio,
pero deja de ser la via nueva de captura.

Cada laptop mantiene su propio archivo en data/competencia_manual.db
(conversacion con el usuario, 2026-09-16: no hay servidor compartido, cada
companero agrega productos desde su propia maquina). Para consolidar el
trabajo de varios companeros en un solo master_prototipo.xlsx, alguien reune
los .db de cada quien y los importa todos en la GUI ("Importar de
companeros...") antes de correr la fusion -- merge_human.apply_merge_many()
los aplica en secuencia para que el archivo del segundo companero ya vea lo
que aplico el primero.
"""
from __future__ import annotations

import sqlite3
import sys
from datetime import date
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import schema  # noqa: E402

if getattr(sys, "frozen", False):
    # Mismo ajuste que pipeline.py/merge_human.py: empaquetado con
    # PyInstaller, data/ debe vivir junto al .exe, no en la carpeta temporal
    # que __file__ apuntaria dentro del binario.
    ROOT = Path(sys.executable).resolve().parent
else:
    ROOT = Path(__file__).resolve().parent.parent

DEFAULT_DB_PATH = ROOT / "data" / "competencia_manual.db"

_TABLE = "registros_manuales"


def ensure_db(db_path: Path = DEFAULT_DB_PATH) -> None:
    """Crea el archivo .db y la tabla si no existen. Todas las columnas se
    guardan como TEXT -- mismo criterio que ya usa merge_human.py con el
    Excel humano: el valor crudo se re-tipa recien al fusionar
    (_typed_value), no hace falta que sqlite conozca el tipo real de cada
    columna de antemano."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    columnas_sql = ", ".join(f'"{c}" TEXT' for c in schema.SCHEMA_COLUMNS)
    with sqlite3.connect(db_path) as conn:
        conn.execute(f"CREATE TABLE IF NOT EXISTS {_TABLE} (id INTEGER PRIMARY KEY AUTOINCREMENT, {columnas_sql})")
        _migrar_pais(conn)


def _migrar_pais(conn: sqlite3.Connection) -> None:
    """Bases creadas antes de la expansion regional no tienen la columna
    `pais`: se agrega con default 'ecuador' (PLAN_REGIONAL.md 2.5)."""
    columnas = [fila[1] for fila in conn.execute(f"PRAGMA table_info({_TABLE})")]
    if "pais" not in columnas:
        conn.execute(f"ALTER TABLE {_TABLE} ADD COLUMN pais TEXT DEFAULT 'ecuador'")


def insert_record(record: dict, db_path: Path = DEFAULT_DB_PATH) -> int:
    """Inserta un registro (dict con claves de schema.SCHEMA_COLUMNS) y
    devuelve su id autoincremental. No valida -- el caller (gui.py) debe
    correr merge_human.validate_rows() sobre el registro antes de llamar a
    esto, igual que ya se exige para el Excel humano."""
    ensure_db(db_path)
    columnas = schema.SCHEMA_COLUMNS
    placeholders = ", ".join("?" for _ in columnas)
    record = {**record, "pais": record.get("pais") or "ecuador"}
    valores = [None if record.get(c) is None else str(record[c]) for c in columnas]
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute(
            f'INSERT INTO {_TABLE} ({", ".join(columnas)}) VALUES ({placeholders})',
            valores,
        )
        return cur.lastrowid


def fetch_all(db_path: Path = DEFAULT_DB_PATH) -> pd.DataFrame:
    """Todos los registros guardados, en las mismas columnas/orden que
    schema.SCHEMA_COLUMNS -- listo para pasar directo a
    merge_human.validate_rows()/apply_merge_many(). Si el archivo no existe
    todavia (nadie ha agregado nada en esta laptop) devuelve un DataFrame
    vacio, no un error -- es un estado normal, no uno invalido."""
    if not db_path.exists():
        return pd.DataFrame(columns=schema.SCHEMA_COLUMNS)
    try:
        ensure_db(db_path)  # aplica la migracion de `pais` a bases viejas
        with sqlite3.connect(db_path) as conn:
            df = pd.read_sql_query(f"SELECT * FROM {_TABLE} ORDER BY id", conn)
    except (sqlite3.DatabaseError, pd.errors.DatabaseError) as exc:
        # pandas envuelve el sqlite3.DatabaseError original en el suyo propio
        # (pandas.errors.DatabaseError) al fallar la query -- hay que atrapar
        # ambos para cubrir tanto un archivo que no es sqlite en absoluto
        # como uno que si lo es pero no tiene la tabla esperada.
        raise ValueError(f"{db_path.name} no es un archivo de datos manuales valido: {exc}") from exc
    if df.empty:
        return pd.DataFrame(columns=schema.SCHEMA_COLUMNS)
    return df[schema.SCHEMA_COLUMNS].reset_index(drop=True)


def today_str() -> str:
    return date.today().isoformat()
