# R7.4 — Más competidores con catálogo web (solo listar)

Pedido del usuario (2026-11-09). Research web con Codex; acceso con `requests` comprobado por Claude en 7 URL (una consulta cada una, sin scraping). Detalle por país en `src/paises/<pais>/README.md`.

**Ranking para implementar (cada uno, una fase aparte):**
1. **El Pedregal (México):** tabla HTML con nombre, tamaño, proteína. Verificado (200).
2. **Prilabsa (Ecuador, distribuidor):** PDF con texto; Higashimaru, Mackay Marine y Zeigler de laboratorio. Verificado (200).
3. **Balnova (Ecuador) vía Agroshow:** datos parciales (2.0–1.7 mm; 22/28/35 %). Verificado (200).
4. **AQUATEC (México) vía Nutrimentos:** error SSL con `requests`. Pendiente: decidir si se acepta sin verificar el certificado.
5. **NasaFeed/Aquanasa (Panamá):** timeout. Reintentar otro día.

Ya cubiertos: Nutrición Marina = Nutrimar; Malta Texo = Api-Aba; Alimentsa = BioMar; ALCON = Cargill. Sin fuente útil: Oromar, Molinos Champion, Naltech, INVE, Bioalimentar, Avícola Grecia, Honduras y Nicaragua.
