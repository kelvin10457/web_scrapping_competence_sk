# R3.7 — `proteina_pct` siempre numérico decimal

> Roadmap: [R3.7](../../roadmap.md) · Estado: se marca solo en el roadmap

## Contexto
Hoy los parsers mezclan tipos: Agripac, Agrizon y Nicovita devuelven texto (`"35"`) y el resto `float`. Además, los regex de Agripac, Agrizon, Haid y Aquaxcel no aceptan coma decimal: un `37,5` se leería como `37`. Los CSV actuales no tienen valores no numéricos (Ecuador 146, Honduras 38 y México 82 filas con proteína), así que el cambio no debería mover ningún valor.

## Requisitos
- **REQ-1:** `schema.normalize_proteina(valor)` devuelve un `float` o `None`. Acepta número, `"35"`, `"37.5"`, `"37,5"` y `"35 %"`. Devuelve `None` si el valor está vacío, no tiene número, tiene más de un número (`"30%, 35%"`) o queda fuera de (1, 100]. Un `0.375` da `None`: no se convierte a 37.5 (no se infiere).
- **REQ-2:** Todos los parsers asignan `proteina_pct` con `normalize_proteina`, así que en todas las fuentes el valor es `float` o `None`. Un test transversal lo comprueba sobre los fixtures reales de cada fuente (Haid y Nicovita con sus PDF de `data/raw/`, y se saltan si no están).
- **REQ-3:** Los valores de los CSV no cambian: el master de cada país regenerado tiene el mismo `proteina_pct` que antes.

## Fuera de alcance
- `registros_oficiales.py` (no es un parser de fuente; ya devuelve `float`).
- La GUI y `merge_human` (congeladas).

## Restricciones de la constitución que más pesan acá
- Vacío antes que inferir: un valor ambiguo o fuera de rango queda `None`.
- Normalizar en el parser con una función de `schema.py`, no al exportar.
