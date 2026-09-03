"""Parser de Nicovita: HTML de pagina de producto + texto de la ficha
tecnica PDF -> dict con el esquema unificado (schema.SCHEMA_COLUMNS).

Todo por regex/keyword-matching, sin LLM (PLAN.md § 6). Si un campo no
aparece explicitamente en la fuente, queda None -- no se infiere.
"""
from __future__ import annotations

import datetime
import io
import re

import pdfplumber

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import schema  # noqa: E402

# Nombre comercial real por slug de URL (slug = URL sin "nicovita-" ni
# "-ecuador"). Se construyo a mano confirmando cada pagina contra su
# og:title y el campo "Nombre Comercial del Producto" de su PDF, porque
# ninguna de esas dos fuentes por si sola es confiable para TODOS los
# productos: el og:title de katal-ad-ecuador es identico al de katal-ecuador
# (bug del sitio), y el PDF de terap-e-ecuador es el mismo binario que el de
# terap-ecuador (Nicovita no publica una ficha distinta para la variante E+).
_SLUG_TO_NAME = {
    "classic": "Nicovita Classic",
    "classic-ad": "Nicovita Classic AD",
    "classic-post-transferencia": "Nicovita Classic Post Transferencia",
    "classic-precria": "Nicovita Classic Precría",
    "finalis": "Nicovita Finalis",
    "katal": "Nicovita Katal",
    "katal-ad": "Nicovita Katal AD",
    "katal-engorde": "Nicovita Katal Engorde",
    "katal-post-transferencia": "Nicovita Katal Post Transferencia",
    "katal-precria": "Nicovita Katal Precría",
    "katal-proterra": "Nicovita Katal Proterra",
    "classic-proterra": "Nicovita Classic Proterra",
    "finalis-proterra": "Nicovita Finalis Proterra",
    "origin": "Nicovita Origin",
    "qualis": "Nicovita Qualis",
    "terap": "Nicovita Térap",
    "terap-e": "Nicovita Térap E+",
}

_SLUG_RE = re.compile(r"nicovita-(?P<slug>[a-z0-9\-]+)-ecuador")
# Fallback para la linea Proterra (ver src/scrapers/nicovita.py): su URL no
# trae el sufijo "-ecuador", asi que el regex de arriba no matchea nada.
_SLUG_RE_SIN_PAIS = re.compile(r"nicovita\.com/productos/nicovita-(?P<slug>[a-z0-9\-]+)/?$")


def slug_from_url(url: str) -> str:
    m = _SLUG_RE.search(url)
    if m:
        return m.group("slug")
    m = _SLUG_RE_SIN_PAIS.search(url)
    return m.group("slug") if m else url


def product_name_from_slug(slug: str) -> str:
    if slug in _SLUG_TO_NAME:
        return _SLUG_TO_NAME[slug]
    # Fallback generico para slugs no mapeados a mano (ej. producto nuevo).
    return "Nicovita " + " ".join(w.upper() if w == "ad" else w.capitalize() for w in slug.split("-"))


def _extract_descripcion_html(html: str) -> str | None:
    m = re.search(r'id="descripcion">.*?<div class="inner">(.*?)</div>\s*</div>\s*</div>', html, re.S)
    if not m:
        return None
    text = re.sub(r"<[^>]+>", " ", m.group(1))
    text = re.sub(r"\s+", " ", text).strip()
    return text or None


def _extract_empaque_kg(html: str) -> str | None:
    """Kg por saco desde el tab 'Disponible para' (ej. "Saco de polipropileno
    laminado de 25 kg de peso neto")."""
    m = re.search(r'Presentaci[oó]n:?\s*</h3>\s*<p>([^<]+)</p>', html, re.I)
    if not m:
        return None
    kg_match = re.search(r"((?:\d+\s*(?:y|,)?\s*)+)kg\s+de\s+peso\s+neto", m.group(1), re.I)
    if not kg_match:
        return None
    kgs = re.findall(r"\d+", kg_match.group(1))
    return ",".join(kgs) if kgs else None


def _extract_pdf_url(html: str) -> str | None:
    m = re.search(
        r'href="(https://nicovita\.com/wp-content/uploads/[^"]+\.pdf)"\s+class="btn-link btn-violeta"\s+download',
        html,
    )
    return m.group(1) if m else None


def _pdf_field_line(text: str, label_pattern: str) -> str | None:
    m = re.search(label_pattern + r"[^\n]*", text, re.I)
    return m.group(0) if m else None


def _first_number(line: str | None) -> float | None:
    if not line:
        return None
    m = re.search(r"\d+(?:\.\d+)?", line)
    return float(m.group(0)) if m else None


_REPRODUCTOR_MARKER = re.compile(r"reproductor|broodstock|maduraci[oó]n", re.I)
_EARLY_MARKER = re.compile(r"post\s*larva|postlarva|\bpl\s?\d|desde\s+pl\b", re.I)
_LATE_MARKER = re.compile(r"tama[ñn]o de mercado|hasta cosecha|tama[ñn]o de cosecha|peso de cosecha", re.I)


def _infer_etapa_from_description(text: str) -> str | None:
    """Fallback especifico de Nicovita cuando el slug no trae la etapa
    explicita (ej. 'classic', 'katal-ad'). Nicovita agrupa varios productos
    bajo una etiqueta de categoria ambigua ('Iniciadores') que no distingue
    entre un producto exclusivamente de larva (Origin) y uno de rango
    completo post-larva-a-mercado (Classic/Katal base) -- por eso NO se usa
    esa etiqueta aqui. En su lugar se detecta el rango de peso real descrito
    en la ficha: si menciona SOLO el marcador temprano (post larva / PL) es
    'larva'; si menciona SOLO el tardio (tamano de mercado / cosecha) es
    'engorde'; si menciona ambos o ninguno, el producto cubre multiples
    etapas y no se fuerza un valor (queda None).

    Ya NO prioriza el marcador de enfermedad (ver _detect_producto_salud):
    un producto con funcion terapeutica (ej. Terap, "post larva hasta
    tamano de mercado para disminuir carga microbiana") NO tiene una etapa
    propia -- puede cubrir cualquier rango de tamano, igual que uno sin esa
    funcion. Devolver 'salud' aca antes descartaba la etapa real que el
    mismo texto tambien describia (hallazgo del usuario 2026-09-02, ver
    MEMORY.md)."""
    if _REPRODUCTOR_MARKER.search(text):
        return "reproductores"
    early = bool(_EARLY_MARKER.search(text))
    late = bool(_LATE_MARKER.search(text))
    if early and not late:
        return "larva"
    if late and not early:
        return "engorde"
    return None


def parse_pdf_text(pdf_text: str) -> dict:
    """Campos que si se pueden leer de forma segura como texto plano. NO
    incluye proteina_pct/tamano_pellet_mm -- esos se leen de la tabla
    estructurada de la ficha (ver _extract_presentacion_pairs) porque un
    regex sobre el texto aplanado no distingue que tamano va con que
    proteina (MEMORY.md, bug tamano/proteina 2026-09-02)."""
    fields: dict = {}

    fields["tipo_presentacion"] = schema.detect_tecnologia(pdf_text)
    fields["grasa_pct"] = _first_number(_pdf_field_line(pdf_text, r"Grasa\s*\(%\)"))

    desc_match = re.search(
        r"Descripci[oó]n del Producto\s*\n(.+?)\n\s*3\.", pdf_text, re.S
    )
    fields["_descripcion_pdf"] = " ".join(desc_match.group(1).split()) if desc_match else None

    return fields


_PROTEIN_CELL_RE = re.compile(r"^\d+(?:\.\d+)?%$")
_SIZE_CELL_RE = re.compile(r"^\d+(?:\.\d+)?(?:-\d+(?:\.\d+)?)?$")


def _extract_presentacion_pairs(pdf) -> list[tuple[str, str]]:
    """Extrae pares reales (proteina_pct, tamano_mm) de la tabla 'Presentacion
    Comercial' (seccion 4 de la ficha). Nicovita la publica como FORMATO (%)
    -> DIAMETRO (mm), donde un mismo % agrupa varios tamanos (celda
    combinada en el PDF) y un mismo tamano puede repetirse bajo % distintos
    -- ej. Classic AD: 2.5mm aparece en la fila de 28% Y en la de 35%. No es
    una correspondencia 1 a 1 por posicion, asi que no se puede reconstruir
    leyendo "Proteina (%)" y "Presentacion Comercial" como dos listas de
    numeros sueltas (enfoque anterior, ver git history / MEMORY.md). Ademas,
    al menos una ficha (Qualis) tiene el texto de la seccion 3.a
    desincronizado de su propia tabla (25% en el texto, 22% en la tabla) --
    por eso esta funcion lee UNICAMENTE la tabla, celda por celda, sin
    asumir una columna fija: el indice de columna del % y del tamano varia
    de una ficha a otra (confirmado con pdfplumber en 5 fichas reales).
    Recorre TODAS las paginas -- en fichas con mas filas en la tabla de
    composicion (ej. Katal Post Transferencia, que agrega Calcio/Sal/
    Fosforo) la tabla de Presentacion Comercial cae en la pagina 2, no la 1."""
    for page in pdf.pages:
        for table in page.extract_tables():
            header = " ".join((cell or "") for row in table[:2] for cell in row).upper()
            if "FORMATO" not in header:
                continue
            if "DIAMETRO" not in header and "PELLET" not in header:
                continue
            pairs: list[tuple[str, str]] = []
            current_protein: str | None = None
            for row in table:
                for cell in row:
                    if not cell:
                        continue
                    for token in cell.split("\n"):
                        token = token.strip()
                        if _PROTEIN_CELL_RE.match(token):
                            current_protein = token.rstrip("%")
                        elif _SIZE_CELL_RE.match(token) and current_protein is not None:
                            pairs.append((current_protein, token))
            if pairs:
                return pairs
    return []


def parse_product(url: str, html: str, pdf_bytes: bytes | None) -> list[dict]:
    """Devuelve una fila por combinacion real (tamano, proteina) del
    producto -- mismo grano que Aquaxcel -- en vez de una sola fila con dos
    listas aplanadas y sin relacion entre si (ver _extract_presentacion_pairs).
    Si no hay ficha PDF o su tabla no trae pares (ej. Katal Precria, sin
    ficha enlazada), devuelve una unica fila con esos dos campos en None."""
    record = schema.empty_record("Nicovita")
    record["fuente_url"] = url
    record["fecha_extraccion"] = datetime.date.today().isoformat()

    slug = slug_from_url(url)
    nombre = product_name_from_slug(slug)
    record["nombre_producto"] = nombre

    record["empaque_kg"] = _extract_empaque_kg(html)

    descripcion_html = _extract_descripcion_html(html) or ""

    pdf_fields = {}
    descripcion_pdf = ""
    pairs: list[tuple[str, str]] = []
    if pdf_bytes:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            pdf_text = "\n".join(p.extract_text() or "" for p in pdf.pages)
            pairs = _extract_presentacion_pairs(pdf)
        pdf_fields = parse_pdf_text(pdf_text)
        descripcion_pdf = pdf_fields.pop("_descripcion_pdf", None) or ""
        record.update(pdf_fields)

    # Etapa: primero por slug (fuente mas confiable y corta -- distingue
    # precria de post_transferencia, cosa que la propia categoria de
    # Nicovita NO hace, ver _infer_etapa_from_description). Si el slug no
    # trae la etapa explicita, se infiere del rango de peso descrito en la
    # ficha.
    etapa_text = f"{descripcion_pdf} {descripcion_html}"
    record["producto_salud"] = schema.detect_producto_salud(etapa_text)

    etapa = schema.normalize_etapa(slug.replace("-", " "))
    if etapa is None:
        etapa = _infer_etapa_from_description(etapa_text)
    record["etapa"] = etapa

    if not pairs:
        if record["etapa"] is None:
            record["etapa"] = schema.etapa_from_tamano(record["tamano_pellet_mm"], record["tipo_presentacion"])
        return [record]

    records = []
    for proteina, tamano in pairs:
        row = dict(record)
        row["proteina_pct"] = proteina
        row["tamano_pellet_mm"] = tamano
        # Fallback de ultimo recurso, por fila: si ni el slug ni la
        # descripcion del producto completo resolvieron etapa (ej. Classic/
        # Katal base, que cubren post-larva a mercado), se intenta con el
        # tamano puntual de ESTA fila -- solo es posible desde la
        # explosion a grano SKU (antes no habia un tamano puntual que usar).
        if row["etapa"] is None:
            row["etapa"] = schema.etapa_from_tamano(tamano, row["tipo_presentacion"])
        records.append(row)
    return records
