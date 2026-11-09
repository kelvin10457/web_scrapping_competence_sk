# R5.1 — Excel para Power BI (requisitos)

- **REQ-1:** `data/powerbi/<pais>/<empresa>.xlsx` se escribe por cada par (pais, empresa) del master, con exactamente las 16 columnas de la tabla "Excel para Power BI" de `tech-stack.md`, en ese orden. `etapa_competidor`, `empaque_kg`, `fuente_url` y `fecha_extraccion` quedan fuera.
- **REQ-2:** Tipos fijos: `es_producto_de_salud` y `etapa_*` → booleano (vacío = celda vacía); `particula_min_mm`, `particula_max_mm`, `proteina_pct` → número decimal; resto → texto.
- **REQ-3:** Sin transformaciones: los valores vienen tal cual del master (`etapa_skt` ya derivado).
- **REQ-4:** Test de contrato (R5.3 lo amplía): todos los Excel tienen las mismas columnas, orden y tipos.
