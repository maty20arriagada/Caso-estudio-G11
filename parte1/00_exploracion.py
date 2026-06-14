"""
00_exploracion.py
=================================================================
Caso de Estudio CMPC Mulchen - Parte 1: Analisis de productividad
Exploracion y perfilado inicial de los datos (/explore-data)
=================================================================
Objetivo de este script: entender la FORMA, CALIDAD y PATRONES de
los datos antes de cualquier analisis. No calcula KPIs todavia.
"""

from pathlib import Path
import pandas as pd
import numpy as np

pd.set_option("display.max_columns", 50)
pd.set_option("display.width", 160)

# ----------------------------------------------------------------------
# Localizacion de datos
# ----------------------------------------------------------------------
BASE = Path(__file__).resolve().parent.parent          # .../Tareas
DATA = BASE / "data"

print("=" * 70)
print("ARCHIVOS PRESENTES EN LA CARPETA data/")
print("=" * 70)
for f in sorted(DATA.iterdir()):
    print(f"  {f.name:30s} {f.stat().st_size/1024:8.1f} KB")

# Archivos que el PDF dice que deberian venir en el paquete
esperados = [
    "inputs_readme.md", "parameters.csv", "calendar.csv", "log_arrivals.csv",
    "station_events.csv", "batches.csv", "buffer_events.csv",
    "product_outputs.csv", "failures.csv", "daily_wip.csv", "daily_throughput.csv",
]
presentes = {f.name for f in DATA.iterdir()}
faltan = [e for e in esperados if e not in presentes]
print("\n>>> Archivos esperados por el PDF que NO estan presentes:")
print("   ", faltan if faltan else "ninguno")

# ----------------------------------------------------------------------
# Carga de todos los CSV disponibles
# ----------------------------------------------------------------------
csvs = {f.stem: f for f in DATA.glob("*.csv")}
dfs = {name: pd.read_csv(path) for name, path in csvs.items()}

print("\n" + "=" * 70)
print("PERFIL GENERAL POR TABLA")
print("=" * 70)
for name, df in dfs.items():
    print(f"\n----- {name}.csv  ->  filas={len(df):,}  columnas={len(df.columns)}")
    print("Columnas y dtypes:")
    for c in df.columns:
        nn = df[c].isna().mean() * 100
        print(f"   {c:24s} {str(df[c].dtype):10s} nulos={nn:5.1f}%  distintos={df[c].nunique()}")
    print("Muestra (head 3):")
    print(df.head(3).to_string(index=False))

# ----------------------------------------------------------------------
# Dimensiones clave del experimento de simulacion
# ----------------------------------------------------------------------
print("\n" + "=" * 70)
print("DIMENSIONES DEL EXPERIMENTO")
print("=" * 70)

# Replicas
for name in ["station_events", "failures", "daily_throughput", "product_outputs"]:
    if name in dfs and "replication" in dfs[name].columns:
        reps = sorted(dfs[name]["replication"].unique())
        print(f"  {name}: replicas = {reps}")

# Horizonte temporal
if "calendar" in dfs:
    cal = dfs["calendar"]
    print(f"\n  calendar: dias = {cal['day'].min()} .. {cal['day'].max()}  (total {cal['day'].nunique()} dias)")
    print(f"  calendar: is_operating_day -> {cal['is_operating_day'].value_counts().to_dict()}")
    print(f"  calendar: planned_operating_hours unicos -> {sorted(cal['planned_operating_hours'].unique())}")

# Rango de tiempo en station_events
if "station_events" in dfs:
    se = dfs["station_events"]
    print(f"\n  station_events: t_min={se['start_time_h'].min():.2f} h  t_max={se['end_time_h'].max():.2f} h")
    print(f"  station_events: estaciones -> {sorted(se['station'].unique())}")
    print(f"  station_events: estados   -> {sorted(se['state'].unique())}")
    print(f"  station_events: productos -> {sorted(se['product'].dropna().unique())}")

# Estaciones en failures
if "failures" in dfs:
    fa = dfs["failures"]
    print(f"\n  failures: estaciones con fallas -> {fa['station'].value_counts().to_dict()}")
    print(f"  failures: t_min={fa['failure_time_h'].min():.2f}  t_max={fa['failure_time_h'].max():.2f}")
    print(f"  failures: repair_duration_h  min={fa['repair_duration_h'].min():.3f}  "
          f"mean={fa['repair_duration_h'].mean():.3f}  max={fa['repair_duration_h'].max():.3f}")

print("\nOK - exploracion base completada.")
