"""
run_all.py - Ejecuta toda la Parte 1 en orden, de forma reproducible.
Uso:  python parte1/run_all.py
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = [
    "00_exploracion.py",        # perfilado / explore-data
    "01_validacion_fallas.py",  # fallas vs calendario y estado
    "01b_diagnostico_overrun.py",
    "01c_resumen_fallas.py",
    "02_warmup.py",             # warm-up (Welch) -> persiste warmup_days.txt
    "03_disponibilidad.py",     # disponibilidad / utilizacion / yield
    "04_cuello_botella.py",     # cuello de botella + mejora
    "05_dashboard_data.py",     # calcula metricas para el dashboard -> JSON
    "05_dashboard_build.py",    # genera dashboard.html (ECharts, offline)
]

for s in SCRIPTS:
    print("\n" + "=" * 80 + f"\n>>> Ejecutando {s}\n" + "=" * 80)
    r = subprocess.run([sys.executable, str(HERE / s)], cwd=str(HERE))
    if r.returncode != 0:
        print(f"\n!!! ERROR ejecutando {s} (codigo {r.returncode}).")
        sys.exit(r.returncode)

print("\n" + "=" * 80)
print("TODO OK. Resultados en parte1/output/ (figuras/, tablas/, *.md).")
print("=" * 80)
