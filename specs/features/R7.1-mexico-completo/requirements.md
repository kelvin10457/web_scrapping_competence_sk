# R7.1 — México completo con el esquema nuevo

> Roadmap: [R7.1](../../roadmap.md) · Estado: se marca solo en el roadmap

## Requisitos
- **REQ-1:** `pipeline.py --pais mexico` corre las 7 fuentes de México sin errores ni bloqueos.
- **REQ-2:** `data/presentaciones_nuevas.csv` se revisa: cada valor fuera de `TIPO_PRESENTACION_OFICIAL` queda anotado con su causa.
- **REQ-3:** El contrato de Power BI (`tests/test_powerbi_contrato.py`) sigue en verde con los Excel de México regenerados.
