"""
01b_diagnostico_overrun.py
=================================================================
Resuelve la ambiguedad de 01: las 48 fallas de estaciones de turno
que caen FUERA de la ventana operativa, ¿son...
   (A) overruns legitimos  -> el lote se INICIO dentro de turno y
       solo termino de procesarse pasado el cierre (regla: solo se
       prohibe INICIAR lotes fuera de turno, no terminarlos), o
   (B) violaciones reales   -> la maquina inicio/proceso un lote
       fuera de la ventana operativa (inconsistencia del modelo).
=================================================================
Metodo: a cada falla anomala se le asocia el lote en curso (via el
intervalo BUSY que la contiene en station_events) y se consulta en
batches.csv el instante de INICIO de proceso de ese lote. Si el inicio
esta dentro de la ventana operativa -> overrun legitimo (A).
"""

import numpy as np
import pandas as pd
import cmpc_utils as U

pd.set_option("display.width", 170)
pd.set_option("display.max_columns", 40)

calendar = U.load("calendar")
failures = U.load("failures")
events = U.load("station_events")
batches = U.load("batches")

# --- fallas anomalas (turno + fuera de ventana) ---
fa = U.attach_calendar(failures, "failure_time_h", calendar)
fa["station_type"] = np.where(fa["station"].isin(U.CONTINUOUS_STATIONS), "24/7", "turno")
anom = fa[(fa["station_type"] == "turno") & (~fa["in_shift_window"])].copy()
print(f"Fallas anomalas a diagnosticar: {len(anom)}")

# --- asociar cada falla al intervalo BUSY que la contiene (batch_id) ---
busy = events[events["state"] == "BUSY"].sort_values("start_time_h").reset_index(drop=True)

def busy_interval(rep, station, t):
    sub = busy[(busy["replication"] == rep) & (busy["station"] == station)]
    hit = sub[(sub["start_time_h"] <= t) & (sub["end_time_h"] > t)]
    return hit.iloc[0] if len(hit) else None

rows = []
for _, r in anom.iterrows():
    bi = busy_interval(r["replication"], r["station"], r["failure_time_h"] - 1e-6)
    bid = int(bi["batch_id"]) if bi is not None else -999
    # lote en batches.csv
    b = batches[(batches["replication"] == r["replication"]) &
                (batches["station"] == r["station"]) &
                (batches["batch_id"] == bid)]
    if len(b):
        b = b.iloc[0]
        start_proc = b["start_process_time_h"]
        end_proc = b["end_process_time_h"]
    else:
        start_proc = end_proc = np.nan
    rows.append({
        "replication": r["replication"], "station": r["station"],
        "failure_time_h": r["failure_time_h"],
        "clasificacion": ("DIA_NO_OPERATIVO" if not r["in_operating_day"]
                          else "FUERA_DE_TURNO"),
        "shift_close_h": r["shift_close_time_h"],
        "batch_id": bid, "batch_start_h": start_proc, "batch_end_h": end_proc,
    })
D = pd.DataFrame(rows)

# --- ventana operativa del INICIO del lote ---
# attach_calendar sobre batch_start_h: shift_open_time_h / shift_close_time_h
# pasan a ser los del DIA DE INICIO del lote (referencia correcta).
D2 = U.attach_calendar(D.dropna(subset=["batch_start_h"]), "batch_start_h", calendar)
D2["inicio_lote_en_turno"] = D2["in_shift_window"]

# Overrun correcto = horas entre la falla y el cierre del turno del dia
# en que se INICIO el lote (referencia fisica del overrun).
D2["overrun_h_post_cierre"] = D2["failure_time_h"] - D2["shift_close_time_h"]

# Para los casos (B), cuanto se "salio" el INICIO del lote de su ventana:
def gap_inicio(row):
    if not row["is_operating_day"]:
        return np.nan  # dia no operativo: no hay ventana
    if row["batch_start_h"] > row["shift_close_time_h"]:
        return row["batch_start_h"] - row["shift_close_time_h"]   # despues del cierre
    if row["batch_start_h"] < row["shift_open_time_h"]:
        return row["shift_open_time_h"] - row["batch_start_h"]    # antes de abrir
    return 0.0
D2["gap_inicio_fuera_ventana_h"] = D2.apply(gap_inicio, axis=1)

print("\n=== Diagnostico A vs B ===")
print("Inicio del lote en curso estaba dentro de la ventana operativa?")
print(D2["inicio_lote_en_turno"].value_counts().to_string())

legit = D2[D2["inicio_lote_en_turno"]]
viol = D2[~D2["inicio_lote_en_turno"]]
print(f"\n(A) Overruns legitimos (lote iniciado en turno): {len(legit)}")
print(f"(B) Violaciones reales  (lote iniciado fuera turno): {len(viol)}")

print("\nMagnitud del overrun (h pasado el cierre del turno del dia de inicio) - casos (A):")
if len(legit):
    print(legit["overrun_h_post_cierre"].describe()[["min", "25%", "50%", "75%", "max"]].to_string())

print("\nCaracterizacion de los casos (B) - cuanto se salio el INICIO del lote de la ventana:")
if len(viol):
    print(viol[["replication", "station", "batch_id", "batch_start_h",
                "shift_open_time_h", "shift_close_time_h", "is_operating_day",
                "gap_inicio_fuera_ventana_h"]].to_string(index=False))
    print(f"\n  gap mediano = {viol['gap_inicio_fuera_ventana_h'].median():.3f} h, "
          f"max = {viol['gap_inicio_fuera_ventana_h'].max():.3f} h")

# duracion tipica de lote por estacion (contexto)
print("\nDuracion de proceso por lote (h) - contexto, por estacion:")
batches["dur_h"] = batches["end_process_time_h"] - batches["start_process_time_h"]
print(batches.groupby("station")["dur_h"]
      .agg(["count", "mean", "median", "max"]).reindex(U.ALL_STATIONS).to_string())

print("\nDetalle de las fallas anomalas (primeras 20):")
print(D2[["replication", "station", "batch_id", "batch_start_h", "failure_time_h",
          "batch_end_h", "shift_close_h", "overrun_h_post_cierre",
          "clasificacion", "inicio_lote_en_turno"]].head(20).to_string(index=False))

D2.to_csv(U.OUT / "tablas" / "fallas_anomalas_diagnostico.csv", index=False)
print(f"\n>> Guardado: {U.OUT/'tablas'/'fallas_anomalas_diagnostico.csv'}")
