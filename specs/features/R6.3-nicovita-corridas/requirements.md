# R6.3 + R6.4 — Nicovita: corridas reales en los 3 países

> Roadmap: [R6.3, R6.4](../../roadmap.md) · Estado: se marca solo en el roadmap

## Contexto (spec corregida contra la realidad, 2026-11-09)
- **R6.3** pedía quitar Nicovita de `fuentes.INACTIVAS`. Ya está vacío desde el 2026-10-29: se reactivó tras correr sin captcha en los 3 países (comentario en `fuentes.py`). Queda correr Honduras, validar 3 productos y anotar el tiempo.
- **R6.4** pedía comparar con "los CSV guardados el 2026-10-20". Esos CSV no existen: `data/processed/` está en `.gitignore` y ningún commit ni zip los guarda. La foto más vieja disponible es `data.zip` (CSV de Nicovita del **2026-10-29**). Se compara contra esa y contra la copia de antes de esta corrida (2026-11-09).

## Requisitos
- **REQ-1:** `('honduras','nicovita')`, `('ecuador','nicovita')` y `('mexico','nicovita')` están activos (`fuentes.listar(solo_activas=True)`).
- **REQ-2:** Corrida real de Honduras con el ritmo de R6.1: tiempo anotado, sin captcha (o, si aparece, con la copia guardada) y 3 productos validados contra la ficha.
- **REQ-3:** Corrida real de Ecuador y México: diferencias por producto contra el 2026-10-29 (filas nuevas, que faltan y campos cambiados) anotadas en `validation.md`, con la causa de cada cambio.

## Fuera de alcance
- Corregir el parser de Nicovita, salvo una regresión que aparezca en la comparación.
