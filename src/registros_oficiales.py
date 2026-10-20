"""Fase 5 (PLAN_REGIONAL.md): registros oficiales como fuente COMPLEMENTARIA.

Nunca crean filas en el master. Solo:
  1. completan celdas vacias (proteina_pct, tamano_pellet_mm, empaque_kg) de un
     producto ya scrapeado cuando el nombre coincide sin ambiguedad; cada celda
     completada queda en data/conflictos.csv con regla `registro_oficial:<fuente>`;
  2. dejan en data/registros_oficiales.csv|xlsx todo lo registrado con su
     estado (coincide / difiere / completa_nulo / sin_match) para revision
     manual: los `sin_match` son SKUs o competidores que no tenemos.

Fuentes:
  - SENASICA (Mexico): "Productos regulados y registrados" de la Direccion de
    Sanidad Acuicola, con el analisis garantizado (formula) de cada alimento.
    La version de datos.gob.mx / repodatos.atdt.gob.mx responde 403 fuera de
    Mexico (2026-10-20); se usa la publicada en agricultura.gob.mx (jul-2024).
  - eaduana.com: fichas de clasificacion arancelaria (Mexico/Ecuador/Colombia/
    Peru) con analisis garantizado, calibre y presentacion. No dicen el
    fabricante, por eso solo se cruzan por nombre exacto.

`actualizar()` descarga (red, con cache en data/raw/) y deja los registros en
data/processed/_registros_oficiales.csv; `aplicar()` es pura sobre el DataFrame
del master y la llama pipeline.build_master().
"""
from __future__ import annotations

import datetime
import re
import time
import unicodedata
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

import netutil

SENASICA_URL = ("https://www.agricultura.gob.mx/sites/default/files/sagarpa/document/"
                "2024/07/05/2209/08072024-productos-regulados-registrados.xlsx")
EADUANA_SITEMAP = "https://www.eaduana.com/subheadings_tariff_sitemap/sitemap.xml"
EADUANA_BASE = "https://www.eaduana.com/fracciones-arancelarias/"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; competence-scraper/1.0)"}

RAW_DIR = netutil.DATA_DIR / "raw"
SENASICA_XLSX = RAW_DIR / "senasica" / "productos_regulados_registrados.xlsx"
EADUANA_DIR = RAW_DIR / "eaduana"
MAX_DIAS_CACHE = 30

REGISTRO_COLUMNS = ["fuente", "pais", "empresa", "empresa_registro", "nombre_producto",
                    "proteina_pct", "tamano_pellet_mm", "empaque_kg", "registro", "vigencia",
                    "fuente_url"]
REVISAR_COLUMNS = REGISTRO_COLUMNS + ["estado", "coincide_con", "proteina_master"]
CAMPOS = ["proteina_pct", "tamano_pellet_mm", "empaque_kg"]

# Razon social en SENASICA -> `empresa` del master. Las demas quedan sin mapear
# (empresa vacia) y salen como `sin_match` para revision.
EMPRESAS_SENASICA = {
    "VIMIFOS": "Vimifos",
    "AGRIBRANDS PURINA": "Cargill",  # registra la linea Aquaxcel en Mexico
    "MALTA TEXO": "Api-Aba",  # APICAMARON
    "NUTRICION MARINA": "Nutrimar",
}

# Slugs de eaduana que vale la pena bajar (de ~1500 fichas de la partida 23.09
# y afines). Luego se filtra por contenido: camaron + 2309.
_EADUANA_SLUG_RE = re.compile(
    r"camaron|shrimp|vannamei|larva|aquatech|aquaxcel|nicovita|agripac|feedpac|royal-|"
    r"vitellus|mpex|larfeed|haid|biomar|vimifos|zeigler|apicamaron|exia|bumper|xtrudix|"
    r"raceway|nursery|starter|grower")

_STOP = {"de", "del", "la", "el", "y", "con", "proteina", "kg", "20kg", "25kg"}


def _sin_acentos(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c))


def clave(nombre: str | None) -> frozenset[str]:
    """Clave de comparacion de nombres: sin acentos, sin '%', guiones dentro de
    palabras unidos ("XTRU-DIX 2" == "Xtrudix 2") y sin palabras de relleno."""
    if not nombre:
        return frozenset()
    s = _sin_acentos(str(nombre)).lower().replace("%", " ")
    s = re.sub(r"(?<=[a-z])-(?=[a-z])", "", s)
    s = re.sub(r"(\d),(\d)", r"\1.\2", s)
    tokens = re.findall(r"[a-z0-9]+(?:\.[0-9]+)?", s)
    return frozenset(t for t in tokens if t not in _STOP)


def _num(texto: str) -> float:
    return float(texto.replace(",", "."))


_PROTEINA_RE = re.compile(
    # "prote.na": el xlsx de SENASICA trae la i acentuada danada (U+FFFD) en muchas filas.
    r"prote.na\s*(?:cruda)?[\s,:.(]*(?:m.n[\s.:]*)?[^0-9a-z]{0,15}(\d+(?:[.,]\d+)?)\s*%",
    re.IGNORECASE)


def proteina_de_formula(formula: str | None) -> float | None:
    """Proteina minima garantizada de un analisis ("Proteina cruda, min ..35%",
    "PROTEINA CRUDA 40.00 % MIN"). Ignora "Proteinas de origen marino 68%",
    que es un ingrediente, no el analisis."""
    if not formula or not isinstance(formula, str):
        return None
    m = _PROTEINA_RE.search(formula)
    if not m:
        return None
    valor = _num(m.group(1))
    return valor if 5 <= valor <= 70 else None


def _mm_unico(texto: str | None) -> str | None:
    """Un solo calibre en mm ("2.0 mm", "3 mm (3000 micras)", "800 um"); None si
    hay varios o ninguno (ahi no hay un valor para completar sin adivinar)."""
    if not texto:
        return None
    t = _sin_acentos(texto).lower()
    valores = {_num(v) for v in re.findall(r"(\d+(?:[.,]\d+)?)\s*mm\b", t)}
    # "3 mm (3000 micras)" da 3 dos veces: el set lo deja en uno.
    valores |= {_num(v) / 1000 for v in re.findall(r"(\d+(?:[.,]\d+)?)\s*(?:um|µm|micras)\b", t)}
    valores = {round(v, 2) for v in valores}
    return f"{valores.pop():g}" if len(valores) == 1 else None


def _kg_unico(texto: str | None) -> str | None:
    if not texto:
        return None
    valores = {_num(v) for v in re.findall(r"(\d+(?:[.,]\d+)?)\s*kg", texto.lower())}
    return f"{valores.pop():g}" if len(valores) == 1 else None


# ---------------------------------------------------------------- SENASICA

def leer_senasica(path: Path = SENASICA_XLSX) -> pd.DataFrame:
    """El xlsx trae 5 filas de membrete antes del encabezado."""
    df = pd.read_excel(path, dtype=str, header=5)
    df.columns = ["nombre", "empresa", "ingredientes", "formula", "uso", "dosis", "retiro",
                  "registro", "clasificacion", "fecha_registro", "vigencia"]
    return df


def _empresa_master(razon_social: str | None) -> str | None:
    rs = _sin_acentos(str(razon_social or "")).upper()
    return next((v for k, v in EMPRESAS_SENASICA.items() if k in rs), None)


def registros_senasica(df: pd.DataFrame) -> list[dict]:
    """Solo alimentos (no aditivos/medicamentos) para camaron."""
    out = []
    for r in df.itertuples(index=False):
        texto = f"{r.nombre} {r.uso}".lower()
        if "alimen" not in str(r.clasificacion).lower() or "camar" not in texto:
            continue
        vigencia = pd.to_datetime(r.vigencia, errors="coerce")
        out.append({
            "fuente": "senasica", "pais": "mexico",
            "empresa": _empresa_master(r.empresa),
            "empresa_registro": str(r.empresa).strip(),
            "nombre_producto": str(r.nombre).strip(),
            "proteina_pct": proteina_de_formula(r.formula),
            "tamano_pellet_mm": _mm_unico(r.nombre),
            "empaque_kg": None,
            "registro": None if pd.isna(r.registro) else str(r.registro).strip(),
            "vigencia": None if pd.isna(vigencia) else vigencia.date().isoformat(),
            "fuente_url": SENASICA_URL,
        })
    return out


# ---------------------------------------------------------------- eaduana

def parse_eaduana(html: str) -> dict | None:
    """Ficha de eaduana -> registro, o None si no es alimento para camaron
    (partida 2309) -- p. ej. "Omega 35" es aceite de pescado."""
    soup = BeautifulSoup(html, "html.parser")
    texto = soup.get_text(" ", strip=True)
    if "2309" not in texto or not re.search(r"camar|vannamei|shrimp", texto, re.IGNORECASE):
        return None
    h1 = soup.find("h1")
    canonical = soup.find("link", rel="canonical")
    filas = {}
    tabla = soup.find("table", class_="double-field-table")
    for tr in tabla.find_all("tr") if tabla else []:
        tds = tr.find_all("td")
        if len(tds) == 2:
            filas[_sin_acentos(tds[0].get_text(strip=True)).lower()] = tds[1].get_text(" ", strip=True)

    def fila(*claves):
        return " ".join(v for k, v in filas.items() if any(c in k for c in claves)) or None

    analisis = fila("analisis")
    # Sin fila de analisis, la descripcion a veces dice "de 35% proteina".
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*%\s*prote", texto, re.IGNORECASE)
    proteina = proteina_de_formula(analisis) or (_num(m.group(1)) if m else None)
    return {
        "fuente": "eaduana", "pais": None, "empresa": None, "empresa_registro": None,
        "nombre_producto": h1.get_text(strip=True) if h1 else None,
        "proteina_pct": proteina,
        "tamano_pellet_mm": _mm_unico(fila("tamano", "diametro", "aspecto", "calibre")),
        "empaque_kg": _kg_unico(fila("presentacion")),
        "registro": None, "vigencia": None,
        "fuente_url": canonical["href"] if canonical and canonical.get("href") else None,
    }


# ---------------------------------------------------------------- red

def _vigente(path: Path, max_dias: int) -> bool:
    return path.exists() and (time.time() - path.stat().st_mtime) < max_dias * 86400


def actualizar(destino: Path, max_dias: int = MAX_DIAS_CACHE, session=None) -> int:
    """Baja SENASICA y las fichas de eaduana (cache de `max_dias`) y escribe los
    registros en `destino`. Devuelve cuantos registros hay."""
    s = session or requests.Session()
    if not _vigente(SENASICA_XLSX, max_dias):
        r = netutil.get(s, SENASICA_URL, headers=HEADERS, timeout=120)
        r.raise_for_status()
        SENASICA_XLSX.parent.mkdir(parents=True, exist_ok=True)
        SENASICA_XLSX.write_bytes(r.content)
    registros = registros_senasica(leer_senasica(SENASICA_XLSX))

    EADUANA_DIR.mkdir(parents=True, exist_ok=True)
    sitemap = EADUANA_DIR / "_sitemap.xml"
    if not _vigente(sitemap, max_dias):
        r = netutil.get(s, EADUANA_SITEMAP, headers=HEADERS, timeout=60)
        r.raise_for_status()
        sitemap.write_text(r.text, encoding="utf-8")
    slugs = sorted(set(re.findall(r"fracciones-arancelarias/([^<\s]+)</loc>",
                                  sitemap.read_text(encoding="utf-8"))))
    for slug in (x for x in slugs if _EADUANA_SLUG_RE.search(x)):
        pagina = EADUANA_DIR / f"{slug}.html"
        if not pagina.exists():
            r = netutil.get(s, EADUANA_BASE + slug, headers=HEADERS, timeout=60)
            r.raise_for_status()
            pagina.write_text(r.text, encoding="utf-8")
            if netutil.ENABLED:
                time.sleep(2)  # cortesia: eaduana no esta en PACED_HOSTS
        registro = parse_eaduana(pagina.read_text(encoding="utf-8"))
        if registro:
            registros.append(registro)

    destino.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(registros, columns=REGISTRO_COLUMNS).to_csv(destino, index=False, encoding="utf-8-sig")
    return len(registros)


# ---------------------------------------------------------------- cruce

def _vacio(v) -> bool:
    return v is None or (isinstance(v, float) and pd.isna(v)) or str(v).strip() == ""


def _fmt(v) -> str:
    return f"{float(v):g}" if not _vacio(v) and re.fullmatch(r"\d+(?:\.\d+)?", str(v)) else str(v)


def aplicar(master: pd.DataFrame, registros: pd.DataFrame | None) -> tuple[pd.DataFrame, pd.DataFrame, list[dict]]:
    """Cruza registros oficiales con el master (sin red, sin crear filas).

    Coincidencia: misma `clave()` de nombre y, si el registro trae pais/empresa,
    mismos pais/empresa. Si un registro coincide con mas de un producto o un
    producto con mas de un registro, no se completa nada (ambiguo).
    Devuelve (master completado, tabla para revisar, filas de conflictos)."""
    master = master.copy()
    if registros is None or registros.empty:
        return master, pd.DataFrame(columns=REVISAR_COLUMNS), []
    hoy = datetime.date.today().isoformat()
    claves_master = master["nombre_producto"].map(clave)

    def candidatos(reg) -> list:
        mask = claves_master == clave(reg["nombre_producto"])
        if not _vacio(reg["pais"]):
            mask &= master["pais"] == reg["pais"]
        if not _vacio(reg["empresa"]):
            mask &= master["empresa"] == reg["empresa"]
        return list(master.index[mask & (claves_master != frozenset())])

    matches = {i: candidatos(reg) for i, reg in registros.iterrows()}
    # Un producto puede estar registrado dos veces con los mismos datos (p. ej.
    # Dorado 35% en SENASICA): solo es ambiguo si los registros difieren.
    valores_por_producto: dict[int, set] = {}
    for i, idx in matches.items():
        tupla = tuple(_fmt(registros.at[i, c]) if not _vacio(registros.at[i, c]) else None for c in CAMPOS)
        for j in idx:
            valores_por_producto.setdefault(j, set()).add(tupla)

    revisar, conflictos = [], []
    for i, reg in registros.iterrows():
        fila = {c: reg.get(c) for c in REGISTRO_COLUMNS}
        idx = matches[i]
        fila.update(estado="sin_match", coincide_con=None, proteina_master=None)
        if len(idx) > 1 or (idx and len(valores_por_producto[idx[0]]) > 1):
            fila["estado"] = "ambiguo"
            fila["coincide_con"] = " | ".join(sorted(set(master.loc[idx, "nombre_producto"])))
        elif idx:
            j = idx[0]
            fila["coincide_con"] = master.at[j, "nombre_producto"]
            fila["proteina_master"] = master.at[j, "proteina_pct"]
            completados, difiere = [], False
            for campo in CAMPOS:
                oficial, actual = reg.get(campo), master.at[j, campo]
                if _vacio(oficial):
                    continue
                if _vacio(actual):
                    master.at[j, campo] = _fmt(oficial)
                    completados.append(campo)
                    conflictos.append({
                        "pais": master.at[j, "pais"], "empresa": master.at[j, "empresa"],
                        "nombre_producto": master.at[j, "nombre_producto"], "campo": campo,
                        "valor_elegido": _fmt(oficial), "regla": f"registro_oficial:{reg['fuente']}",
                        "candidatos": f"{_fmt(oficial)} ({reg['fuente']}: {reg['nombre_producto']}"
                                      + (f", registro {reg['registro']}" if not _vacio(reg.get("registro")) else "")
                                      + ") | vacio (sitio)",
                        "fuente_url": reg["fuente_url"], "fecha_extraccion": hoy,
                    })
                elif _fmt(oficial) != _fmt(actual):
                    difiere = True
            fila["estado"] = ("completa_nulo" if completados else "difiere" if difiere else "coincide")
        revisar.append(fila)
    return master, pd.DataFrame(revisar, columns=REVISAR_COLUMNS), conflictos


def leer_registros(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    return pd.read_csv(path, dtype=str, keep_default_na=False, na_values=[""])
