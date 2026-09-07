"""Esquema unificado de datos para el pipeline de scraping de competencia.

Ver PLAN.md § 3 para el diseño completo. Este modulo define:
- La lista de columnas del esquema unificado (mismo orden para los 4 CSV + master.csv).
- `normalize_etapa`: mapea el texto de etapa de cada empresa a los valores
  categoricos normalizados usados para poder filtrar entre empresas.
- `empty_record`: dict con todas las columnas en None, para que cada parser
  solo tenga que llenar lo que realmente encontro (evita inventar/inferir).
"""
from __future__ import annotations

import re

# Orden exacto de columnas para todos los CSV (por empresa y master.csv).
SCHEMA_COLUMNS = [
    # Identificacion
    "empresa",
    "nombre_producto",
    "etapa",
    "producto_salud",
    "clasificacion_camaron",
    "tamano_pellet_mm",
    "particula_min_mm",
    "particula_max_mm",
    "tipo_presentacion",
    "empaque_kg",
    # Composicion nutricional
    "proteina_pct",
    "grasa_pct",
    # Metadata
    "fuente_url",
    "fecha_extraccion",
]

# Columnas que representan un numero real (para promediar/filtrar/graficar),
# a diferencia de tamano_pellet_mm (mezcla numero suelto y rango como texto
# a proposito, ver parse_particula_range) o empaque_kg en los pocos casos
# donde una ficha publica mas de un peso de saco para el mismo producto
# (ej. Nicovita Origin, "10,20" -- ahi pd.to_numeric() simplemente no puede
# convertir y queda vacio, no se fuerza un valor). Usado por
# pipeline.write_xlsx() para que esas columnas salgan con tipo numerico
# real en el .xlsx en vez de texto -- así Excel no tiene que adivinar el
# separador decimal al abrir el archivo, que es lo que hace que un valor
# como "0.9" se lea como 9 bajo configuracion regional en espanol (punto
# interpretado como separador de miles, hallazgo del usuario 2026-09-03).
NUMERIC_COLUMNS = ["particula_min_mm", "particula_max_mm", "empaque_kg", "proteina_pct", "grasa_pct"]

# Valores normalizados validos para la columna "etapa" (PLAN.md § 3).
# "salud" YA NO es uno de ellos (ver nota abajo, 2026-09-02) -- se dejo aca
# comentado por si algun caller viejo lo referencia, pero normalize_etapa()
# no lo devuelve mas.
ETAPA_VALUES = {
    "larva",
    "precria",
    "post_transferencia",
    "engorde",
    "reproductores",
}

# Reglas de normalizacion: (regex sobre texto en minusculas -> etapa normalizada).
# Se evalua en orden; la primera regla que matchea gana. Ya NO incluye una
# regla "salud" (ver "producto_salud" en SCHEMA_COLUMNS, 2026-09-02): un
# producto con funcion terapeutica (ej. tratamiento anti-Vibrio) no tiene
# una etapa de ciclo de vida propia, puede cubrir cualquier rango de tamano
# -- forzarlo a "salud" en esta columna descartaba la etapa real que el
# texto tambien pudiera describir (hallazgo del usuario, ver MEMORY.md).
_ETAPA_RULES: list[tuple[re.Pattern, str]] = [
    (re.compile(r"post[\s\-_]?transfer|transferencia|transici[oó]n|alevinaje"), "post_transferencia"),
    (re.compile(r"larva|hatchery|mysis|\bpl\b|post[\s\-_]?larval"), "larva"),
    (re.compile(r"precr[ií]a|precria|starter|nursery|iniciador|\binicio\b"), "precria"),
    (re.compile(r"reproductor|broodstock|maduraci[oó]n"), "reproductores"),
    (re.compile(r"engorde|grow[\s\-_]?out|finalizador|finish|crecimiento"), "engorde"),
]


def normalize_etapa(raw_text: str | None) -> str | None:
    """Normaliza un texto libre de etapa (nombre de producto, categoria, etc.)
    a uno de los valores de ETAPA_VALUES. Devuelve None si no hay match
    (no se debe inventar una etapa que el texto no sugiere)."""
    if not raw_text:
        return None
    text = raw_text.strip().lower()
    for pattern, etapa in _ETAPA_RULES:
        if pattern.search(text):
            return etapa
    return None


def etapa_matches(raw_text: str | None) -> set[str]:
    """Como normalize_etapa, pero devuelve TODAS las etapas distintas que
    matchean el texto en vez de solo la primera. Uso: detectar cuando una
    fuente mezcla senales de mas de una etapa a la vez en el mismo texto,
    en vez de asumir que la primera regla que matcheo es la correcta --
    ej. Agrizon (src/parsers/agrizon.py) tagea un mismo SKU de Exia Prime
    1.2mm con "engorde" Y "Iniciadores" (categorias de merchandising) al
    mismo tiempo; con normalize_etapa() sola, el orden de _ETAPA_RULES
    decidiria arbitrariamente cual gana. Con esta funcion el caller puede
    chequear len(...) == 1 antes de confiar en el resultado."""
    if not raw_text:
        return set()
    text = raw_text.strip().lower()
    return {etapa for pattern, etapa in _ETAPA_RULES if pattern.search(text)}


# tipo_presentacion es la tecnologia de fabricacion del pellet (Extruido vs
# Pelletizado), no el material del empaque -- confirmado con el usuario
# 2026-09-01 tras notar que Aquaxcel (Extruido/Pelletizado) y Nicovita/HAID
# (antes: "Saco de polipropileno...") llenaban la misma columna con dos
# conceptos distintos e incomparables.
#
# Ampliada 2026-09-07 (division Larvicultura de Agripac, ver
# src/parsers/agripac.py) con 3 valores mas alla de la dicotomia original:
# "Polvo" (Artemia Cysts), "Microparticulado" (Mpex) y "Liquido" (Royal
# Pepper Protein) -- a pedido explicito del usuario, que prefirio agregarlos
# como categorias propias en vez de dejarlos en None (criterio usado antes
# para "Polvo" de Feedpac Premium y "Microgranulado" de Agrizon). Efecto
# retroactivo esperado: los productos Agripac que YA traian "Polvo" en su
# pestana "Tipo" (ej. "35% Premium Micropellet Agua Dulce") dejan de quedar
# en None y ahora muestran "Polvo".
_TECNOLOGIA_RE = re.compile(r"extrui|extrus|extrud|pel{1,2}etiz|\bpolvo\b|particulad|l[ií]quid", re.I)


def detect_tecnologia(text: str | None) -> str | None:
    """Detecta si el texto describe el producto como Extruido o Pelletizado.
    Usa la PRIMERA mencion en el texto: en las fichas HAID el encabezado
    (ej. "ALIMENTO BALANCEADO PELLETIZADO PARA CAMARON") precede a la
    descripcion, lo que resuelve el caso "Speed Pellet" -- su encabezado
    dice pelletizado pero el parrafo de descripcion dice, por error de la
    propia ficha, "elaborado por proceso de extruido" (MEMORY.md). Devuelve
    None si no se menciona ninguna de las dos -- no se asume una por
    defecto ni se infiere de otros campos.

    Ampliado 2026-09-03 (fuente Agrizon, ver src/parsers/agrizon.py) para
    cubrir tambien ingles y variantes que el regex original (solo
    "extrui"/"pelletiza", espanol) no reconocia: "Extrusado" (tag de
    Larviva) y "Pelletized"/"Extruded" (titulos de producto en ingles).
    Se recorta cada raiz a su prefijo comun (p.ej. "extrus" en vez de
    "extrusa") para que matchee ambos idiomas con una sola alternativa.

    Ampliado 2026-09-07 con "Polvo"/"Microparticulado"/"Liquido" (ver nota
    junto a `_TECNOLOGIA_RE`) -- "Microextruido" (MeM, Larvicultura) ya
    resolvia solo a "Extruido" desde antes, porque contiene "extrui" como
    substring, asi que no necesito una regla aparte para el."""
    if not text:
        return None
    m = _TECNOLOGIA_RE.search(text)
    if not m:
        return None
    token = m.group(0).lower()
    if token.startswith(("extrui", "extrus", "extrud")):
        return "Extruido"
    if token.startswith("pel"):
        return "Pelletizado"
    if token == "polvo":
        return "Polvo"
    if token.startswith("particulad"):
        return "Microparticulado"
    return "Líquido"


_TAMANO_NUM_RE = re.compile(r"\d+(?:\.\d+)?")


def etapa_from_tamano(tamano_pellet_mm: str | None, tipo_presentacion: str | None) -> str | None:
    """Fallback de etapa a partir de tamano de particula, usando las bandas
    de negocio que dio el usuario (no publicadas por ningun competidor,
    criterio propio): Nursery hasta 1.6mm (se mapea a 'precria', que ya
    incluye 'nursery' como sinonimo en _ETAPA_RULES) y Grower desde 1.8mm
    en Pelletizado o 1.9mm en Extruido (se mapea a 'engorde'). Solo se usa
    como ultimo recurso, cuando normalize_etapa()/la descripcion del
    producto no resolvieron nada (ver parsers/nicovita.py) -- por ejemplo
    Nicovita Classic/Katal base, cuya ficha cubre post-larva a mercado
    completo y no distingue etapa por texto.
    Devuelve None (no fuerza un valor) para: tamano_pellet_mm vacio o sin
    numero reconocible; exactamente 1.6mm, porque la propia definicion lo
    da como techo de Nursery Y como tamano tipico de Pre Grower a la vez
    (no hay Pre Grower en el esquema actual, y elegir uno de los dos series
    inventar dato); el hueco entre 1.6 y el arranque de Grower; y cualquier
    tamano >= 1.8/1.9 si no se conoce tipo_presentacion, porque el umbral
    de Grower depende de cual sea."""
    if not tamano_pellet_mm:
        return None
    m = _TAMANO_NUM_RE.search(tamano_pellet_mm)
    if not m:
        return None
    size = float(m.group(0))
    if size < 1.6:
        return "precria"
    if size == 1.6:
        return None
    if tipo_presentacion == "Pelletizado" and size >= 1.8:
        return "engorde"
    if tipo_presentacion == "Extruido" and size >= 1.9:
        return "engorde"
    return None


# Los 4 valores del negocio para el reporte de competencia (mensaje de la
# jefa del usuario, 2026-09-02) -- distintos de ETAPA_VALUES, que se disenaron
# antes de tener ese mensaje y por eso no calzan 1 a 1 con estos 4 terminos.
CLASIFICACION_CAMARON_VALUES = {"Hatchery", "Nursery", "Pre Grower", "Grower"}


def clasificacion_camaron_from_row(
    etapa: str | None,
    tamano_pellet_mm: str | None,
    tipo_presentacion: str | None,
    es_larvicultura: bool = False,
) -> str | None:
    """Clasifica el producto en las 4 etapas que definio la jefa del usuario
    para el reporte de competencia -- Hatchery/Nursery/Pre Grower/Grower --
    columna aparte de `etapa` porque no comparten vocabulario (ver arriba).
    Nombrada `clasificacion_camaron` (antes `etapa_camaron`, renombrada
    2026-09-03 a pedido del usuario) para no confundirla con `etapa`: esta
    no es "una etapa mas" del mismo vocabulario, sino la clasificacion fija
    de 4 casillas que pide el reporte, derivada sobre todo de tamano de
    pellet en vez del texto/categoria de la fuente.

    Hatchery se decide por el propio valor de `etapa` (`"larva"`), no por
    tamano: la jefa la define por tipo de producto ("de laboratorios
    larvarios"), no por una banda de mm, y el unico producto `larva` de los
    datos actuales (Nicovita Origin, 0.3-0.8mm) es justamente un caso donde
    clasificar solo por tamano lo hubiera puesto en Nursery por error.

    `es_larvicultura` (agregado 2026-09-07, division Larvicultura de
    Agripac) es la MISMA idea aplicada por division en vez de por `etapa`:
    a pedido del usuario, CUALQUIER producto de esa division (Larfeed,
    MeM, Mpex, Artemia Cysts...) es Hatchery sin mirar tamano, aunque su
    `etapa` no resuelva a "larva" (ej. Mpex, en estadio "PL1 a PL6", no
    matchea la regla `larva` de `_ETAPA_RULES` con la misma fuerza que un
    "larva"/"hatchery" explicito) y aunque su tamano en micras (100-800um)
    hubiera caido en Nursery por banda. Se revisa ANTES que `etapa=="larva"`
    porque es la senal mas fuerte (division completa, no texto ambiguo por
    producto), pero en la practica nunca compiten: ningun producto fuera de
    Larvicultura tiene este flag en True.

    El resto se deriva de tamano_pellet_mm (y tipo_presentacion para el
    umbral de Grower, que la jefa dio distinto por Pellet/Extruido: 1.8mm
    vs 1.9mm). A diferencia de `etapa_from_tamano` (que deja 1.6mm sin
    resolver porque esa funcion reusa los 6 valores viejos de ETAPA_VALUES,
    donde 1.6mm queda ambiguo entre 2 de ellos), aca 1.6mm SI se resuelve a
    "Pre Grower": al ser una columna dedicada a los 4 terminos de la jefa,
    y ella asocio ese tamano especificamente a Pre Grower ("#4, normalmente
    1.6mm"), no hay conflicto con otro valor que tambien lo reclame.
    Devuelve None para tamano_pellet_mm vacio/sin numero reconocible, el
    hueco entre 1.6 y el arranque de Grower, y Grower si no se conoce
    tipo_presentacion -- no se fuerza un valor sin evidencia."""
    if es_larvicultura:
        return "Hatchery"
    if etapa == "larva":
        return "Hatchery"
    if not tamano_pellet_mm:
        return None
    m = _TAMANO_NUM_RE.search(tamano_pellet_mm)
    if not m:
        return None
    size = float(m.group(0))
    if size < 1.6:
        return "Nursery"
    if size == 1.6:
        return "Pre Grower"
    if tipo_presentacion == "Pelletizado" and size >= 1.8:
        return "Grower"
    if tipo_presentacion == "Extruido" and size >= 1.9:
        return "Grower"
    return None


_TAMANO_RANGE_RE = re.compile(r"(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)")


def parse_particula_range(tamano_pellet_mm: str | None) -> tuple[float | None, float | None]:
    """Convierte tamano_pellet_mm (texto, a veces un rango como "0.5-1.0")
    en un par numerico (particula_min_mm, particula_max_mm), para poder
    promediar/filtrar/graficar por tamano de particula entre empresas --
    algo que la columna de texto no permite tal cual (hallazgo del usuario,
    2026-09-03). Si el texto es un rango, devuelve sus dos extremos; si es
    un solo numero (el caso mas comun), devuelve ese mismo valor en min y
    max -- no hay rango real que partir, y dejar uno de los dos en None
    haria imposible promediar esa fila junto con las que si son rango.
    Devuelve (None, None) si no hay ningun numero reconocible, sin inventar
    un valor que el dato no tiene."""
    if not tamano_pellet_mm:
        return None, None
    m = _TAMANO_RANGE_RE.search(tamano_pellet_mm)
    if m:
        return float(m.group(1)), float(m.group(2))
    m = _TAMANO_NUM_RE.search(tamano_pellet_mm)
    if not m:
        return None, None
    value = float(m.group(0))
    return value, value


# Compartido entre parsers (antes duplicado con una pequena diferencia entre
# nicovita.py y haid.py -- este ya las incluye a ambas) para que Aquaxcel
# use exactamente el mismo criterio (2026-09-02).
# "profil[aá]ctic" se agrego 2026-09-03 (hallazgo real en Agripac): su
# "Linea Profilactica" (Ultra, Ultrapro, Premium Profilactico) describe
# resistencia especifica a "bacterias, virus y parasitos" -- un reclamo
# concreto de prevencion de enfermedad, no marketing generico de "salud"
# (ver test_detect_producto_salud_false_when_text_present_without_marker,
# que a proposito deja en False una mencion suelta de "salud del camaron"
# sin ese reclamo especifico). Confirmado que ningun PDF real de Nicovita/
# HAID ya scrapeado usa esta palabra, asi que el agregado no cambia ninguna
# clasificacion existente de esas 2 empresas.
_DISEASE_MARKER = re.compile(
    r"vibrio|enfermedades?|terap[eé]utic|tratamiento|antibacterian|profil[aá]ctic", re.I
)


def detect_producto_salud(text: str | None) -> bool | None:
    """Detecta si un texto describe funcion terapeutica/de salud (ej.
    tratamiento anti-Vibrio) -- propiedad del producto independiente de la
    etapa del ciclo de vida: un producto de salud puede cubrir cualquier
    tamano/etapa (Nicovita Terap: "post larva hasta tamano de mercado para
    disminuir carga microbiana"; HAID Fitness: "camarones juveniles y
    engorde que... previene enfermedades"; Agripac Linea Profilactica:
    "resistencia a problemas de bacterias, virus y parasitos"). Devuelve
    None solo si no hay texto que revisar; si hay texto y no menciona nada
    de esto, es False con confianza -- no se deja en None solo por falta de
    mencion cuando si se leyo el texto completo."""
    if not text or not text.strip():
        return None
    return bool(_DISEASE_MARKER.search(text))


def empty_record(empresa: str) -> dict:
    """Devuelve un dict con todas las columnas del esquema en None, salvo
    'empresa'. Cada parser llena solo los campos que realmente extrajo."""
    record = {col: None for col in SCHEMA_COLUMNS}
    record["empresa"] = empresa
    return record
