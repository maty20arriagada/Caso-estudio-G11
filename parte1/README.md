# Parte 1 — Estructura del análisis (Python)

Análisis de productividad de la línea del aserradero CMPC Mulchén a partir de los CSV
en `../data/`. Todo es reproducible y los KPIs se calculan como media de las 5 réplicas.

## Cómo ejecutar

```bash
# desde la carpeta Tareas/
python parte1/run_all.py          # corre todo en orden
# o individualmente:
python parte1/00_exploracion.py
```

Requisitos: Python 3.11, `pandas`, `numpy`, `matplotlib` (sin dependencias extra).

## Scripts (orden de ejecución)

| Script | Qué hace |
|---|---|
| `cmpc_utils.py` | Módulo compartido: rutas, carga, calendario/turnos, warm-up, descomposición de estados. |
| `00_exploracion.py` | Perfilado de los 9 CSV (`/explore-data`): formas, nulos, dimensiones. |
| `01_validacion_fallas.py` | Cruza fallas con calendario y estado real → clasificación. |
| `01b_diagnostico_overrun.py` | Resuelve si las fallas “fuera de horario” son overrun u error. |
| `01c_resumen_fallas.py` | Figura-resumen y veredicto de la validación. |
| `02_warmup.py` | Detección del warm-up (Welch) → persiste `output/warmup_days.txt`. |
| `03_disponibilidad.py` | Disponibilidad, utilización, MTBF/MTTR, yield, composición de estados. |
| `04_cuello_botella.py` | Triangulación del cuello de botella + propuesta de mejora. |
| `06_auditoria.py` | Auditoría de consistencia interna (11 verificaciones cruzadas) → `output/audit.json` y `AUDITORIA.md`. |
| `05_dashboard_data.py` | Calcula todas las métricas (por réplica + media/IC95%) → `output/dashboard_data.json`. |
| `05_dashboard_build.py` | Genera `output/dashboard.html` (dashboard interactivo con ECharts, offline). |

## Salidas (`output/`)

- `RESUMEN_PARTE1.md` (en `parte1/`) — informe consolidado.
- **`output/dashboard.html` — dashboard interactivo** (abrir en el navegador; offline). Métricas Factory Physics (disponibilidad FP, t_e/capacidad, utilización FP, ciclo=cola+proceso); filtros de réplica, **producto**, **máquina**, período (Año/Mes/Día) y **warm-up** que recalculan todo; secciones de warm-up, auditoría, cumplimiento de demanda, supuestos y fórmulas con resultado evaluado.
- `output/figuras/*.png` — todas las figuras.
- `output/tablas/*.csv` — KPIs por réplica y resúmenes.
- `output/VEREDICTO_fallas.md` — conclusión de la validación de fallas.
- `output/warmup_days.txt` — warm-up adoptado (compartido por los scripts).

## Resultado en una línea

El **aserradero es el cuello de botella** (utilización 84 %, nunca ocioso, concentra el 82 %
de las fallas, y el patio de trozos crece sin acotarse). La mejor palanca es **extender su
operación** (16 h → 24 h, +50 % de capacidad), con holgura de sobra aguas abajo.
