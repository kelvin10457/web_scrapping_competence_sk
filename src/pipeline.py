"""Orquestador: scrape -> parse -> CSV por empresa -> master.csv.

Uso: python src/pipeline.py [--pais P] [--empresa E]
Sin argumentos corre todos los (pais, empresa) de fuentes.py. Cada empresa se corre de forma aislada
(un fallo en una no afecta a las demas) y master.csv se regenera siempre
al final con lo que haya en processed/ (PLAN.md § 4-5: snapshot, no historico).
"""
from __future__ import annotations

import argparse
import sys
import traceback
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import schema  # noqa: E402

if getattr(sys, "frozen", False):
    # Empaquetado con PyInstaller: __file__ apunta a la carpeta temporal
    # (_MEIxxxxx) que se borra al cerrar el .exe. data/ debe vivir junto
    # al .exe, no ahi, o "desaparece" al cerrar la app.
    ROOT = Path(sys.executable).resolve().parent
else:
    ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = ROOT / "data" / "processed"
MASTER_PATH = ROOT / "data" / "master.csv"

import fuentes  # noqa: E402

ALL_EMPRESAS = fuentes.empresas()


def processed_path(pais: str, empresa: str) -> Path:
    return PROCESSED_DIR / pais / f"{empresa}.csv"


def run_empresa(empresa: str, pais: str = "ecuador") -> list[dict]:
    """Scrapea + parsea un (pais, empresa) segun el registro de fuentes.py."""
    return fuentes.run_fuente(pais, empresa)


def _format_value(value):
    """Evita que un float entero (ej. 35.0) se escriba con ".0" en el CSV.
    Aquaxcel ya usaba f"{v:g}" para tamano_pellet_mm/empaque_kg pero no para
    proteina_pct -- mismo criterio aplicado aca de forma pareja a las 4
    empresas en vez de repetirlo por parser. Motivo: un ".0" de mas en un
    visor de CSV con locale en español (donde "." es separador de miles) se lee como el
    valor x10 (ej. "45.0" -> 450) -- hallazgo del usuario 2026-09-02."""
    if isinstance(value, float):
        return f"{value:g}"
    return value


def write_xlsx(df: pd.DataFrame, path: Path) -> None:
    """Copia .xlsx del mismo DataFrame que el CSV, con `schema.NUMERIC_COLUMNS`
    convertidas a numero real (`pd.to_numeric`, `errors="coerce"`) en vez de
    texto. El CSV sigue siendo la fuente de verdad en texto tal cual la
    publica cada fuente -- este archivo es una copia de conveniencia para
    abrir directo en Excel sin que tenga que adivinar el separador decimal
    (ver `schema.NUMERIC_COLUMNS` para el motivo exacto)."""
    xlsx_df = df.copy()
    for col in schema.NUMERIC_COLUMNS:
        if col in xlsx_df.columns:
            xlsx_df[col] = pd.to_numeric(xlsx_df[col], errors="coerce")
    xlsx_df.to_excel(path, index=False)


def write_csv(records: list[dict], path: Path) -> None:
    for record in records:
        record["etapa_skt"] = schema.etapa_skt_from_row(
            record.get("etapa_competidor"),
            record.get("tamano_pellet_mm"),
            record.get("tipo_presentacion"),
            record.get("_es_larvicultura", False),
        )
        record["particula_min_mm"], record["particula_max_mm"] = schema.parse_particula_range(
            record.get("tamano_pellet_mm")
        )
    records = [{k: _format_value(v) for k, v in record.items()} for record in records]
    df = pd.DataFrame(records, columns=schema.SCHEMA_COLUMNS)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")
    write_xlsx(df, path.with_suffix(".xlsx"))


def build_master() -> None:
    frames = []
    for pais, empresa in fuentes.listar():
        csv_path = processed_path(pais, empresa)
        if csv_path.exists():
            frames.append(pd.read_csv(csv_path, dtype=str, keep_default_na=False, na_values=[""]))
    # Cualquier otro processed/{pais}/*.csv que ya no este en el registro igual entra.
    if not frames:
        return
    master = pd.concat(frames, ignore_index=True)
    master = master[schema.SCHEMA_COLUMNS]
    master.to_csv(MASTER_PATH, index=False, encoding="utf-8-sig")
    write_xlsx(master, MASTER_PATH.with_suffix(".xlsx"))


def main(pares: list[tuple[str, str]]) -> int:
    """Corre cada (pais, empresa) de forma aislada. Devuelve la cantidad de errores."""
    errores = 0
    for pais, empresa in pares:
        print(f"--- {pais}/{empresa} ---")
        try:
            records = run_empresa(empresa, pais)
            write_csv(records, processed_path(pais, empresa))
            print(f"  OK: {len(records)} productos -> data/processed/{pais}/{empresa}.csv")
        except Exception:
            errores += 1
            print(f"  ERROR en {pais}/{empresa}:")
            traceback.print_exc()
    build_master()
    print(f"--- master.csv regenerado en {MASTER_PATH} ---")
    return errores


def parse_args(argv: list[str]):
    parser = argparse.ArgumentParser(description="Scrapea competencia y regenera master.csv")
    parser.add_argument("--pais", choices=schema.PAIS_VALUES, help="solo este pais")
    parser.add_argument("--empresa", help="solo esta empresa")
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    pares = fuentes.listar(args.pais, args.empresa)
    if not pares:
        print(f"Sin fuentes registradas para pais={args.pais} empresa={args.empresa}")
        sys.exit(2)
    sys.exit(1 if main(pares) else 0)
