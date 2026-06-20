"""
03_disponibilidad.py
=================================================================
Descomposicion de estados, DISPONIBILIDAD y UTILIZACION por estacion.
Marco de referencia: Factory Physics (Hopp & Spearman) y teoria de
mantenimiento/confiabilidad.

Definiciones empleadas (estimacion empirica desde los logs):
  tiempo_total      = horas del periodo estacionario [warmup, 8760]
  OFF_SHIFT         = fuera de turno (no aplica a secado/impregnado)
  tiempo_programado = tiempo_total - OFF_SHIFT   (rostered / disponible)
  Utilizacion  u    = BUSY / tiempo_programado
  Disponibilidad A  = BUSY / (BUSY + DOWN) = MTBF/(MTBF+MTTR)
                      (falla dependiente de operacion: el reloj de TBF
                       corre solo mientras la maquina procesa)
  MTBF (empirico)   = horas BUSY / numero de fallas
  MTTR (empirico)   = duracion media de reparacion
  Yield (calidad)   = volume_out / volume_in   (por estacion)
Los KPIs se calculan por replica y se reportan como media +/- IC95%
(t de Student, 4 g.l., R=5 replicas).
=================================================================
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import cmpc_utils as U

pd.set_option("display.width", 180)
pd.set_option("display.max_columns", 40)

TCRIT = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571,
         6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228}


def ci95(x):
    x = np.asarray(x, dtype=float)
    n = len(x)
    m = x.mean()
    if n < 2:
        return m, 0.0
    s = x.std(ddof=1)
    hw = TCRIT.get(n - 1, 1.96) * s / np.sqrt(n)
    return m, hw


events = U.load("station_events")
batches = U.load("batches")
failures = U.load("failures")
warmup_h = U.warmup_start_h()
print(f"Warm-up aplicado: {U.get_warmup_days()} dias ({warmup_h:.0f} h). "
      f"Periodo estacionario: [{warmup_h:.0f}, {U.HORIZON_H:.0f}] h\n")

# ----------------------------------------------------------------------
# 1) Matriz de horas por estado (rep, station) en periodo estacionario
# ----------------------------------------------------------------------
M = U.state_matrix(events, warmup_h)          # index (rep,station) x estados
M["TOTAL"] = M.sum(axis=1)
M["SCHEDULED"] = M["TOTAL"] - M["OFF_SHIFT"]

# sanity check: TOTAL ~ 8760 - warmup
print(f"[check] TOTAL horas por (rep,station): "
      f"min={M['TOTAL'].min():.1f}  max={M['TOTAL'].max():.1f}  "
      f"(esperado ~{U.HORIZON_H-warmup_h:.0f})")

# ----------------------------------------------------------------------
# 2) Fallas y yield por (rep, station) en periodo estacionario
# ----------------------------------------------------------------------
fa = failures[failures["failure_time_h"] >= warmup_h]
nfail = (fa.groupby(["replication", "station"]).size()
         .rename("n_fail").reset_index())
mttr = (fa.groupby(["replication", "station"])["repair_duration_h"].mean()
        .rename("MTTR_h").reset_index())

bb = batches[batches["start_process_time_h"] >= warmup_h]
yld = (bb.groupby(["replication", "station"])[["volume_in_m3", "volume_out_m3"]]
       .sum().reset_index())
yld["yield"] = yld["volume_out_m3"] / yld["volume_in_m3"]

# ----------------------------------------------------------------------
# 3) KPIs por (rep, station)
# ----------------------------------------------------------------------
df = M.reset_index().merge(nfail, on=["replication", "station"], how="left") \
                    .merge(mttr, on=["replication", "station"], how="left") \
                    .merge(yld[["replication", "station", "yield"]],
                           on=["replication", "station"], how="left")
df["n_fail"] = df["n_fail"].fillna(0)

df["utilizacion"] = df["BUSY"] / df["SCHEDULED"]
# Disponibilidad inherente = BUSY/(BUSY+DOWN) (secundaria)
df["disponibilidad"] = np.where(df["BUSY"] + df["DOWN"] > 0,
                                df["BUSY"] / (df["BUSY"] + df["DOWN"]), np.nan)
# Disponibilidad operacional (Apunte/FP, principal) = (req - DOWN)/req,
# req = BUSY+DOWN+IDLE+SETUP+BLOCKED (excluye OFF_SHIFT)
_req = df[["BUSY", "DOWN", "IDLE", "SETUP", "BLOCKED"]].sum(axis=1)
df["disponibilidad_fp"] = np.where(_req > 0, (_req - df["DOWN"]) / _req, np.nan)
df["MTBF_h"] = np.where(df["n_fail"] > 0, df["BUSY"] / df["n_fail"], np.nan)
# OEE = Disponibilidad(FP) * BUSY/(BUSY+SETUP) * Yield   (alineado al dashboard)
denom = df["BUSY"] + df["SETUP"]
df["OEE"] = np.where(
    (denom > 0) & df["disponibilidad_fp"].notna() & df["yield"].notna(),
    df["disponibilidad_fp"] * df["BUSY"] / denom * df["yield"],
    np.nan
)
# fracciones de tiempo (sobre total) para composicion
for s in U.STATES:
    df[f"f_{s}"] = df[s] / df["TOTAL"]

# ----------------------------------------------------------------------
# 4) Agregacion media +/- IC95% por estacion
# ----------------------------------------------------------------------
rows = []
for st in U.ALL_STATIONS:
    d = df[df["station"] == st]
    rec = {"station": st,
           "tipo": "24/7" if st in U.CONTINUOUS_STATIONS else "turno"}
    for k in ["utilizacion", "disponibilidad", "disponibilidad_fp", "OEE", "MTBF_h", "MTTR_h", "yield"]:
        m, hw = ci95(d[k].dropna())
        rec[k] = m
        rec[k + "_ic"] = hw
    rec["fallas"] = d["n_fail"].mean()
    for s in U.STATES:
        rec[f"f_{s}"] = d[f"f_{s}"].mean()
    rows.append(rec)
R = pd.DataFrame(rows).set_index("station").reindex(U.ALL_STATIONS)

# ----------------------------------------------------------------------
# 5) Reporte
# ----------------------------------------------------------------------
print("\n" + "=" * 72)
print(" DISPONIBILIDAD / UTILIZACION POR ESTACION (media de 5 replicas)")
print("=" * 72)
rep_tab = R[["tipo", "utilizacion", "disponibilidad_fp", "disponibilidad", "OEE", "MTBF_h", "MTTR_h",
             "fallas", "yield"]].copy()
rep_tab.columns = ["tipo", "Utiliz.", "Disp.FP", "Disp.inh", "OEE", "MTBF_h", "MTTR_h",
                   "fallas", "Yield"]
print(rep_tab.round(3).to_string())

print("\nIC95% (semiancho) de utilizacion y disponibilidad:")
print(R[["utilizacion", "utilizacion_ic", "disponibilidad", "disponibilidad_ic"]]
      .round(4).to_string())

print("\nComposicion del tiempo (fraccion del total, media replicas):")
comp = R[[f"f_{s}" for s in U.STATES]].copy()
comp.columns = U.STATES
print((comp * 100).round(1).to_string())

# ----------------------------------------------------------------------
# 6) Guardar tablas
# ----------------------------------------------------------------------
df.to_csv(U.OUT / "tablas" / "kpis_por_replica.csv", index=False)
R.to_csv(U.OUT / "tablas" / "disponibilidad_resumen.csv")
print(f"\n>> Guardado: {U.OUT/'tablas'/'kpis_por_replica.csv'}")
print(f">> Guardado: {U.OUT/'tablas'/'disponibilidad_resumen.csv'}")

# ----------------------------------------------------------------------
# 7) Figuras
# ----------------------------------------------------------------------
plt.rcParams.update({"font.size": 10})
state_colors = {"BUSY": "#2e7d32", "SETUP": "#9c27b0", "IDLE": "#fbc02d",
                "BLOCKED": "#e64a19", "DOWN": "#c62828", "OFF_SHIFT": "#9e9e9e"}

# Fig 1: composicion de estados (stacked, % del total)
fig, ax = plt.subplots(figsize=(10, 5.5))
x = np.arange(len(U.ALL_STATIONS))
bottom = np.zeros(len(U.ALL_STATIONS))
for s in U.STATES:
    vals = (comp[s] * 100).reindex(U.ALL_STATIONS).to_numpy()
    ax.bar(x, vals, bottom=bottom, label=s, color=state_colors[s])
    bottom += vals
ax.set_xticks(x)
ax.set_xticklabels([f"{s}\n({R.loc[s,'tipo']})" for s in U.ALL_STATIONS])
ax.set_ylabel("% del tiempo total")
ax.set_title("Composicion del tiempo por estado y estacion\n(periodo estacionario, media de 5 replicas)")
ax.legend(ncol=6, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.08))
fig.tight_layout()
fig.savefig(U.OUT / "figuras" / "composicion_estados.png", dpi=120)
plt.close(fig)

# Fig 2: utilizacion y disponibilidad con IC95
fig, ax = plt.subplots(figsize=(10, 5))
w = 0.38
u = R["utilizacion"].to_numpy(); u_ic = R["utilizacion_ic"].to_numpy()
a = R["disponibilidad"].to_numpy(); a_ic = R["disponibilidad_ic"].to_numpy()
ax.bar(x - w/2, u*100, w, yerr=u_ic*100, capsize=4, label="Utilizacion (BUSY/programado)",
       color="#1565c0")
ax.bar(x + w/2, a*100, w, yerr=a_ic*100, capsize=4, label="Disponibilidad (MTBF/(MTBF+MTTR))",
       color="#2e7d32")
for i in range(len(x)):
    ax.text(x[i]-w/2, u[i]*100+1.5, f"{u[i]*100:.0f}%", ha="center", fontsize=8)
    ax.text(x[i]+w/2, a[i]*100+1.5, f"{a[i]*100:.0f}%", ha="center", fontsize=8)
ax.set_xticks(x); ax.set_xticklabels(U.ALL_STATIONS)
ax.set_ylabel("%"); ax.set_ylim(0, 105)
ax.set_title("Utilizacion y Disponibilidad por estacion (media 5 replicas, IC95%)")
ax.legend()
fig.tight_layout()
fig.savefig(U.OUT / "figuras" / "utilizacion_disponibilidad.png", dpi=120)
plt.close(fig)

# Fig 3: yield por estacion
fig, ax = plt.subplots(figsize=(9, 4.5))
yv = R["yield"].to_numpy()*100; yic = R["yield_ic"].to_numpy()*100
ax.bar(x, yv, yerr=yic, capsize=4, color="#00897b")
for i in range(len(x)):
    ax.text(x[i], yv[i]+1, f"{yv[i]:.1f}%", ha="center", fontsize=9)
ax.set_xticks(x); ax.set_xticklabels(U.ALL_STATIONS)
ax.set_ylabel("Yield (%)"); ax.set_ylim(0, 105)
ax.set_title("Rendimiento de proceso (yield = vol_out/vol_in) por estacion")
fig.tight_layout()
fig.savefig(U.OUT / "figuras" / "yield_por_estacion.png", dpi=120)
plt.close(fig)

print(f">> Guardado: {U.OUT/'figuras'/'composicion_estados.png'}")
print(f">> Guardado: {U.OUT/'figuras'/'utilizacion_disponibilidad.png'}")
print(f">> Guardado: {U.OUT/'figuras'/'yield_por_estacion.png'}")
print("\nOK - disponibilidad completada.")
