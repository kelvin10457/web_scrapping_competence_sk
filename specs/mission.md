# Misión

## Para qué existe

Para que la gerencia de Skretting pueda **compararse contra la competencia en Power BI**: qué alimento para camarón vende cada empresa, en qué país, para qué etapa, con qué proteína, de qué tamaño de pellet y en qué presentación.

El proyecto genera **un Excel por país y empresa** (`data/powerbi/<pais>/<empresa>.xlsx`), con columnas idénticas y tipos fijos. Esos archivos se unen en Power BI. Al tener archivos separados, si una fuente falla o trae datos raros, el error queda aislado en su propio archivo y no contamina el resto.

## Para quién

- **Gerencia**: consume el reporte de Power BI armado con estos Excel.
- **Quien arma el reporte de Power BI** (el usuario): corre el script, une los Excel y avisa cuando algo no cuadra.
- **Equipo comercial**: corre la app de escritorio (`.exe`) y carga a mano lo que no está publicado en internet.

## Alcance

| Territorio | Países | Cómo se obtienen los datos |
|---|---|---|
| Ecuador | ecuador | Sitios web y fichas PDF de los competidores |
| México | mexico | Sitios web + registro oficial SENASICA. Se trabaja como territorio separado |
| Centroamérica | honduras, nicaragua, panama | Nicovita (Honduras), registros oficiales de cada país y carga manual |

`pais` es el país donde **se vende** el producto, no donde se fabrica.

**Fuera de alcance:** Skretting (es la empresa del usuario), fuentes de pago (ImportGenius, Volza, etc.) y atributos de marketing.

## Principios innegociables

1. **No inventar ni inferir valores.** Si la fuente no publica un dato, queda vacío. Una celda vacía es mejor que un valor adivinado.
2. **Normalizar en el origen, no al final.** Cada valor se lleva al vocabulario oficial en el momento de extraerlo (una función compartida en `schema.py`). El Excel de Power BI es solo una selección de columnas, sin transformaciones de último momento.
3. **Avisar lo desconocido, no esconderlo.** Si aparece un valor que no está en el vocabulario oficial (por ejemplo, una presentación nueva), se conserva tal cual y se avisa al final de la corrida.
4. **Trazabilidad.** Internamente, cada fila guarda `fuente_url` y `fecha_extraccion`. Los conflictos entre valores se resuelven con reglas fijas y quedan registrados.
5. **Costo cero por corrida.** Nada de LLM ni APIs pagas. OCR local sí.
6. **Validar contra la fuente real.** Antes de cerrar una fase de scraping se comparan ≥3 productos contra la ficha o la página real.
7. **Respetar los sitios, sin hacer esperar al usuario.** Pausas aleatorias solo donde hay captcha, caché agresiva y un presupuesto de tiempo por corrida. Los bloqueos no se evaden.
8. **Que lo corra cualquiera.** Tiene que funcionar como `.exe`, sin navegador headless.
