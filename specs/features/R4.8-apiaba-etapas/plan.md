# R4.8 — Plan

1. Tests primero con apiaba_dorado40.html, apiaba_dorado35.html y apiaba_raceways.html existentes.
2. Extraer título y párrafos del contenido del producto, sin tarjetas relacionadas.
3. Aplicar detectar_etapas y columnas_etapa, marcar _etapas_detectadas.
4. Correr solo `.venv/bin/python -m pytest -q -x tests/test_apiaba*.py` y validar los tres productos offline.
