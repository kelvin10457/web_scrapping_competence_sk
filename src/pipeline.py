"""Orquestador: scrape -> parse -> CSV por empresa -> master.csv.

Uso: python src/pipeline.py [--pais P] [--empresa E]
Sin argumentos corre todos los (pais, empresa) de fuentes.py. Cada empresa se corre de forma aislada
(un fallo en una no afecta a las demas) y master.csv se regenera siempre
al final con lo que haya en processed/ (PLAN.md § 4-5: snapshot, no historico).
"""
from __future__ import annotations

import argparse
from datetime import datetime
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
CONFLICTOS_PATH = ROOT / "data" / "conflictos.csv"

import fuentes  # noqa: E402
import netutil  # noqa: E402
import registros_oficiales  # noqa: E402

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


def conflictos_path(pais: str) -> Path:
    return PROCESSED_DIR / pais / "_conflictos.csv"


def write_conflictos(records: list[dict], pais: str, empresa: str) -> int:
    """Reemplaza las filas de `empresa` en processed/{pais}/_conflictos.csv por
    los conflictos de esta corrida (las de otras empresas del pais se conservan)."""
    path = conflictos_path(pais)
    nuevas = pd.DataFrame(schema.conflictos_de(records), columns=schema.CONFLICTO_COLUMNS)
    # La columna empresa trae el nombre del record ("Api-Aba", "Zeigler"), no el slug.
    propias = {empresa.lower()} | {str(r.get("empresa")).lower() for r in records}
    if path.exists():
        previas = pd.read_csv(path, dtype=str, keep_default_na=False, na_values=[""])
        previas = previas[~previas["empresa"].str.lower().isin(propias)]
        nuevas = pd.concat([previas, nuevas], ignore_index=True)
    if nuevas.empty:
        if path.exists():
            path.unlink()
        return 0
    path.parent.mkdir(parents=True, exist_ok=True)
    nuevas.to_csv(path, index=False, encoding="utf-8-sig")
    return len(schema.conflictos_de(records))


def build_conflictos(extra: list[dict] | None = None) -> None:
    """Junta todos los processed/*/_conflictos.csv en data/conflictos.csv, mas
    `extra` (celdas completadas con registros oficiales en build_master)."""
    frames = [pd.read_csv(p, dtype=str, keep_default_na=False, na_values=[""])
              for p in sorted(PROCESSED_DIR.glob("*/_conflictos.csv"))]
    if extra:
        frames.append(pd.DataFrame(extra, columns=schema.CONFLICTO_COLUMNS))
    if not frames:
        pd.DataFrame(columns=schema.CONFLICTO_COLUMNS).to_csv(CONFLICTOS_PATH, index=False, encoding="utf-8-sig")
        return
    pd.concat(frames, ignore_index=True)[schema.CONFLICTO_COLUMNS].to_csv(
        CONFLICTOS_PATH, index=False, encoding="utf-8-sig")


def registros_path() -> Path:
    return PROCESSED_DIR / "_registros_oficiales.csv"


def revisar_registros_path() -> Path:
    return MASTER_PATH.parent / "registros_oficiales.csv"


def actualizar_registros(max_dias: int = registros_oficiales.MAX_DIAS_CACHE) -> str:
    """Fase 5: baja SENASICA/eaduana (cache de `max_dias`). Es complementaria:
    si falla se avisa y el master se arma igual con los registros anteriores.
    Devuelve el mensaje para el log (CLI o GUI)."""
    try:
        n = registros_oficiales.actualizar(registros_path(), max_dias=max_dias)
        return f"--- registros oficiales: {n} (SENASICA + eaduana) ---"
    except Exception as exc:
        return f"  AVISO: no se pudieron actualizar los registros oficiales ({exc}); se usan los anteriores."


def build_master() -> None:
    frames = []
    for pais, empresa in fuentes.listar():
        csv_path = processed_path(pais, empresa)
        # Los archivos que empiezan con "_" (ej. _conflictos.csv) no son productos.
        if csv_path.exists() and not csv_path.name.startswith("_"):
            frames.append(pd.read_csv(csv_path, dtype=str, keep_default_na=False, na_values=[""]))
    # Cualquier otro processed/{pais}/*.csv que ya no este en el registro igual entra.
    if not frames:
        build_conflictos()
        return
    master = pd.concat(frames, ignore_index=True)
    master = master[schema.SCHEMA_COLUMNS]
    # Registros oficiales: solo completan celdas vacias, nunca agregan filas.
    master, revisar, completados = registros_oficiales.aplicar(
        master, registros_oficiales.leer_registros(registros_path()))
    build_conflictos(completados)
    if not revisar.empty:
        revisar.to_csv(revisar_registros_path(), index=False, encoding="utf-8-sig")
        revisar.to_excel(revisar_registros_path().with_suffix(".xlsx"), index=False)
    master.to_csv(MASTER_PATH, index=False, encoding="utf-8-sig")
    write_xlsx(master, MASTER_PATH.with_suffix(".xlsx"))
    # Un master por pais: data/processed/{pais}/master_{pais}.csv|xlsx (cada pais
    # puede ofrecer productos distintos aunque la empresa sea la misma).
    for pais, df_pais in master.groupby("pais", sort=False):
        pais_path = PROCESSED_DIR / pais / f"master_{pais}.csv"
        df_pais.to_csv(pais_path, index=False, encoding="utf-8-sig")
        write_xlsx(df_pais, pais_path.with_suffix(".xlsx"))


def reportar_bloqueos(bloqueadas) -> None:
    """Resumen de fuentes bloqueadas por captcha y como ver el problema. Tambien
    se guarda en data/bloqueos.md."""
    if not bloqueadas:
        return
    lineas = [
        "# Fuentes bloqueadas por captcha",
        "",
        f"Corrida: {datetime.now():%Y-%m-%d %H:%M}",
        "",
        "| pais | empresa | pagina pedida | pagina del captcha que vio el script |",
        "|---|---|---|---|",
    ]
    for pais, empresa, exc in bloqueadas:
        lineas.append(f"| {pais} | {empresa} | {exc.url} | `{exc.saved}` |")
    lineas += [
        "",
        "## Como ver el problema",
        "1. Abre en tu navegador el archivo HTML de la ultima columna (doble clic): es lo que recibio el script en vez de la pagina.",
        "2. Abre tambien la 'pagina pedida' en tu navegador. Si ahi entras normal, el sitio solo bloquea a scripts (lo normal).",
        "3. El captcha se resuelve en TU navegador y no desbloquea al script. Alternativa: guarda las paginas con Guardar como... HTML en data/raw/nicovita_html/ (ver src/paises/_compartido/README.md) y vuelve a correr.",
        "4. El script no evade captchas. Esperar unas horas entre corridas y usar el ritmo con pausas ayuda a que no se repita.",
    ]
    texto = "\n".join(lineas) + "\n"
    (ROOT / "data").mkdir(exist_ok=True)
    (ROOT / "data" / "bloqueos.md").write_text(texto, encoding="utf-8")
    print("\n=== FUENTES BLOQUEADAS POR CAPTCHA ===")
    for pais, empresa, exc in bloqueadas:
        print(f"  - {pais}/{empresa}: {exc.url}\n      pagina del captcha: {exc.saved}")
    print("  Como verlo: abre ese archivo .html en tu navegador. Detalle en data/bloqueos.md\n")


def procesar(pais: str, empresa: str) -> tuple[int, int]:
    """Scrapea un (pais, empresa) y escribe su CSV y sus conflictos. Lo usan el
    CLI y la GUI. Devuelve (productos, conflictos resueltos)."""
    records = run_empresa(empresa, pais)
    if not records:
        # No pisar un CSV bueno con uno vacio (sitio caido/bloqueado/rediseñado).
        raise RuntimeError("0 productos: se conserva el CSV anterior")
    write_csv(records, processed_path(pais, empresa))
    return len(records), write_conflictos(records, pais, empresa)


def main(pares: list[tuple[str, str]], registros: bool = False, max_dias: int | None = None) -> int:
    """Corre cada (pais, empresa) de forma aislada. Devuelve la cantidad de errores.
    Con `registros` tambien actualiza SENASICA/eaduana antes de armar el master."""
    errores = 0
    bloqueadas: list[tuple[str, str, netutil.BlockedError]] = []
    netutil.reset_blocked()
    for pais, empresa in pares:
        print(f"--- {pais}/{empresa} ---")
        try:
            n, n_conf = procesar(pais, empresa)
            print(f"  OK: {n} productos -> data/processed/{pais}/{empresa}.csv")
            if n_conf:
                print(f"  {n_conf} conflictos resueltos -> data/processed/{pais}/_conflictos.csv")
        except netutil.BlockedError as exc:
            errores += 1
            bloqueadas.append((pais, empresa, exc))
            print(f"  BLOQUEADO {pais}/{empresa}: captcha/anti-bot. Se conserva el CSV anterior.")
            print(f"    Pagina que vio el script: {exc.saved}")
        except Exception:
            errores += 1
            print(f"  ERROR en {pais}/{empresa}:")
            traceback.print_exc()
    reportar_bloqueos(bloqueadas)
    if registros:
        print(actualizar_registros(registros_oficiales.MAX_DIAS_CACHE if max_dias is None else max_dias))
    build_master()
    print(f"--- master.csv regenerado en {MASTER_PATH} ---")
    return errores


def parse_args(argv: list[str]):
    parser = argparse.ArgumentParser(description="Scrapea competencia y regenera master.csv")
    parser.add_argument("--pais", choices=schema.PAIS_VALUES, help="solo este pais")
    parser.add_argument("--empresa", help="solo esta empresa")
    parser.add_argument("--registros", action="store_true",
                        help="volver a bajar SENASICA/eaduana aunque la cache tenga menos de 30 dias")
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    # Sin --empresa se saltan las fuentes pausadas (fuentes.INACTIVAS); con
    # --empresa se corren igual (p. ej. `--empresa nicovita`).
    pares = fuentes.listar(args.pais, args.empresa, solo_activas=args.empresa is None)
    if not pares:
        print(f"Sin fuentes registradas para pais={args.pais} empresa={args.empresa}")
        sys.exit(2)
    # Registros oficiales: en la corrida completa (cache de 30 dias) o con --registros.
    completa = args.pais is None and args.empresa is None
    sys.exit(1 if main(pares, registros=completa or args.registros,
                       max_dias=0 if args.registros else None) else 0)
