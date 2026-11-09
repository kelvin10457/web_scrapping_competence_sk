"""Parser de ProAqua (distribuidor, Mexico), R7.9. Tienda BigCommerce proaqua.mx.

Del listado de la categoria Camaron entran solo los alimentos formulados
(decision del usuario 2026-11-09). Cada ficha: titulo "Nombre [Empaque] Marca",
descripcion (#ProductDescription) y tablas de composicion; una tabla con
encabezado "Parametro | V1 | V2" trae una columna por variante."""
from __future__ import annotations

import datetime
import os
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import schema  # noqa: E402

_FORMULADO_RE = re.compile(r"biogrow\s+formula|biogrow\s+xt|epifeed|epibal", re.I)
_PNAME_RE = re.compile(r'<a href="([^"]+)" class="\s*pname">([^<]+)</a>')
_EMPAQUE_RE = re.compile(r"\[[^\]]*?(\d+(?:[.,]\d+)?)\s*(kilos?|kg|li?l?bras?|lb)\b[^\]]*\]", re.I)
_MICRAS_TEXTO_RE = re.compile(r"\bde\s+(\d+)\s*-\s*(\d+)\s*micras", re.I)
_XT_RE = re.compile(r"XT\s+ULTRA\s+(\d+(?:[.,]\d+)?)\s*MM", re.I)
_DEFINE_RE = re.compile(r"\bes\s+una?\b", re.I)
_LIBRA_KG = 0.45359237


def _fmt(x: float) -> str:
    return f"{x:g}"


def _num(s: str) -> float:
    return float(s.replace(",", "."))


def _clave(s: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", s.upper())


def productos_de_listado(html: str) -> list[tuple[str, str]]:
    """[(url, nombre)] de los alimentos formulados de una pagina del listado."""
    vistos = {}
    for url, nombre in _PNAME_RE.findall(html):
        nombre = " ".join(nombre.split())
        if _FORMULADO_RE.search(nombre):
            vistos.setdefault(url, nombre)
    return list(vistos.items())


def _titulo(soup) -> str:
    t = " ".join(soup.title.get_text().split()) if soup.title else ""
    return t.split(" - ProAqua")[0].strip()


def _nombre_base(titulo: str) -> str:
    n = re.sub(r"\s*\[[^\]]*\]\s*", " ", titulo)
    n = re.sub(r"\s+Epicore\s*$", "", n.strip(), flags=re.I)
    n = re.split(r"\s+adicionado\s+con", n, flags=re.I)[0]
    n = re.sub(r"^Alimento\s+para\s+camar[oó]n\s+", "", n, flags=re.I)
    return " ".join(n.split())


def _empaque(titulo: str) -> str | None:
    m = _EMPAQUE_RE.search(titulo)
    if not m:
        return None
    valor = _num(m.group(1))
    if m.group(2).lower().startswith(("kilo", "kg")):
        return _fmt(valor)
    return _fmt(round(valor * _LIBRA_KG, 2))


def _tablas(desc) -> tuple[dict[str, str], dict[str, dict[str, str]]]:
    """(comunes {parametro: valor}, variantes {columna: {parametro: valor}})."""
    comunes, variantes = {}, {}
    for tabla in desc.find_all("table"):
        filas = [[" ".join(c.get_text(" ").split()) for c in tr.find_all(["td", "th"])]
                 for tr in tabla.find_all("tr")]
        filas = [f for f in filas if len(f) >= 2]
        if not filas:
            continue
        cols = filas[0][1:] if filas[0][0].lower().startswith("par") else None
        if cols is None:
            comunes.update({f[0]: f[1] for f in filas})
        elif len(cols) == 1:
            comunes.update({f[0]: f[1] for f in filas[1:]})
        else:
            for f in filas[1:]:
                for col, valor in zip(cols, f[1:]):
                    variantes.setdefault(col, {})[f[0]] = valor
    return comunes, variantes


def _buscar(param: dict[str, str], patron: str) -> str | None:
    return next((v for k, v in param.items() if re.search(patron, k, re.I)), None)


def _presentacion(param: dict[str, str], texto: str) -> str | None:
    forma = _buscar(param, r"^forma")
    if forma:
        return schema.normalize_presentacion(forma)
    if re.search(r"tecnolog[ií]a\s+de\s+microencapsulaci[oó]n", texto, re.I):
        return schema.normalize_presentacion("Microencapsulado")
    if re.search(r"tecnolog[ií]a\s+de\s+extrusi[oó]n", texto, re.I):
        return schema.normalize_presentacion("Extruido")
    return None


def _definicion(texto: str) -> str:
    """La primera oracion que define el producto ("X es una dieta ...")."""
    for oracion in re.split(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÑ])", texto):
        if _DEFINE_RE.search(oracion):
            return oracion
    return ""


def _variante(nombre_base: str, col: str) -> str:
    partes = nombre_base.split()
    if partes and _clave(col).startswith(_clave(partes[-1])):
        return " ".join(partes[:-1] + [col])
    return f"{nombre_base} {col}"


def parse_producto(url: str, html: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    titulo = _titulo(soup)
    desc = soup.find(id="ProductDescription")
    if desc is None:
        return []
    texto = " ".join(desc.get_text(" ").split()).replace(" ®", "®")
    base = _nombre_base(titulo)
    empresa = "Epicore" if "epicore" in titulo.lower() else "Biogrow" if "biogrow" in titulo.lower() else None
    comunes, variantes = _tablas(desc)
    elegidas = {c: p for c, p in variantes.items() if _clave(c) in _clave(base)}
    if not elegidas and variantes:
        # Titulo que nombra una variante ("Epibal-200") sin columna propia: no se
        # reparte en las demas columnas (revision Codex); queda solo lo comun.
        prefijo = re.match(r"[A-Z]+", os.path.commonprefix([_clave(c) for c in variantes]))
        if prefijo and re.search(prefijo.group(0) + r"\d", _clave(base)):
            variantes = {}
    variantes = elegidas or variantes

    # (nombre, tamano_mm, parametros) por fila
    filas = []
    xt = list(dict.fromkeys(_fmt(_num(m)) for m in _XT_RE.findall(texto)))
    if xt:
        filas = [(base, t, comunes) for t in xt]
    elif variantes:
        for col, p in variantes.items():
            nombre = base if elegidas else _variante(base, col)
            filas.append((nombre, None, {**comunes, **p}))
    else:
        filas = [(base, None, comunes)]

    paren = " ".join(re.findall(r"\(([^)]*)\)", base))
    etapas = schema.detectar_etapas(f"{paren} {_definicion(texto)}")
    mt = _MICRAS_TEXTO_RE.search(texto)
    hoy = datetime.date.today().isoformat()
    records = []
    for nombre, tamano, p in filas:
        if tamano is None:
            micras = _buscar(p, r"tama.*micr")
            if micras and re.fullmatch(r"\d+(?:[.,]\d+)?", micras):
                tamano = _fmt(_num(micras) / 1000)
            elif mt:
                tamano = f"{_fmt(int(mt.group(1)) / 1000)}-{_fmt(int(mt.group(2)) / 1000)}"
        record = schema.empty_record(empresa)
        record["nombre_producto"] = nombre
        record["tamano_pellet_mm"] = tamano
        record["tipo_presentacion"] = _presentacion(p, texto)
        record["empaque_kg"] = _empaque(titulo)
        record["proteina_pct"] = schema.normalize_proteina(_buscar(p, r"^prote"))
        record["fuente_url"] = url
        record["fecha_extraccion"] = hoy
        record["_etapas_detectadas"] = True
        record.update(schema.columnas_etapa(etapas))
        records.append(record)
    return records


# R11.3: selección verificada en la columna Camarón de las fichas Instant
# Algae y en las aplicaciones de LPB. N-Rich y dietas de rotíferos no entran.
_REED_RE = re.compile(
    r"^Concentrado de microalga Instant Algae "
    r"(?:Isochrysis 1800|Tetraselmis 3600|TW 1200|TP 1800)(?:\s*\([^)]*\))?$"
    r"|^Concentrado de Microalgas LPB para Larvas, Juveniles y Reproductores de Reed Mariculture$",
    re.I,
)
_CELULA_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*-\s*(\d+(?:[.,]\d+)?)\s*(?:[µμ]m|micrones)\b", re.I)


def productos_reed_de_listado(html: str) -> list[tuple[str, str]]:
    """Solo las cinco microalgas Reed con aplicación publicada para camarón."""
    soup = BeautifulSoup(html, "lxml")
    vistos = {}
    for enlace in soup.select("a.pname[href]"):
        nombre = " ".join(enlace.get_text(" ").split())
        if _REED_RE.fullmatch(nombre):
            vistos.setdefault(enlace["href"], nombre)
    return list(vistos.items())


def parse_reed(url: str, html: str) -> list[dict]:
    """Una fila por microalga; etapas y tecnología solo del texto propio."""
    soup = BeautifulSoup(html, "lxml")
    titulo = _titulo(soup)
    desc = soup.find(id="ProductDescription")
    if desc is None or not _REED_RE.fullmatch(titulo):
        return []
    # Las tablas compartidas de especies y las dosis no describen las etapas
    # del producto. Se excluyen antes de delimitar el texto de cada aplicación.
    for tabla in desc.find_all("table"):
        tabla.decompose()
    texto = " ".join(desc.get_text(" ").split())
    lpb = re.search(r"\bL\s+P\s+B Frozen Shellfish Diet\b", texto)
    if lpb:
        nombre = re.sub(r"\bL\s+P\s+B\b", "LPB", lpb.group())
        aplicacion = re.search(r"\bAplicaciones\b(.*?)\bIngredientes\b", texto, re.I)
        camaron = re.search(r"\bCamar[oó]n\b(.*)", aplicacion.group(1), re.I) if aplicacion else None
        propio = camaron.group(1) if camaron else ""
        celula = re.search(r"Tamaño de la célula:\s*(.*?)(?:Densidad|$)", texto, re.I)
        tamano = _CELULA_RE.search(celula.group(1)) if celula else None
        proteina = re.search(r"Prote[ií]na\s*[><=]?\s*(\d+(?:[.,]\d+)?\s*%)", texto, re.I)
    else:
        nombre = re.sub(r"^Concentrado de microalga\s+", "", titulo, flags=re.I)
        nombre = re.sub(r"\s*\([^)]*\)", "", nombre).strip()
        # Sin el cierre de la introducción no se toma texto genérico por propio.
        partes = texto.split("sistema de cultivo de zooplancton o tanque.", 1)
        propio = partes[1].strip() if len(partes) == 2 else ""
        tamano = _CELULA_RE.search(propio)
        proteina = None
    record = schema.empty_record("Reed Mariculture")
    record["nombre_producto"] = nombre
    if tamano:
        record["tamano_pellet_mm"] = "-".join(_fmt(_num(n) / 1000) for n in tamano.groups())
    record["proteina_pct"] = schema.normalize_proteina(proteina.group(1) if proteina else None)
    record["tipo_presentacion"] = schema.detect_tecnologia(propio)
    record.update(schema.columnas_etapa(schema.detectar_etapas(propio)))
    record["_etapas_detectadas"] = True
    record["fuente_url"] = url
    record["fecha_extraccion"] = datetime.date.today().isoformat()
    return [record]
