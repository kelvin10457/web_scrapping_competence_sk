# RONDA2_REGIONAL.md — Segunda ronda de la expansión regional

> Continúa `PLAN_REGIONAL.md`. Siguen vigentes sus reglas de §4, el manejo de bloqueos de §5, los defaults de §6 y el modo de trabajo eficiente de §7.2.
> Agregar los ítems de abajo al checklist de `PROGRESO_REGIONAL.md` como **"R2.x"** y trabajarlos en este orden. Cada ítem se cierra con su test y su commit.

## R2.0 — Nicovita: pausada (decisión del usuario)
- No correr ni tocar el scraper de Nicovita en ningún país. Tampoco gastar turnos en el captcha.
- Los CSV de Nicovita que ya están en `data/processed/*/nicovita.csv` **se dejan como están**, para que `master.csv` los siga incluyendo.
- Agregar en `fuentes.py` una marca `activa=False` para los tres (pais, nicovita). La corrida sin argumentos (`pipeline.py` solo) se los salta, pero se pueden correr a mano con `--empresa nicovita`.
- En `PROGRESO_REGIONAL.md`, marcar esos tres pares como `pausado (usuario)`. Esto cuenta como estado final para §7.3.

## R2.1 — Registro de conflictos (base compartida por R2.2 y R2.3)
Cuando una fuente da **más de un valor** para un mismo campo, no se deja la celda vacía. Se elige un valor con una regla fija y se deja constancia:
- Crear `schema.resolver_campo(candidatos: list[tuple[valor, origen]], reglas) -> (valor, regla_aplicada)`. Es una función pura, sin red, y debe tener test.
- Cada vez que se resuelve un conflicto, se agrega una fila a `data/processed/{pais}/_conflictos.csv` con estas columnas: `pais, empresa, nombre_producto, campo, valor_elegido, regla, candidatos, fuente_url, fecha_extraccion`.
- **El esquema principal no cambia.** `build_master()` debe ignorar los archivos que empiezan con `_`, y además hay que juntarlos todos en `data/conflictos.csv`.
- Así, si alguien quiere corregir un valor elegido, lo hace con la GUI (`competencia_human`) como cualquier otra corrección.

## R2.2 — Vimifos: una celda con varias proteínas
Hoy esa celda queda vacía. El cambio es que **se separa en varias filas**, una por SKU. La regla es determinística:
1. Extraer todos los valores de proteína de la celda con el regex `(\d+(?:[.,]\d+)?)\s*%` y conservar el orden.
2. Ver cuántos calibres trae la misma fila (`M`) frente a cuántas proteínas (`N`):
   - **Si `M == N`:** emparejar 1 a 1 en el orden publicado y generar `N` filas.
   - **Si `M` es 0 o 1:** generar `N` filas, cada una con una proteína y el mismo calibre.
   - **Si `M ≠ N` y los dos son mayores que 1:** generar `N` filas, cada una con una proteína y con `tamano_pellet_mm` como el texto original completo. Registrar el caso en `_conflictos.csv` con la regla `calibre_no_emparejable`.
3. Antes de emparejar, revisar en la página si el texto ya asocia cada proteína a un calibre o a una etapa (por ejemplo, `"35% (2.0 mm)"`). Si lo asocia, esa asociación explícita manda sobre el orden.
4. Agregar un fixture con una celda real de varias proteínas y un test que verifique cuántas filas salen y cómo quedan emparejadas.

## R2.3 — Api-Aba: proteína que se contradice (ej. Dorado 35%: el título dice 35 y el análisis dice 40)
No se deja vacía. Se aplica `resolver_campo` con esta jerarquía, y se usa la primera regla que decida:
1. **Coincidencia:** si dos o más fuentes de la misma página dan el mismo valor, se toma ese (`regla=coincidencia`).
2. **Copia detectada:** si el bloque de análisis de este producto es **igual, normalizado,** al de otro producto del mismo sitio, y el título de ese otro producto tiene el valor del análisis (por ejemplo, el análisis de "Dorado 35%" es idéntico al de "Dorado 40%"), entonces el análisis está copiado del otro producto. Se toma el valor del título (`regla=analisis_copiado_de:<otro producto>`).
3. **Default:** se toma el **número del nombre comercial** (`regla=nombre_comercial`). Motivo: el nombre identifica al SKU que se vende y se registra con esa proteína, mientras que las tablas de análisis se copian y pegan entre productos con frecuencia.

Los tres casos quedan en `_conflictos.csv` con todos los candidatos. Usar esta misma función para cualquier otra empresa que tenga el mismo problema; no escribir lógica aparte por empresa.
Test: fixture de Dorado 35% y Dorado 40%, verificando que la regla aplicada y el valor elegido sean los esperados.

## R2.4 — Nutrimar (México): sí tiene fichas técnicas
Hoy el scraper solo trae nombres. Esto es lo que encontré al revisar el sitio el 2026-10-19:
- El sitio está hecho en **Wix**. Las páginas de producto son `https://www.nutrimar.mx/engorda-nutrimar`, `/larvario-zeigler`, `/maduración-zeigler`, `/maternidad-zeigler` y `/probioticos-zeigler`.
- En "Engorda" las variantes (Extensivo, Semi-intensivo, Intensivo, Vpak) aparecen como **imágenes** en `static.wixstatic.com/media/...`. Lo más probable es que las fichas sean imágenes o PDF enlazados desde las subpáginas.

Qué hacer:
1. Buscar en el HTML estático (con `requests`) los enlaces a `.pdf` y las URLs de `static.wixstatic.com/media/`. Si el HTML no los trae, buscarlos en el JSON que Wix deja embebido en la página (`<script type="application/json">` o `wix-warmup-data`). **No usar Playwright.**
2. Si la ficha es un PDF con texto, usar `pdfplumber`. Si es una imagen o un PDF escaneado, usar el **mismo OCR con Tesseract (español) que ya usa HAID**: reutilizar esa función en vez de copiarla.
3. En los productos Zeigler que distribuye Nutrimar, poner `empresa = "Zeigler"` y en `fuente_url` la página de Nutrimar. En la línea propia, poner `empresa = "Nutrimar"`.
4. Validar 3 productos contra la ficha real. Si el OCR da un número dudoso (fuera de 20–60 % de proteína o fuera de 0.1–4 mm de calibre), el campo queda en `null` y el caso se registra en `_conflictos.csv` con la regla `ocr_fuera_de_rango`.

## R2.5 — Nicaragua y Panamá: candidatos nuevos (ya revisados, solo reconfirmar con 1 request cada uno)
Revisé estos candidatos el 2026-10-19. **No hay que investigarlos de nuevo**, solo confirmar que la URL sigue igual y anotar el resultado:

| País | Candidato | Lo que encontré | Acción |
|---|---|---|---|
| Nicaragua | Vitali Alimentos | La URL `vitalialimentos.com/feed/` es el feed RSS de noticias, no un catálogo. La empresa declara alimento acuícola, pero solo menciona Guatemala y El Salvador, y no aparece ningún producto de camarón. | Revisar la home una vez. Si no hay catálogo de camarón: `sin_fuente_publica`. |
| Nicaragua | Disagro (AQUAPLUS) | `/linea-acuicola/` solo trae insumos (Ferti-Plus, Silica-Plus, AQUABIOTIC). **No es balanceado.** | `descartado (no fabrica balanceado)`. |
| Panamá | INASA / Larro (Grupo Calesa) | `/inasa/` confirma que tiene una línea de camarón, pero sin productos. `/balanceados/` solo tiene PDF de bovinos, aves, cerdos y equinos. `/camaron/` es camarón para consumo (Camaco). | `sin_fuente_publica`. Anotar el contacto info@grupocalesa.com para carga manual. |
| Panamá | Rivoflavia Inc., Nutrición Animal S.A. | Solo aparecen en registros históricos de la FAO, sin sitio web. | `sin_fuente_publica`. |
| Panamá | Agromarina del Pacífico | Importador o distribuidor ("Optiline 35%", según registros de importación de pago). | `sin_fuente_publica`. Anotar la marca "Optiline" para carga manual. |
| — | Agro La Hacienda (Camaronina) | Su teléfono es de Colombia (+57) y no menciona NI ni PA. Solo publica nombres, sin especificaciones. | `fuera_de_alcance (país no objetivo)`. |
| — | Balnova | `balnova.com` redirige a `adm.com`: la marca ya no tiene sitio propio. | `descartado (sitio inexistente)`. |

Nicaragua y Panamá siguen con **carga manual por la GUI**. Eso ya es un estado final válido según §7.3.

## Criterio de terminado de la ronda 2
- R2.0 a R2.5 cerrados en `PROGRESO_REGIONAL.md`.
- Vimifos y Api-Aba sin celdas de proteína vacías por contradicción o por varios valores (verificarlo con un conteo de nulos antes y después, y mostrar la salida).
- Nutrimar con ≥3 productos validados con proteína o calibre, o marcado `bloqueado` con el motivo.
- `pytest -q` en verde, `python src/pipeline.py` sin errores y `data/conflictos.csv` generado.
- Cierre en `PROGRESO_REGIONAL.md`: cuántos conflictos se resolvieron y con qué regla.
