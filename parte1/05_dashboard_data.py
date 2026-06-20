"""
05_dashboard_data.py
=================================================================
Calcula datos DIARIOS granulares (por replica) para que el dashboard
recalcule todos los KPIs ante el filtro de periodo (dia / mes / año).
Salida: output/dashboard_data.json
=================================================================
"""
import json
import numpy as np
import pandas as pd
import cmpc_utils as U

NREPS = 5
warmup_d = U.get_warmup_days()
warmup_h = U.warmup_start_h()
DAYS = list(range(365))
R2 = lambda a: [round(float(x), 2) for x in a]

CONV = json.loads((U.OUT / "warmup_convergencia.json").read_text(encoding="utf-8")) \
    if (U.OUT / "warmup_convergencia.json").exists() else {}
AUDIT = json.loads((U.OUT / "audit.json").read_text(encoding="utf-8")) \
    if (U.OUT / "audit.json").exists() else {}

events = U.load("station_events"); batches = U.load("batches")
po = U.load("product_outputs"); dwip = U.load("daily_wip")
dthr = U.load("daily_throughput"); arr = U.load("log_arrivals")
fcls = pd.read_csv(U.OUT / "tablas" / "fallas_clasificadas.csv")
fdiag = pd.read_csv(U.OUT / "tablas" / "fallas_anomalas_diagnostico.csv")

def zeros(): return np.zeros(365)

# ----------------------------------------------------------------------
# (1) Horas por estado y dia: se reparte cada intervalo entre los dias
#     que cruza (clipping por frontera de dia).
# ----------------------------------------------------------------------
state_grid = {(r, s, st): zeros() for r in range(NREPS) for s in U.ALL_STATIONS for st in U.STATES}
for row in events.itertuples(index=False):
    r, s, state = row.replication, row.station, row.state
    a, b = row.start_time_h, row.end_time_h
    d0, d1 = int(a // 24), int((b - 1e-9) // 24)
    for d in range(max(0, d0), min(364, d1) + 1):
        lo, hi = max(a, d * 24), min(b, (d + 1) * 24)
        if hi > lo:
            state_grid[(r, s, state)][d] += (hi - lo)

# ----------------------------------------------------------------------
# (2) Volumenes por lote y dia (asignados al dia de inicio de proceso)
# ----------------------------------------------------------------------
b = batches.copy()
b["day"] = (b["start_process_time_h"] // 24).astype(int).clip(0, 364)
vin = {(r, s): zeros() for r in range(NREPS) for s in U.ALL_STATIONS}
vout = {(r, s): zeros() for r in range(NREPS) for s in U.ALL_STATIONS}
vscr = {(r, s): zeros() for r in range(NREPS) for s in U.ALL_STATIONS}
voutp = {(r, s, p): zeros() for r in range(NREPS) for s in U.ALL_STATIONS for p in ["P1", "P2", "P3"]}
for row in b.itertuples(index=False):
    k = (row.replication, row.station)
    vin[k][row.day] += row.volume_in_m3
    vout[k][row.day] += row.volume_out_m3
    vscr[k][row.day] += row.scrap_m3
    voutp[(row.replication, row.station, row.product)][row.day] += row.volume_out_m3

# ----------------------------------------------------------------------
# (3) Produccion terminada por dia (dia de salida) y series diarias
# ----------------------------------------------------------------------
po2 = po.copy(); po2["day"] = U.day_of(po2["exit_time_h"])
prod = {(r, p): zeros() for r in range(NREPS) for p in ["P1", "P2", "P3"]}
for row in po2.itertuples(index=False):
    prod[(row.replication, row.product)][int(row.day)] += row.volume_m3

arr2 = arr.copy(); arr2["day"] = U.day_of(arr2["arrival_time_h"])
arr_day = {r: zeros() for r in range(NREPS)}
for row in arr2.itertuples(index=False):
    arr_day[row.replication][int(row.day)] += row.volume_m3

asein = {r: zeros() for r in range(NREPS)}
for row in dthr[dthr["station"] == "aserradero"].itertuples(index=False):
    asein[row.replication][int(row.day)] = row.m3_in

wipd = {(r, buf): zeros() for r in range(NREPS) for buf in U.load("daily_wip")["buffer"].unique()}
BUFFERS = sorted(dwip["buffer"].unique())
for row in dwip.itertuples(index=False):
    wipd[(row.replication, row.buffer)][int(row.day)] = row.level_m3_eod

# ----------------------------------------------------------------------
# (4) Sankey: 13 enlaces, valor diario por replica
# ----------------------------------------------------------------------
def link_series(r):
    return {
        "trozos>aserradero": vin[(r, "aserradero")],
        "aserradero>Mermas": vscr[(r, "aserradero")],
        "aserradero>bano": voutp[(r, "aserradero", "P1")],
        "aserradero>secado": voutp[(r, "aserradero", "P2")] + voutp[(r, "aserradero", "P3")],
        "bano>Mermas": vscr[(r, "bano")], "bano>P1": vout[(r, "bano")],
        "secado>Mermas": vscr[(r, "secado")], "secado>drymill": vout[(r, "secado")],
        "drymill>Mermas": vscr[(r, "drymill")], "drymill>P2": voutp[(r, "drymill", "P2")],
        "drymill>impregnado": voutp[(r, "drymill", "P3")],
        "impregnado>Mermas": vscr[(r, "impregnado")], "impregnado>P3": vout[(r, "impregnado")],
    }
SANKEY_LINKS = list(link_series(0).keys())

# ----------------------------------------------------------------------
# (5) Listas: fallas (clasificadas) y lead times
# ----------------------------------------------------------------------
fm = fcls.merge(fdiag[["replication", "station", "failure_time_h", "inicio_lote_en_turno"]],
                on=["replication", "station", "failure_time_h"], how="left")
def cat(row):
    if row["clasificacion_ventana"] == "EN_TURNO": return "en_turno"
    if row["station_type"] == "24/7": return "cont"
    return "overrun" if row["inicio_lote_en_turno"] == True else "borde"
fm["cat"] = fm.apply(cat, axis=1)
failures_list = [[int(r.replication), r.station, int(r.day), round(float(r.hour_of_day), 2),
                  r.cat, round(float(r.repair_duration_h), 3)] for r in fm.itertuples(index=False)]

leads_list = [[int(r.replication), r.product, int(r.day), round(float(r.lead_time_h), 2)]
              for r in po2.itertuples(index=False)]

# ----------------------------------------------------------------------
# (5b) Registros por lote (para t_e, cola, ciclo y distribuciones FP) +
#      parametros de demanda/capacidad por nodo.
# ----------------------------------------------------------------------
ST_IDX = {s: i for i, s in enumerate(U.ALL_STATIONS)}
PR_IDX = {"P1": 0, "P2": 1, "P3": 2}
# Horas BUSY por lote (Apunte: "suma de intervalos BUSY"); excluye DOWN dentro
# del lote. Es el tiempo de PROCESO efectivo (coincide con el Excel del equipo).
busyb = {}
for r in events[events["state"] == "BUSY"].itertuples(index=False):
    k = (r.replication, r.station, r.batch_id)
    busyb[k] = busyb.get(k, 0.0) + (r.end_time_h - r.start_time_h)
bb = batches.copy()
bb["cola"] = (bb["start_process_time_h"] - bb["enter_buffer_time_h"]).clip(lower=0)
bb["ciclo"] = bb["end_process_time_h"] - bb["enter_buffer_time_h"]   # cola + proceso (wall, incl. DOWN)
bb["bday"] = (bb["start_process_time_h"] // 24).astype(int).clip(0, 364)
# [rep, st_idx, pr_idx, day, vol_in, vol_out, setup, proc_busy, cola, ciclo]
batch_records = []
for r in bb.itertuples(index=False):
    proc = busyb.get((r.replication, r.station, r.batch_id),
                     r.end_process_time_h - r.start_process_time_h)
    batch_records.append([int(r.replication), ST_IDX[r.station], PR_IDX[r.product], int(r.bday),
                          round(float(r.volume_in_m3), 3), round(float(r.volume_out_m3), 3),
                          round(float(r.setup_time_h), 3), round(float(proc), 4),
                          round(float(r.cola), 4), round(float(r.ciclo), 4)])
PARAMS = U.load_parametros()

# ----------------------------------------------------------------------
# (6) Empaquetado diario (listas de 5 arrays, una por replica)
# ----------------------------------------------------------------------
def per_rep(fn):  # fn(r) -> array365
    return [R2(fn(r)) for r in range(NREPS)]

daily = {
    "state": {s: {st: per_rep(lambda r, s=s, st=st: state_grid[(r, s, st)]) for st in U.STATES}
              for s in U.ALL_STATIONS},
    "vin": {s: per_rep(lambda r, s=s: vin[(r, s)]) for s in U.ALL_STATIONS},
    "vout": {s: per_rep(lambda r, s=s: vout[(r, s)]) for s in U.ALL_STATIONS},
    "sankey": {ln: per_rep(lambda r, ln=ln: link_series(r)[ln]) for ln in SANKEY_LINKS},
    "prod": {p: per_rep(lambda r, p=p: prod[(r, p)]) for p in ["P1", "P2", "P3"]},
    "throughput": per_rep(lambda r: sum(prod[(r, p)] for p in ["P1", "P2", "P3"])),
    "arrivals": per_rep(lambda r: arr_day[r]),
    "aserradero_in": per_rep(lambda r: asein[r]),
    "wip": {buf: per_rep(lambda r, buf=buf: wipd[(r, buf)]) for buf in BUFFERS},
}

# Calendario sintetico (año no bisiesto): mapear dia-del-horizonte a mes
mdays = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
mnames = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio",
          "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
months = []; acc = 0
for i, dd in enumerate(mdays):
    months.append({"idx": i + 1, "name": mnames[i], "start": acc, "end": acc + dd - 1, "ndays": dd})
    acc += dd

DATA = {
    "meta": {
        "warmup_days": warmup_d, "nreps": NREPS,
        "stations": U.ALL_STATIONS, "continuous": U.CONTINUOUS_STATIONS,
        "states": U.STATES, "buffers": BUFFERS, "days": DAYS,
        "sankey_links": SANKEY_LINKS, "months": months,
        "products": ["P1", "P2", "P3"],
        "warmup_h": round(float(warmup_h), 2),
        "warmup_apunte_days": int(np.ceil(U.WARMUP_APUNTE_H / 24)),
        "warmup_inter_days": int(np.ceil(U.WARMUP_INTER_H / 24)),
        "warmup_welch_days": int(np.ceil(U.WARMUP_WELCH_H / 24)),
        "parametros": PARAMS,
        "convergencia": CONV, "audit": AUDIT,
        "state_colors": {"BUSY": "#2e7d32", "SETUP": "#8e24aa", "IDLE": "#fbc02d",
                         "BLOCKED": "#e64a19", "DOWN": "#c62828", "OFF_SHIFT": "#b0bec5"},
        "product_colors": {"P1": "#4C72B0", "P2": "#55A868", "P3": "#8172B3"},
    },
    "daily": daily,
    "failures": failures_list,
    "leads": leads_list,
    "batches": batch_records,
}

out = U.OUT / "dashboard_data.json"
out.write_text(json.dumps(DATA, ensure_ascii=False, allow_nan=False, separators=(",", ":")), encoding="utf-8")
print(f">> {out}  ({out.stat().st_size/1024:.0f} KB)")

# ----------------------------------------------------------------------
# (7) Auto-chequeo: reproducir KPIs de año completo desde la malla diaria
# ----------------------------------------------------------------------
d0 = warmup_d
busy = np.mean([sum(state_grid[(r, "aserradero", "BUSY")][d0:]) for r in range(NREPS)])
sched = np.mean([sum(state_grid[(r, "aserradero", s)][d0:] for s in U.STATES).sum()
                 - sum(state_grid[(r, "aserradero", "OFF_SHIFT")][d0:]) for r in range(NREPS)])
prod_tot = np.mean([sum(prod[(r, p)][d0:].sum() for p in ["P1", "P2", "P3"]) for r in range(NREPS)]) * 365 / (365 - d0)
print(f"[check] util_aserradero(año)={busy/sched*100:.1f}%  produccion={prod_tot:.0f} m3/año "
      f"(esperado ~84%, ~22158)")
