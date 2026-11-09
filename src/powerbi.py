"""Excel por país y empresa para Power BI: data/powerbi/<pais>/<empresa>.xlsx.

Contrato (specs/tech-stack.md, tabla "Excel para Power BI"): 16 columnas, en ese
orden, con tipos fijos. Sin transformaciones: los valores vienen del master ya
normalizado. Las filas cargadas a mano (competencia_human.xlsx) se suman a su
país y empresa (R5.2).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from openpyxl import Workbook

import schema

ROOT = Path(__file__).resolve().parent.parent
POWERBI_DIR = ROOT / "data" / "powerbi"
HUMAN_PATH = ROOT / "data" / "competencia_human.xlsx"

BOOLEAN_COLUMNS = [
    "es_producto_de_salud",
    "etapa_reproductores",
    "etapa_larva",
    "etapa_post_larva",
    "etapa_precria",
    "etapa_post_transferencia",
    "etapa_engorde",
]
DECIMAL_COLUMNS = ["particula_min_mm", "particula_max_mm", "proteina_pct"]

POWERBI_COLUMNS = [
    "pais",
    "empresa",
    "nombre_producto",
    "es_producto_de_salud",
    "etapa_reproductores",
    "etapa_larva",
    "etapa_post_larva",
    "etapa_precria",
    "etapa_post_transferencia",
    "etapa_engorde",
    "etapa_skt",
    "tamano_pellet_mm",
    "particula_min_mm",
    "particula_max_mm",
    "tipo_presentacion",
    "proteina_pct",
]
TEXT_COLUMNS = [c for c in POWERBI_COLUMNS if c not in BOOLEAN_COLUMNS + DECIMAL_COLUMNS]

_TRUE = {"true", "1", "1.0", "si", "sí", "yes"}
_FALSE = {"false", "0", "0.0", "no"}


def _vacio(valor) -> bool:
    if valor is None:
        return True
    if isinstance(valor, float) and pd.isna(valor):
        return True
    return isinstance(valor, str) and valor.strip() == ""


AVISOS: list[str] = []  # valores no vacíos que no se pudieron tipar (se vacían y se avisan)


def _bool(valor):
    if _vacio(valor):
        return None
    if isinstance(valor, bool):
        return valor
    if isinstance(valor, (int, float)):
        return bool(valor)
    texto = str(valor).strip().lower()
    if texto in _TRUE:
        return True
    if texto in _FALSE:
        return False
    AVISOS.append(f"booleano no reconocido: {valor!r}")
    return None


def _decimal(valor):
    if _vacio(valor):
        return None
    if isinstance(valor, (int, float)):
        return float(valor)
    try:
        return float(str(valor).strip().replace(",", "."))
    except ValueError:
        AVISOS.append(f"decimal no convertible: {valor!r}")
        return None


def _texto(valor):
    if _vacio(valor):
        return None
    if isinstance(valor, float) and valor.is_integer():
        return str(int(valor))
    return str(valor).strip()


def a_contrato(df: pd.DataFrame) -> pd.DataFrame:
    """Devuelve el DataFrame con exactamente POWERBI_COLUMNS, tipado.
    Vacío queda vacío (None); nunca se inventa un valor."""
    salida = pd.DataFrame(index=df.index)
    for col in POWERBI_COLUMNS:
        if col in df.columns:
            serie = df[col]
        else:
            serie = pd.Series([None] * len(df), index=df.index)
        if col in BOOLEAN_COLUMNS:
            salida[col] = serie.map(_bool).astype(object)
        elif col in DECIMAL_COLUMNS:
            salida[col] = serie.map(_decimal).astype(object)
        else:
            salida[col] = serie.map(_texto).astype(object)
    return salida[POWERBI_COLUMNS]


def filas_humanas(path: Path | None = HUMAN_PATH) -> pd.DataFrame:
    """Filas de competencia_human.xlsx en el esquema de Power BI (R5.2).

    Sin columna `pais` (o celda vacía) se asume ecuador, igual que
    merge_human._with_default_pais (PLAN_REGIONAL 2.5). Las etapa_* salen de
    etapa_competidor si el archivo la trae (puente R3.5); etapa_skt y las
    particulas se derivan como en pipeline.write_csv."""
    if path is None or not Path(path).exists():
        return pd.DataFrame(columns=POWERBI_COLUMNS)
    df = pd.read_excel(path, dtype=object)
    if "pais" not in df.columns:
        df["pais"] = "ecuador"
    df["pais"] = [("ecuador" if _vacio(p) else p) for p in df["pais"]]
    filas = []
    for _, fila in df.iterrows():
        rec = {c: fila.get(c) for c in df.columns}
        etapa = _texto(rec.get("etapa_competidor"))
        if etapa:
            rec.update(schema.etapas_desde_competidor(etapa))
        tamano = _texto(rec.get("tamano_pellet_mm"))
        rec["etapa_skt"] = schema.etapa_skt_from_row(etapa, tamano, False)
        rec["particula_min_mm"], rec["particula_max_mm"] = schema.parse_particula_range(tamano)
        filas.append(rec)
    return pd.DataFrame(filas)


def _escribir_xlsx(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    wb = Workbook()
    ws = wb.active
    ws.title = "datos"
    ws.append(POWERBI_COLUMNS)
    for fila in df.itertuples(index=False):
        ws.append([None if (v is None or (isinstance(v, float) and pd.isna(v))) else v for v in fila])
    wb.save(path)


def escribir_todo(master: pd.DataFrame, out_dir: Path = POWERBI_DIR, human_path: Path | None = HUMAN_PATH) -> list[Path]:
    """Escribe out_dir/<pais>/<empresa>.xlsx para cada par del master (y de las
    filas humanas). Devuelve las rutas escritas."""
    AVISOS.clear()
    partes = [a_contrato(master)]
    humanas = filas_humanas(human_path)
    if len(humanas):
        partes.append(a_contrato(humanas))
    todo = pd.concat(partes, ignore_index=True)
    todo = todo[todo["pais"].notna() & todo["empresa"].notna()]
    for aviso in AVISOS:
        print(f"[powerbi] AVISO: {aviso} (queda vacío en el Excel)")
    escritos = []
    for (pais, empresa), grupo in todo.groupby(["pais", "empresa"], sort=True):
        ruta = Path(out_dir) / str(pais) / f"{empresa}.xlsx"
        _escribir_xlsx(grupo.reset_index(drop=True), ruta)
        escritos.append(ruta)
    # Un par (pais, empresa) que ya no existe no debe quedar publicado con datos viejos.
    for viejo in Path(out_dir).glob("*/*.xlsx"):
        if viejo not in escritos:
            viejo.unlink()
    return escritos
