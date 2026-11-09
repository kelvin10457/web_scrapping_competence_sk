# R6.1 + R6.2 — Plan

## Archivos que se tocan
- `src/netutil.py` — constantes de ritmo, `_lentos`, contador de bloqueos por host, `reset_blocked`
- `tests/test_netutil.py` — un test por REQ (con `time.sleep` y `random` simulados)
- `scratchpad/medir_nicovita.py` (fuera del repo) — corrida en frío con cachés en un directorio temporal, sin borrar `data/`

## ¿Cambia la constitución?
Sí: `README.md` § Bloqueos/ritmo y `tech-stack.md` si nombran los tiempos.
