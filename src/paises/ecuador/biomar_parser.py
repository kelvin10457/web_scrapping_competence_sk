"""Parser de BioMar: solo identificacion (empresa, nombre_producto, etapa).
La ficha de producto no publica composicion nutricional ni fisico/funcional
en ningun lado (docs/historico/MEMORY.md) -- el resto de columnas queda explicitamente
None, no se infiere ni se inventa.
"""
from __future__ import annotations

import datetime
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import schema  # noqa: E402


def _extract_nombre(soup: BeautifulSoup) -> str | None:
    h1 = soup.find("h1")
    if not h1:
        return None
    parts = [s.get_text(strip=True) for s in h1.find_all("span")]
    parts = [p for p in parts if p]
    return " ".join(parts) if parts else h1.get_text(strip=True) or None


def _extract_dl_values(soup: BeautifulSoup, label: str) -> list[str]:
    """Devuelve TODOS los valores de un <dt> dado. Algunos productos (ej.
    EXIA Prime) tienen mas de un valor de Etapa dentro del MISMO <dd>
    (dos <a> distintos, ej. "De Engorde" y "De Alevinaje") -- hay que
    detectarlo para no forzar una sola etapa cuando la propia BioMar publica
    mas de una."""
    for dt in soup.find_all("dt"):
        if dt.get_text(strip=True).lower() == label.lower():
            values = []
            for sib in dt.find_next_siblings():
                if sib.name == "dt":
                    break
                if sib.name != "dd":
                    continue
                links = sib.find_all("a")
                if links:
                    values.extend(a.get_text(strip=True) for a in links if a.get_text(strip=True))
                else:
                    text = sib.get_text(strip=True)
                    if text:
                        values.append(text)
            return values
    return []


def parse_product(url: str, html: str) -> dict:
    record = schema.empty_record("BioMar")
    record["fuente_url"] = url
    record["fecha_extraccion"] = datetime.date.today().isoformat()

    soup = BeautifulSoup(html, "html.parser")
    record["nombre_producto"] = _extract_nombre(soup)

    etapa_values = _extract_dl_values(soup, "Etapa")
    # R4.10: todas las etapas que publica la ficha (EXIA Prime: "De Engorde" y
    # "De Alevinaje" -> las dos), igual que Agrizon (R4.5). Modulo deshabilitado.
    record.update(schema.columnas_etapa(schema.detectar_etapas(" ".join(etapa_values))))
    record["_etapas_detectadas"] = True

    return record
