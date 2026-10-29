# Decisiones vigentes

> Una línea por decisión tomada por el usuario, con su fecha. Si una decisión cambia, se tacha la anterior y se agrega la nueva debajo. La evidencia y el contexto completo están en `docs/historico/MEMORY.md` (sección "Decisiones tomadas en conversación con el usuario" y el historial del esquema).

## Método
- **Sin LLM ni APIs pagas**, por costo. Todo con regex o keywords.
- **2026-08-31:** el OCR local (Tesseract) sí está permitido.
- Un parser por empresa, no por producto.

## Esquema
- **2026-09-02:** se quitan `fibra_pct`, `ceniza_pct`, `humedad_pct`, `estabilidad_agua_min` y los campos cualitativos. Marca y submarca van dentro de `nombre_producto`.
- **2026-09-02:** `salud` deja de ser una etapa. Pasa a ser la columna booleana `producto_salud`.
- **2026-09-02:** se agrega la clasificación de 4 etapas de la jefatura (hoy `etapa_skt`), separada de la etapa que publica el competidor.
- **2026-09-03:** `particula_min_mm` y `particula_max_mm` se derivan de `tamano_pellet_mm`, que se mantiene como texto.
- **2026-09-03:** cada CSV tiene un `.xlsx` espejo con columnas numéricas reales (Excel en español corrompe los decimales).
- **2026-09-15:** se quita `grasa_pct`.
- **2026-09-15:** renombres: `etapa` → `etapa_competidor` y `clasificacion_camaron` → `etapa_skt`.
- **2026-10-19:** se agrega `pais` como primera columna. Indica dónde se vende, no dónde se fabrica.
- **2026-10-28:** el destino final es un **Excel por país y empresa** (`data/powerbi/<pais>/<empresa>.xlsx`) para unir en Power BI. Columnas en `tech-stack.md`. Se agregan `empresa` y `etapa_skt` a la lista del usuario.
- **2026-10-28:** la etapa del competidor pasa a 5 booleanos (`etapa_reproductores`, `etapa_larva`, `etapa_precria`, `etapa_post_transferencia`, `etapa_engorde`). `post_transferencia` tiene columna propia.
- **2026-10-28:** `etapa_skt` es una sola columna, calculada por tamaño de pellet (criterio propio de Skretting). En un rango manda el mínimo; sin tamaño, se usa la etapa del competidor como respaldo.
- **2026-10-28:** cortes de `etapa_skt`: menos de 1.6 mm → Nursery; 1.6 mm → Pre Grower; más de 1.6 mm → Grower (1.7 mm es Grower). Se elimina la distinción 1.8 pellet / 1.9 extruido.
- **2026-10-28:** `proteina_pct` va como porcentaje decimal (`37.5`).
- **2026-10-28:** lista oficial de `tipo_presentacion` (ver `tech-stack.md`); `Pelletizado` pasa a `Pellet`. Se normaliza al extraer, no al final. Los valores nuevos no son error: se conservan y se avisan.

## Fuentes
- **2026-09-03:** BioMar solo por Agrizon. biomar.com queda deshabilitado aunque se pierdan productos sin match (los módulos se conservan).
- **2026-10-20:** Nicaragua y Panamá **no** duplican las filas de Honduras. Se cargan a mano.
- **2026-10-20:** HAID y Agripac solo en Ecuador.
- **2026-10-20:** Fase 5 (SENASICA / eaduana) ejecutada como fuente complementaria. Nunca pisa un dato del sitio.
- ~~**2026-10-20:** Nicovita pausada en todos los países (`fuentes.INACTIVAS`).~~
- **2026-10-28:** Nicovita se reactiva con cuidado: pausas aleatorias solo para las páginas problemáticas, con un límite de ≤3 min por país en la primera corrida, sin caché (roadmap R6).
- **2026-10-29:** Nicovita sale de `fuentes.INACTIVAS`: corrió sin captcha en Ecuador (57, 2 min 56 s), México (26) y Honduras (38).
- **2026-10-29:** Pausas de `netutil` más irregulares: corta triangular 1.5–7 s (moda 2.5), larga 15–40 s cada 3–6, reintentos con +0–50 % al azar y nunca menos que `Retry-After`.
- **2026-10-29:** Agrizon (complemento de BioMar) pasa a `netutil.PACED_HOSTS` con las mismas pausas aleatorias que Nicovita, tras responder 429 el 2026-10-28.
- **2026-10-28:** Centroamérica: buscar registros oficiales de cada país; lo que no aparezca se carga a mano con una plantilla.
- No se borran módulos viejos que quedan sin uso.

## Salida
- **2026-09-01:** `master.csv` es snapshot y se sobrescribe. Es provisorio (ver [roadmap](roadmap.md)).
- **2026-10-29:** La prioridad es que los datos se puedan analizar; el dashboard lo arma el usuario y la gerencia no necesita correr el script. La GUI (`gui.py`) queda congelada: no se le agregan funciones nuevas ni se la adapta al esquema nuevo, y tampoco se borra. Las salidas y los avisos van solo por CLI y archivos en `data/`.
