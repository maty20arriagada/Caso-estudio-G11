"""
run_all.py
=========================================================================
Script maestro de la Parte 2: ejecuta todo en orden.
1. kml_parser.py       — extrae distancias desde Google Earth
2. modelo_distribucion.py — resuelve el modelo LP (PuLP + CBC)
3. build_dashboard.py  — genera dashboard HTML interactivo
=========================================================================
"""

import subprocess
import sys
from pathlib import Path

PARTE2 = Path(__file__).resolve().parent
STEPS = [
    ("Parseando KML (distancias de Google Earth)", "kml_parser.py"),
    ("Resolviendo modelo de distribucion (PuLP + CBC)", "modelo_distribucion.py"),
    ("Generando dashboard HTML", "build_dashboard.py"),
]

if __name__ == "__main__":
    python = sys.executable
    ok = True
    for label, script in STEPS:
        print(f"\n{'='*60}")
        print(f"  {label}")
        print(f"{'='*60}")
        r = subprocess.run([python, str(PARTE2 / script)], cwd=str(PARTE2.parent))
        if r.returncode != 0:
            print(f"\n[FALLO] {script} termino con codigo {r.returncode}")
            ok = False
            break

    if ok:
        print(f"\n{'='*60}")
        print("  Parte 2 completada exitosamente.")
        print(f"{'='*60}")
        print(f"  Dashboard: parte2/output/dashboard_distribucion.html")
        print(f"  CSV con solucion: parte2/solucion_distribucion.csv")
        print(f"  JSON con datos: parte2/solucion_distribucion.json")
    else:
        sys.exit(1)
