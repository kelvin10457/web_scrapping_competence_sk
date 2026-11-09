# Revisión pendiente (expansion-regional)

> Lista para revisar juntos. Se actualiza después de cada commit. Arriba va el resumen final; abajo, el registro cronológico de decisiones.

## Resumen final
_Se completa al cerrar la corrida (ver CIERRE del pedido)._

## Registro de decisiones y cambios

### Sesión 1 (2026-11-09)

- **Commit `edca063` — docs: ruta del Python en Linux/macOS.** CLAUDE.md ahora lista la ruta de Windows y la de Linux/macOS. Revertir: `git revert edca063`.
- **Reparto:** R5.1–R5.3 y R5.4 los hace Claude; R4.7–R4.9 los hace Codex (plugin `codex:rescue`, en segundo plano), una por vez. Codex no commitea ni toca el roadmap.
- **R5.2, `pais` faltante en `competencia_human.xlsx`:** el archivo no tiene columna `pais`. Se aplica la regla ya existente de `merge_human._with_default_pais` (fila sin país → `ecuador`, PLAN_REGIONAL 2.5). Alternativa descartada: dejarlas fuera del Excel (perdería 5 filas que el usuario cargó). Para revertir: quitar el default y excluir filas sin `pais`.
- **Commit `db5a5d2` — R5.1 + R5.2 (Claude).** `src/powerbi.py` escribe `data/powerbi/<pais>/<empresa>.xlsx` desde `data/master.csv` más `competencia_human.xlsx`. 16 columnas de tech-stack, sin `etapa_competidor`. Se llama desde `pipeline.build_master`. 12 archivos generados (ver `specs/features/R5.1-excel-powerbi/validation.md`).
  - *Decisión:* un valor no vacío que no se puede tipar (ej. `35%`, `desconocido`) queda vacío en el Excel y se imprime un AVISO. Alternativa descartada: fallar la corrida. Revertir: quitar el aviso o cambiar a error.
  - *Decisión:* al escribir, se borran los `data/powerbi/*/*.xlsx` de pares (pais, empresa) que ya no existen. Alternativa descartada: dejarlos (Power BI los seguiría uniendo con datos viejos). Revertir: quitar el `unlink` en `powerbi.escribir_todo`.
  - *Hallazgo de revisión (Codex adversarial-review, 2026-11-09):* los dos puntos de arriba salieron de esa revisión y se aplicaron. Los demás hallazgos: ninguno.
  - *Pendiente:* las filas humanas se agregan sin deduplicar contra el master. Si una fila humana repite una scrapeada, aparece dos veces. Revisar contra `merge_human` (que sí casa por nombre+pais).
- **Commit `c688b30` — R5.3 + R5.4 (Claude).** `tests/test_powerbi_contrato.py` valida los 12 Excel reales; `docs/powerbi.md` tiene la guía y el código M. *No probado en Power BI Desktop* (no disponible aquí): el código M queda sin ejecutar.
