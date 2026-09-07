"""Orquestador: scrape -> parse -> CSV por empresa -> master.csv.

Uso: python src/pipeline.py [empresa ...]
Sin argumentos corre las 4 empresas. Cada empresa se corre de forma aislada
(un fallo en una no afecta a las demas) y master.csv se regenera siempre
al final con lo que haya en processed/ (PLAN.md § 4-5: snapshot, no historico).
"""
from __future__ import annotations

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

ALL_EMPRESAS = ["nicovita", "haid", "aquaxcel", "biomar", "agripac"]


def run_empresa(empresa: str) -> list[dict]:
    if empresa == "nicovita":
        from scrapers import nicovita as sc
        from parsers import nicovita as pr

        records = []
        for item in sc.scrape_all():
            records.extend(pr.parse_product(item["url"], item["html"], item["pdf_bytes"]))
        return records

    if empresa == "haid":
        from scrapers import haid as sc
        from parsers import haid as pr

        records = []
        for item in sc.scrape_all():
            records.extend(pr.parse_product(item["url"], item["html"], item["pdf_bytes"]))
        return records

    if empresa == "aquaxcel":
        from scrapers import aquaxcel as sc
        from parsers import aquaxcel as pr

        html = sc.fetch_listing()
        return pr.parse_listing(html)

    if empresa == "biomar":
        from scrapers import agrizon as agrizon_sc
        from parsers import agrizon as agrizon_pr

        # biomar.com deshabilitado a proposito (decision del usuario,
        # 2026-09-03): sus filas son solo identificacion por familia de
        # producto, sin tamano/clasificacion_camaron/proteina -- se prefiere que
        # BioMar aparezca unicamente via Agrizon, con datos tecnicos reales
        # por SKU, aunque eso deje fuera productos sin match en Agrizon
        # (Blue Impact, INICIO *, SmartCare Balance *, EXIA Focus). Ver
        # MEMORY.md "BioMar -- fuente complementaria Agrizon". src/scrapers/
        # biomar.py y src/parsers/biomar.py quedan sin usar aqui pero no se
        # borraron.
        return agrizon_pr.parse_listing(agrizon_sc.scrape_all())

    if empresa == "agripac":
        from scrapers import agripac as sc
        from parsers import agripac as pr

        return pr.parse_listing(sc.scrape_all())

    raise ValueError(f"Empresa desconocida: {empresa}")


def _format_value(value):
    """Evita que un float entero (ej. 35.0) se escriba con ".0" en el CSV.
    Aquaxcel ya usaba f"{v:g}" para tamano_pellet_mm/empaque_kg pero no para
    proteina_pct/grasa_pct, y HAID/Nicovita (grasa_pct) devuelven float crudo
    -- mismo criterio aplicado aca de forma pareja a las 4 empresas en vez de
    repetirlo por parser. Motivo: un ".0" de mas en un visor de CSV con
    locale en español (donde "." es separador de miles) se lee como el
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
        record["clasificacion_camaron"] = schema.clasificacion_camaron_from_row(
            record.get("etapa"),
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
    for empresa in ALL_EMPRESAS:
        csv_path = PROCESSED_DIR / f"{empresa}.csv"
        if csv_path.exists():
            frames.append(pd.read_csv(csv_path, dtype=str, keep_default_na=False, na_values=[""]))
    if not frames:
        return
    master = pd.concat(frames, ignore_index=True)
    master = master[schema.SCHEMA_COLUMNS]
    master.to_csv(MASTER_PATH, index=False, encoding="utf-8-sig")
    write_xlsx(master, MASTER_PATH.with_suffix(".xlsx"))


def main(empresas: list[str]) -> None:
    for empresa in empresas:
        print(f"--- {empresa} ---")
        try:
            records = run_empresa(empresa)
            write_csv(records, PROCESSED_DIR / f"{empresa}.csv")
            print(f"  OK: {len(records)} productos -> data/processed/{empresa}.csv")
        except Exception:
            print(f"  ERROR en {empresa}:")
            traceback.print_exc()
    build_master()
    print(f"--- master.csv regenerado en {MASTER_PATH} ---")


if __name__ == "__main__":
    args = sys.argv[1:] or ALL_EMPRESAS
    main(args)
