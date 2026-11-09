# R8.8 — Listados ministeriales de alimentos para camarón

Investigación: **2026-11-09**, rama comprobada: `expansion-regional`. Solo investigación y este documento; sin implementación ni commits.

## Alcance y criterio de verificación

Se leyeron los cuatro README de `src/paises/{panama,honduras,nicaragua,mexico}`. Se consultaron buscadores y páginas/PDF puntuales, sin recorrer catálogos completos ni eludir restricciones. Ecuador queda fuera. SENASICA México ya está cubierto por `data/raw/senasica/productos_regulados_registrados.xlsx`: sus republicaciones no cuentan como fuentes adicionales.

**Acceso** describe la herramienta web, no una descarga local comprobada. Una prueba puntual con `requests` a MIDA falló por resolución DNS del entorno, sin respuesta HTTP; por eso la viabilidad futura de `requests + pdfplumber` es una recomendación, no una integración validada. No se guardaron PDF ni archivos auxiliares.

**Conteo:** registros de producto distintos, no líneas de texto ni presentaciones comerciales. Se separan nombres que explicitan camarón, productos vinculados mediante otra fuente y candidatos sin especie confirmada. `Sin verificar` nunca significa cero. La extracción de texto de PDF une algunas filas y corta fabricantes; requiere revisión al implementar. No se verificó con un parser local ni OCR.

## Panamá — listados encontrados

| País | Organismo / listado | URL exacta | Formato | Fecha o vigencia | Columnas disponibles | N.º de filas de camarón | Empresas de camarón | Acceso | Utilidad para Excel y motivo |
|---|---|---|---|---|---|---|---|---|---|
| Panamá | MIDA / alimentos nacionales | https://mida.gob.pa/wp-content/uploads/2023/08/Alimentos-nacionales-vigentes-2026-1.pdf | PDF texto, 7 páginas | Portal: actualizado a 2026; vigencia por registro | Entrada, registro, producto, clasificación, fabricante, origen, expedición, vigencia. Sin columnas de especie, proteína o tamaño | **1 explícita**; **3 AQUANASA candidatas**, especie sin verificar por SKU | Avícola Grecia; Nutrición Animal como candidata | **ok** | **Alta** para descubrir competidores locales; media para completar características técnicas |
| Panamá | MIDA / alimentos registrados en PGA | https://mida.gob.pa/wp-content/uploads/2026/01/Alimentos-registrados-en-PGA.pdf | PDF texto, 3 páginas | Página publicada 13-01-2026; fechas individuales | Registro, producto, clasificación, fabricante, origen, expedición, vigencia. Sin especie, proteína ni tamaño | **0 explícitas; 1 identificada por cruce: MATEMAX** | Farallón Aquaculture | **ok** | **Alta** para descubrimiento por cruce con catálogo; faltan características nutricionales |
| Panamá | MIDA / listado histórico mixto | https://mida.gob.pa/wp-content/uploads/2020/05/Alimentos-registrados.pdf | PDF texto, 19 páginas | Histórico: contiene vencimientos 2017–2022 en las filas examinadas; no acredita vigencia actual | Registro, producto, fabricante, origen, vigencia. Sin especie, proteína ni tamaño dedicados | **sin verificar** el total; se abrió parcialmente y se localizaron coincidencias | Microfeed; Nutrición Animal como candidata | **ok** | **Baja** para Excel vigente; media para descubrir antecedentes de fabricantes e importados |

### Evidencias de producto

Del [PDF nacional](https://mida.gob.pa/wp-content/uploads/2023/08/Alimentos-nacionales-vigentes-2026-1.pdf):

| Página | Registro | Producto | Fabricante | Expedición → vencimiento |
|---|---|---|---|---|
| 4 | RA-2447-23 | EXCELLENT CAMARÓN | Avícola Grecia, S.A. | 10-04-2023 → 10-04-2028 |
| 1 | RA-2278-25 | AQUANASA 25 | Nutrición Animal, S.A. | 30-05-2025 → 30-05-2030 |
| 1 | RA-2279-25 | AQUANASA 30 | Nutrición Animal, S.A. | 30-05-2025 → 30-05-2030 |
| 1 | RA-2280-25 | AQUANASA 35 | Nutrición Animal, S.A. | 30-05-2025 → 30-05-2030 |

Los números del nombre AQUANASA no se convierten automáticamente en proteína. Hay registros vencidos durante 2026 dentro del archivo titulado «vigentes»; filtrar por fecha individual. Sea Technology también figura con poliquetos: alimento natural, excluido del conteo de balanceados.

En [PGA, página 3](https://mida.gob.pa/wp-content/uploads/2026/01/Alimentos-registrados-en-PGA.pdf), **RA-2550-25, MATEMAX**, fabricante Farallón Aquaculture, Panamá, expedido 09-12-2025 y vigente hasta 09-12-2030. El registro no identifica especie; el [catálogo comercial de Sea Technology](https://seatechpanama.com/wp-content/uploads/2021/10/Catalogos-Sea-Technology-INC-Alimentos.pdf), página física 4 / impresa 6, vincula ese nombre con reproductores de camarón en maduración. Es un cruce por nombre comercial, no una columna de especie del ministerio. La revisión textual de las tres páginas no encontró otros nombres explícitos de camarón.

En el [histórico](https://mida.gob.pa/wp-content/uploads/2020/05/Alimentos-registrados.pdf), página 10, aparece **RAA-2245-09, MICROMIX VITAMINAS CAMARÓN, Microfeed, S.A.**, vencimiento 02-11-2019: premezcla, no alimento completo. Página 16: AQUANASA 25/30/35/40/45 con vencimiento 13-04-2020. No trasladar 40/45 al catálogo vigente. El listado mezcla origen nacional y extranjero —por ejemplo, Vetanco/Argentina—, pero eso no prueba registros de importación vigentes en 2026. No se contó todo el documento ni se atribuyeron especies a productos genéricos.

### ¿Hay un listado MIDA de importados vigentes?

**No se localizó uno verificable en esta búsqueda.** Eso no demuestra que no exista. La ruta oficial [Registros DINASA](https://mida.gob.pa/direcciones/direccion-nacional-de-salud-animal/registros/) enlaza los dos listados actuales anteriores, un formulario de importados y documentos regulatorios. «Productos registrados» lleva a una página que describe productos **químicos**, no a otro padrón de alimentos. PGA no debe etiquetarse como listado de importados: los orígenes revisados son Panamá.

| Ruta comprobada | URL exacta | Resultado / acceso | Consecuencia |
|---|---|---|---|
| MIDA, formulario de importados | https://mida.gob.pa/documentos/formulario-de-alimentos-importados/ | **timeout** al abrir; índice describe un formulario, publicado 29-08-2024 | No es evidencia de un listado; columnas, filas y empresas: **sin verificar** |
| MIDA, productos registrados | https://mida.gob.pa/documentos/productos-registrados/ | **ok**, HTML; descripción: químicos actualizados a 2026 | Descartado como listado de balanceados |
| APA, inicio | https://apa.gob.pa/ | **timeout** al abrir; contenido indexado menciona acreditación de importadores y trámites | El trámite no demuestra acceso público a un padrón; no se inició sesión |
| APA, consultas | https://apa.gob.pa/consultas/ | **502**, sin verificar contenido actual | No se clasificó como ausencia de registros |
| APA, aplicaciones | https://apa.gob.pa/aplicaciones-en-linea/ | **502** | Sin listado descargable verificado |
| APA, menú de registro | https://sit.apa.gob.pa/RegistroV2/MenuRegistro.aspx?AspxAutoDetectCookieSupport=1 | **bucle de redirección**; índice distingue consumo humano/animal | No se atribuye un login observado; filas y empresas: **sin verificar** |

## Honduras — SAG / SENASA

No se confirmó un listado público de productos de alimentación animal con filas de camarón. Se buscaron combinaciones de `listado`, `piensos`, `productos registrados`, `alimentación animal`, `consulta` y `camarón` en los dominios SAG y SENASA.

| País | Organismo / recurso | URL exacta | Formato | Fecha o vigencia | Columnas | Filas de camarón | Empresas | Acceso | Utilidad para Excel |
|---|---|---|---|---|---|---|---|---|---|
| Honduras | SAG / dependencias | https://sag.gob.hn/dependencias/ | HTML | Sin vigencia de productos | Directorio institucional, no registros comerciales | sin verificar; no listado de productos | sin verificar | **ok** | **Baja**; orienta a SENASA |
| Honduras | SENASA / Control de Productos Veterinarios | https://senasa.gob.hn/2022/10/26/depto-de-control-de-productos-veterinarios/ | HTML | Ruta fechada 26-10-2022 | La página abierta no ofrece tabla de productos ni descarga de piensos | sin verificar | sin verificar | **ok** | **Baja**; sin datos extraíbles identificados |
| Honduras | SENASA / GER Salud Animal | https://ger.senasa.gob.hn/servicios/salud-animal | HTML / aplicación | Sin vigencia verificable | Índice: servicios, objeto y tipo de servicio; categoría de alimentación animal. Apertura: solo «Loading…» | sin verificar | sin verificar | **ok** para HTML; contenido dinámico **sin verificar** | **Baja actualmente**; no se confirmó consulta pública ni exportación |

El [GER describe la gestión de registros](https://ger.senasa.gob.hn/acerca-del-ger), no promete un padrón público descargable. No se observaron captcha ni 403 en estas rutas; tampoco se comprobó que un login sea el obstáculo. Las normas de registro y los directorios de granjas/exportadores no se cuentan como listados de alimentos.

## Nicaragua — MAG / IPSA

Se revisaron las secciones oficiales de alimentación animal y control de insumos, además de búsquedas dirigidas a MAG/IPSA. No se confirmó un padrón de piensos con camarón.

| País | Organismo / recurso | URL exacta | Formato | Fecha o vigencia | Columnas | Filas de camarón | Empresas | Acceso | Utilidad para Excel |
|---|---|---|---|---|---|---|---|---|---|---|
| Nicaragua | MAG / inicio | https://www.mag.gob.ni/ | HTML previsto; contenido sin verificar | sin verificar | sin verificar | sin verificar | sin verificar | **502**; variante https://mag.gob.ni/ no accesible por la herramienta | **Baja**; sin listado comprobado |
| Nicaragua | IPSA / alimentación animal | https://www.ipsa.gob.ni/SALUD-ANIMAL/Registro-y-Control-de-Insumos-Pecuarios/Registro-de-Establecimientos-y-Productos-Utilizados-en-la-Alimentaci%C3%B3n-Animal | HTML | Sin corte de registros publicado | Enlaces de requisitos, formularios de registro y renovación; sin tabla de productos | sin verificar; no listado encontrado | sin verificar | **ok** | **Baja**; trámites, no inventario |
| Nicaragua | IPSA / control de insumos pecuarios | https://www.ipsa.gob.ni/SALUD-ANIMAL/Registro-y-Control-de-Insumos-Pecuarios | HTML | Sin corte verificable | Contactos y trámites; enlace a listado de expendios menores | sin verificar | sin verificar | **ok** | **Baja**; el enlace inferior merece verificarse, pero no demuestra un catálogo de piensos |
| Nicaragua | IPSA / productos para expendios menores | https://www.ipsa.gob.ni/Portals/0/3%20Salud%20Animal/Registro%20Veterinario/Registro%20y%20Control%20de%20Insumos%20Pecuarios/Documentos/Lista%20de%20Productos%20Autorizados%20para%20Venta%20en%20Expendios%20Menores.pdf | PDF; texto/imagen **sin verificar** | sin verificar | sin verificar | sin verificar | sin verificar | **502** | **Baja hasta verificar**; no asumir que incluye alimento balanceado |

El enlace `gofile.me` en IPSA corresponde a un videotutorial según la propia página, no a un listado. No se descargó. Las listas de insumos agrícolas/fertilizantes y los manuales acuícolas tampoco acreditan productos balanceados registrados.

## México — solo alternativas adicionales

No se encontró un listado adicional confirmado de alimentos para camarón fuera de la familia SENASICA ya cubierta. Se buscaron registros de balanceados en SADER y se inspeccionó un reporte oficial que menciona camarón para evitar confundir estadísticas con productos comerciales.

| País | Organismo / recurso | URL exacta | Formato | Fecha o vigencia | Columnas | Filas de camarón | Empresas | Acceso | Utilidad para Excel |
|---|---|---|---|---|---|---|---|---|---|---|
| México | SADER / datos abiertos | https://www.agricultura.gob.mx/datos-abiertos/sader | HTML, enlaces a varios formatos | Página indexada: 27-07-2016; vigencia de un padrón de alimentos sin verificar | Índice de archivos; no se identificó un listado adicional pertinente | sin verificar | sin verificar | **timeout**; solo índice de búsqueda disponible | **Baja**; no hay fuente complementaria comprobada |
| México | SADER / DGSIAP, industria agroalimentaria | https://nube.agricultura.gob.mx/industriaAgroalimentaria/julio2026.php | HTML | Julio 2026 | Clases/productos estadísticos, unidades, valores/volúmenes y variaciones; sin registro ni fabricante comercial | **0 registros comerciales**; menciona camarón agrupado con otros animales | Ninguna identificada en esa categoría | **ok** | **Baja**; agregado industrial, no padrón sanitario |
| México | SENASICA / candidato «Productos alimenticios vigentes» | https://www.datos.gob.mx/dataset/productos_alimenticios_vigentes | HTML de catálogo previsto; archivo exacto y formato sin verificar | sin verificar | sin verificar | sin verificar | sin verificar | **403**, se detuvo | **Baja / fuera de prioridad**: pertenece a SENASICA; la descripción indexada de ese título refiere especies terrestres |

La URL del último candidato se probó directamente; el 403 impide confirmar su ficha o descarga. No se la presenta como un listado nuevo encontrado. La [ficha de productos regulados y registrados](https://www.datos.gob.mx/dataset/productos_regulados_registrados) apareció en búsqueda con recursos CSV, pero no se descargó ni se cuenta como adicional: coincide temáticamente con la fuente que el usuario declaró cubierta. No se hizo una auditoría nueva del XLSX existente.

## Qué cambia respecto de Descubrimiento R8.x

| README leído | Conclusión previa | Conclusión de esta revisión |
|---|---|---|
| `src/paises/panama/README.md`, R8.5 | No aparecía listado público MIDA/APA; nada que implementar. Encabezado además negaba fabricante local identificado | **Debe corregirse esa conclusión en una fase posterior**: hay dos PDF públicos de MIDA útiles como fuentes complementarias. Este trabajo no modifica el README |
| `src/paises/honduras/README.md`, R8.1 | No aparecía registro público; portal pendiente | Se mantiene **no localizado/verificado**. Se concretó la URL GER y su limitación de lectura dinámica; no corresponde afirmar inexistencia |
| `src/paises/nicaragua/README.md`, R8.3 | «IPSA no publica un listado» | Reformular como **no se localizó un listado de piensos accesible**: hay secciones oficiales y un listado de expendios menores cuyo contenido no pudo abrirse |
| `src/paises/mexico/README.md` | Catálogos de fabricantes y competidores R7.4 | **No contiene sección Descubrimiento R8.x** en la copia leída. No se atribuye una conclusión ausente. Sin fuente ministerial adicional confirmada |

## Competidores y sitios con fichas surgidos del cruce

| Empresa / rol | Sitio o ficha exacta | Qué se comprobó | Acceso / utilidad |
|---|---|---|---|
| **Farallón Aquaculture / MATEMAX**, fabricante; **Sea Technology**, proveedor con catálogo | https://seatechpanama.com/wp-content/uploads/2021/10/Catalogos-Sea-Technology-INC-Alimentos.pdf | Catálogo PDF texto público: producto para maduración de reproductores de camarón; cajas de 1 y 2 kg, baldes de 10 kg; descripción de dieta extruida semihúmeda. No se verificaron porcentajes nutricionales ni diámetro. Su presencia comercial no convierte al proveedor en fabricante | **ok PDF**; https://seatechpanama.com/ dio **timeout**. **Media**, útil para etapa/empaque. Nuevo frente frente a los README revisados |
| **Nutrición Animal / NasaFeed / AQUANASA** | https://nasafeed.com/files/Ficha-Tecnica-Linea-Premium-Aquanasa.pdf | URL ya mencionada en R7.4; no se pudo abrir en esta revisión. Datos técnicos y correspondencia exacta de cada SKU: **sin verificar** | **timeout PDF e inicio** https://nasafeed.com/. **Media potencial**; no es descubrimiento nuevo frente a R7.4 |
| **Avícola Grecia / Excellent Camarón** | Sitio propio y ficha pública: **sin verificar; no encontrados** | Prospecto del padrón, ya mencionado en R7.4. No se inventa un sitio ni se asigna una marca ajena | **Alta para descubrir fabricante; baja para ficha técnica** |
| **Microfeed**, premezclas | Sitio/ficha específica de camarón: **sin verificar; no encontrados** | Antecedente histórico, sin vigencia actual comprobada; no es un balanceado completo | **Baja**; no incorporar como competidor vigente automáticamente |

**No surgió un fabricante nuevo con ficha nutricional completa propia verificada.** Sí surgió una combinación accionable nueva: fabricante Farallón + catálogo técnico comercial de Sea Technology para MATEMAX. El registro de [marca MATEMAX en el boletín oficial MICI de 2017](https://mici.gob.pa/wp-content/uploads/2021/06/2017-12-bo348-22-12-2017.pdf), localizado en el índice, también asocia Farallón y nutrición de reproductores; no se usó como prueba de vigencia sanitaria ni de composición.

## Ranking de implementación complementaria

1. **MIDA Panamá, PDF nacional — implementar primero.** Descarga puntual con `requests`, extracción con `pdfplumber`, identificación por registro y producto; conservar URL y fechas. Los campos técnicos ausentes deben quedar vacíos. Revisar candidatos con documentación de fabricante antes de clasificarlos como camarón.
2. **MIDA Panamá, PDF PGA — implementar junto al anterior.** Mismo mecanismo; permitir una tabla curada de equivalencias producto/especie sustentada en fichas externas. Validar visualmente filas con fabricantes truncados y deduplicar por registro, sin suponer que PGA reemplaza el listado nacional.
3. **Catálogo Sea Technology — enriquecimiento comercial puntual.** `requests + pdfplumber`; aporta etapa y presentación, no un padrón ministerial. Mantener fabricante y distribuidor separados. Por ahora no derivar proteína ni tamaño del lenguaje promocional.
4. **Histórico MIDA — solo descubrimiento y revisión manual.** No alimentar el Excel vigente desde vencimientos antiguos. Revisar fabricante y renovación antes de elevar cualquier hallazgo.
5. **Honduras GER, Nicaragua IPSA y México adicional — no implementar todavía.** Falta un listado público comprobado; registrar los pendientes de acceso sin evadirlos. Los errores de red no justifican inventar conteos ni declarar ausencia absoluta.

`openpyxl` sería apropiado para un XLSX oficial adicional si se encuentra; **ninguno fue confirmado en esta investigación**. No duplicar SENASICA ni copiar catálogos entre países como evidencia de distribución. La implementación propuesta debe verificar acceso de descarga en un entorno con red habilitada y validar los PDF contra unas pocas filas conocidas antes de integrarlos al Excel.

## Verificación de descarga (2026-11-09, Claude)

Desde este entorno (Linux, red del usuario) `mida.gob.pa` **no entrega los PDF**: el balanceador F5 BigIP acepta TCP y empieza el handshake TLS, y luego corta la conexión (`curl: (56) Connection reset by peer`; `requests`: `RemoteDisconnected`). HTTP en el puerto 80 solo redirige a HTTPS. El resto de la red funciona (google.com → 200). No se reintentó con otros clientes ni proxies (README § Bloqueos).

**Actualización (mismo día):** el corte depende del User-Agent. Con `Mozilla/5.0` a secas o `competence-scraper/1.0` el F5 resetea; con un User-Agent completo de navegador Chrome responde **200**. Tras la decisión del usuario de permitir evadir bloqueos (`specs/decisiones.md`, 2026-11-09), se bajaron los dos PDF a `data/raw/mida/`:

| Archivo | Bytes | Páginas | Tabla con `pdfplumber` |
|---|---|---|---|
| `Alimentos-nacionales-vigentes-2026-1.pdf` | 207 369 | 7 | sí: Entrada, N° de Registro, Nombre del producto, Clasificación oficial, Fabricante, País de origen, Expedido, Vigencia |
| `Alimentos-registrados-en-PGA.pdf` | 139 332 | 3 | `extract_tables()` no detecta tabla en p. 1; hay que parsear por texto/palabras. Fabricante partido en dos líneas (`FARALLON` / `AQUACULTURE,`) |

Verificado contra el PDF: RA-2278/2279/2280-25 AQUANASA 25/30/35 (Nutrición Animal, ALIMENTO COMPLETO, 30-05-2025 → 30-05-2030), RA-2447-23 EXCELLENT CAMARÓN (Avícola Grecia, ALIMENTO BALANCEADO, 10-04-2023 → 10-04-2028), RA-2550-25 MATEMAX (Farallón Aquaculture, ALIMENTO COMPLETO, 09-12-2025 → 09-12-2030) y RA-1350-24 poliquetos de Sea Technology (excluido). Coincide con lo descrito arriba.

Consecuencia: la integración `requests + pdfplumber` **es viable** con User-Agent de navegador (hoy `registros_oficiales.py` y `diagnostico.py` usan `competence-scraper/1.0`, que es bloqueado). Las fechas vienen en texto (`30 DE MAYO DE 2025.`, a veces con punto final) y hay que normalizarlas en el parser.
