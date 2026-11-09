# R11.2 — Plan
- `src/paises/ecuador/agrizon_hatchery.py`: lee una sola vez la colección en español de Agrizon (`functools.cache`). Contiene `biomasa_artemia`, `megalikuid`, `proteinas_bernaqua` y `completar_proteina`.
- `agripac.run()` completa la proteína; `prilabsa.run()` suma la Biomasa; fuente nueva `megasupply.run()`.
- `agrizon_scraper.fetch_collection_products(collection_url=...)`: BioMar sigue con `/en/`.
