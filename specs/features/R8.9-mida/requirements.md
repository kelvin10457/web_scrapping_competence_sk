# R8.9 — MIDA Panamá como registro oficial

> Roadmap: [R8.9](../../roadmap.md) · Estado: se marca solo en el roadmap

## Contexto
R8.8 encontró dos PDF públicos de MIDA (DINASA) con alimentos registrados: el nacional (`Alimentos-nacionales-vigentes-2026-1.pdf`, tabla con bordes) y el de PGA (`Alimentos-registrados-en-PGA.pdf`, texto sin bordes y con celdas de varias líneas). No tienen columnas de especie, proteína ni tamaño. Hoy Panamá no tiene ninguna fuente en el pipeline.

## Requisitos
- **REQ-1:** Cuando se lee el PDF nacional, entonces se obtiene una fila por registro (`registro`, `nombre_producto`, `empresa_registro`, `vigencia`) y aparecen los 3 AQUANASA y EXCELLENT CAMARÓN.
- **REQ-2:** Cuando se lee el PDF de PGA (sin bordes), entonces cada registro `RA-…` queda en una fila, con el fabricante de varias líneas unido (MATEMAX → `FARALLON AQUACULTURE`) y la fecha de vigencia completa.
- **REQ-3:** Solo pasan los alimentos de camarón: nombre con `CAMAR` o nombre en el cruce curado `MIDA_CAMARON_CURADO` (AQUANASA, MATEMAX, con el motivo anotado). Poliquetos, premezclas y alimentos de otras especies quedan fuera.
- **REQ-4:** Un registro con vigencia anterior a la fecha de corte queda fuera. Si la vigencia no se puede leer, el registro se queda con `vigencia` vacía (no se inventa una fecha).
- **REQ-5:** Los registros MIDA salen con `fuente=mida`, `pais=panama`, `empresa` vacía (ninguna empresa del master está mapeada en Panamá) y `proteina_pct`/`tamano_pellet_mm`/`empaque_kg` vacíos: el `25` de AQUANASA 25 **no** se toma como proteína.
- **REQ-6:** `actualizar()` baja los dos PDF con User-Agent de navegador (los guarda en `data/raw/mida/`, caché de `MAX_DIAS_CACHE`) y agrega los registros al CSV de registros oficiales. Si MIDA falla y no hay copia guardada, se avisa y SENASICA/eaduana se escriben igual.

## Fuera de alcance
- El listado histórico de 2020 (vencido).
- Crear filas en el master o en Power BI (los registros oficiales son complementarios).
- Mapear fabricantes panameños a una `empresa` del master.

## Restricciones de la constitución que más pesan acá
Vacío antes que inferir (proteína del nombre, especie no explícita). Sin servicios pagos; evasión del bloqueo solo con UA de navegador (README § Bloqueos).
