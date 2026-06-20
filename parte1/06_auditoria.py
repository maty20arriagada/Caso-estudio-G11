"""
06_auditoria.py
=================================================================
AUDITORIA de consistencia interna de los datos y de los calculos.
Cada verificacion cruza fuentes independientes (logs de estados,
fallas, lotes, buffers, throughput) y debe cuadrar. Resultado:
output/AUDITORIA.md  +  output/audit.json (para el dashboard).
=================================================================
"""
import json
import sys
import numpy as np
import pandas as pd
import cmpc_utils as U

try:
    sys.stdout.reconfigure(encoding="utf-8")   # consola Windows soporta Δ, ≈, etc.
except Exception:
    pass

events = U.load("station_events"); batches = U.load("batches")
failures = U.load("failures"); po = U.load("product_outputs")
be = U.load("buffer_events"); dwip = U.load("daily_wip")
arr = U.load("log_arrivals"); dthr = U.load("daily_throughput"); cal = U.load("calendar")
warmup_d = U.get_warmup_days(); warmup_h = U.warmup_start_h()

checks = []
def add(name, ok, detail):
    checks.append({"name": name, "status": "PASS" if ok else "FAIL", "detail": detail})

# 1) Particion temporal: los estados deben cubrir exactamente 8760 h
Mfull = U.state_matrix(events, warmup_h=0); tot = Mfull.sum(axis=1)
add("Particion temporal: estados suman 8760 h por (rep,estacion)",
    np.allclose(tot, U.HORIZON_H, atol=1e-2),
    f"min={tot.min():.3f} h, max={tot.max():.3f} h (esperado {U.HORIZON_H:.0f})")

# 2) DOWN (station_events) == suma de duraciones de reparacion (failures)
down = U.state_durations(events, 0)
down = down[down["state"] == "DOWN"].groupby(["replication", "station"])["dur_h"].sum()
rep = failures.groupby(["replication", "station"])["repair_duration_h"].sum()
j = pd.concat([down.rename("down"), rep.rename("rep")], axis=1).fillna(0.0)
j["d"] = (j["down"] - j["rep"]).abs()
add("DOWN == suma de reparaciones (confiabilidad consistente)",
    j["d"].max() < 0.5, f"max|Δ|={j['d'].max():.4f} h sobre {len(j)} pares (rep,estacion)")

# 3) OFF_SHIFT solo en estaciones de turno
offst = Mfull["OFF_SHIFT"].groupby("station").mean()
ok3 = all(offst.get(s, 0) == 0 for s in U.CONTINUOUS_STATIONS) and \
      all(offst.get(s, 0) > 0 for s in U.SHIFT_STATIONS)
add("OFF_SHIFT solo en estaciones de turno (24/7 = 0)", ok3,
    "; ".join(f"{s}={offst[s]:.0f}h" for s in U.ALL_STATIONS))

# 4) Todas las fallas ocurren en BUSY
fcls = pd.read_csv(U.OUT / "tablas" / "fallas_clasificadas.csv")
busyrate = (fcls["estado_pre_falla"] == "BUSY").mean()
add("Toda falla ocurre con la maquina en BUSY", busyrate == 1.0,
    f"{busyrate*100:.1f}% de {len(fcls)} fallas (esperado 100%)")

# 5) Balance de materia por lote: vol_in = vol_out + scrap
db = (batches["volume_in_m3"] - batches["volume_out_m3"] - batches["scrap_m3"]).abs()
add("Balance de materia por lote (in = out + scrap)", db.max() <= 2e-3,
    f"max|Δ|={db.max():.2e} m3 (= redondeo a 3 decimales del CSV) en {len(batches)} lotes")

# 6) Rangos validos de KPIs (yields, disponibilidad, utilizacion en [0,1])
M = U.state_matrix(events, warmup_h).reset_index()
M["TOTAL"] = M[U.STATES].sum(axis=1); M["SCHED"] = M["TOTAL"] - M["OFF_SHIFT"]
util = M["BUSY"] / M["SCHED"]; disp = M["BUSY"] / (M["BUSY"] + M["DOWN"]).replace(0, np.nan)
bs = batches[batches["start_process_time_h"] >= warmup_h]
_y = bs.groupby("station")[["volume_in_m3", "volume_out_m3"]].sum()
yl = _y["volume_out_m3"] / _y["volume_in_m3"]
ok6 = util.between(0, 1).all() and disp.dropna().between(0, 1).all() and yl.between(0, 1).all()
add("KPIs en rango valido (utilizacion, disponibilidad, yield en [0,1])", ok6,
    f"util[{util.min():.2f},{util.max():.2f}] disp[{disp.min():.2f},{disp.max():.2f}] yield[{yl.min():.2f},{yl.max():.2f}]")

# 7) Throughput: producto terminado == salida de la ultima estacion de su ruta
fin = po.groupby("product")["volume_m3"].sum()
last_out = {
    "P1": batches[batches["station"] == "bano"]["volume_out_m3"].sum(),
    "P2": batches[(batches["station"] == "drymill") & (batches["product"] == "P2")]["volume_out_m3"].sum(),
    "P3": batches[batches["station"] == "impregnado"]["volume_out_m3"].sum(),
}
rels = {p: abs(fin[p] - last_out[p]) / fin[p] for p in ["P1", "P2", "P3"]}
add("Throughput: terminado == salida de la ultima estacion (por ruta)",
    max(rels.values()) < 0.02, "; ".join(f"{p}:{rels[p]*100:.2f}%" for p in rels))

# 8) Balance log_yard: arribos - procesado == variacion de nivel
tot_arr = arr.groupby("replication")["volume_m3"].sum().mean()
tot_in = dthr[dthr["station"] == "aserradero"].groupby("replication")["m3_in"].sum().mean()
ly_final = dwip[(dwip["buffer"] == "log_yard") & (dwip["day"] == 364)]["level_m3_eod"].mean()
rel8 = abs((tot_arr - tot_in) - ly_final) / ly_final
add("Balance log_yard: arribos - procesado == nivel final",
    rel8 < 0.05, f"arribos={tot_arr:.0f}, procesado={tot_in:.0f}, Δ={tot_arr-tot_in:.0f} vs nivel={ly_final:.0f} m3 ({rel8*100:.1f}%)")

# 9) Conservacion en buffers: cumsum(delta) == level_after
be2 = be.sort_values(["replication", "buffer", "time_h"]).copy()
be2["cum"] = be2.groupby(["replication", "buffer"])["delta_m3"].cumsum()
dbuf = (be2["cum"] - be2["level_after_m3"]).abs()
add("Conservacion en buffers (cumsum Δ = nivel registrado)", dbuf.max() < 1e-3,
    f"max|Δ|={dbuf.max():.2e} m3 en {len(be2)} eventos")

# 10) batch_id unico por (rep, estacion)
g = batches.groupby(["replication", "station"])["batch_id"]
ok10 = (g.nunique() == g.size()).all()
add("batch_id unico por (replica, estacion)", ok10,
    "sin duplicados" if ok10 else "hay duplicados")

# 11) Arribos dentro de la ventana operativa (calidad de datos)
arrc = U.attach_calendar(arr, "arrival_time_h", cal)
pin = arrc["in_shift_window"].mean()
add("Arribos de camiones dentro de la ventana operativa", pin > 0.99,
    f"{pin*100:.2f}% de {len(arr)} arribos en ventana 07-23 de dias operativos")

# ----------------------------------------------------------------------
# Reporte
# ----------------------------------------------------------------------
npass = sum(c["status"] == "PASS" for c in checks)
print("=" * 72); print(f" AUDITORIA DE CONSISTENCIA  ({npass}/{len(checks)} PASS)  warm-up={warmup_d} d")
print("=" * 72)
for c in checks:
    mark = "[OK]  " if c["status"] == "PASS" else "[FALLA]"
    print(f" {mark} {c['name']}\n        -> {c['detail']}")

md = [f"# Auditoría de consistencia interna — Parte 1\n",
      f"**Resultado: {npass}/{len(checks)} verificaciones PASS** · warm-up = {warmup_d} días "
      f"· periodo estacionario [{warmup_h:.0f}, {U.HORIZON_H:.0f}] h\n",
      "| # | Verificación | Estado | Detalle |", "|---|---|---|---|"]
for i, c in enumerate(checks, 1):
    md.append(f"| {i} | {c['name']} | {'✅ '+c['status'] if c['status']=='PASS' else '❌ '+c['status']} | {c['detail']} |")
(U.OUT / "AUDITORIA.md").write_text("\n".join(md), encoding="utf-8")
(U.OUT / "audit.json").write_text(json.dumps(
    {"npass": npass, "ntotal": len(checks), "warmup_days": warmup_d, "checks": checks},
    ensure_ascii=False), encoding="utf-8")
print(f"\n>> {U.OUT/'AUDITORIA.md'}\n>> {U.OUT/'audit.json'}")
