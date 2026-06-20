"""
02_warmup.py  (auditado y reforzado)
=================================================================
Deteccion del periodo de calentamiento (warm-up) por el metodo de
Welch (Law, "Simulation Modeling and Analysis"; Banks et al.).

AUDITORIA DEL WARM-UP:
El throughput agregado se estabiliza casi de inmediato, pero eso puede
enmascarar que las estaciones AGUAS ABAJO (ruta P3: aserradero ->
secado -> drymill -> impregnado) tardan mas en llenarse. Por eso aqui
NO se mira solo el throughput total: se evalua la convergencia de CADA
estacion (m3_out diario) y se toma el warm-up como el MAXIMO de los
cortes individuales (criterio conservador), redondeado a semana.

OJO (no estacionariedad): el WIP de log_yard crece sin acotarse porque
los arribos superan la capacidad del aserradero. Esa serie es NO
estacionaria por diseño y por eso NO se usa para fijar el warm-up.
=================================================================
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import cmpc_utils as U

po = U.load("product_outputs")
dthr = U.load("daily_throughput")
dwip = U.load("daily_wip")
days = np.arange(0, 365)
W = 7  # media movil semanal (absorbe la estacionalidad por el dia no operativo)


def serie_prom(df, day_col, val_col, mask=None):
    d = df if mask is None else df[mask]
    p = (d.pivot_table(index=day_col, columns="replication", values=val_col, aggfunc="sum")
         .reindex(days).fillna(0.0))
    return p.mean(axis=1)


def ma(s):
    return s.rolling(W, center=True, min_periods=1).mean()


# --- Series: throughput total + m3_out por estacion (promedio de replicas) ---
po = po.copy(); po["day"] = U.day_of(po["exit_time_h"])
series = {"LINEA (throughput)": serie_prom(po, "day", "volume_m3")}
for st in U.ALL_STATIONS:
    series[st] = serie_prom(dthr[dthr["station"] == st], "day", "m3_out")

# --- Deteccion del corte por serie (banda alrededor de la media de regimen) ---
def cutoff(s_ma, band=0.12, hold=7):
    """Fin del transitorio = primer dia a partir del cual la serie suavizada
    se mantiene dentro de +-'band' (12%) de su media de regimen durante al
    menos 'hold' dias consecutivos. Capta rampa y sobre-impulso inicial, y es
    robusto al ruido tardio de los nodos de bajo volumen (desviaciones
    aisladas no cuentan; debe ser una estabilizacion sostenida)."""
    mu = s_ma.loc[150:364].mean()
    if mu <= 0:
        return 0, mu
    a = (s_ma / mu).values
    for d in range(len(a)):
        seg = a[d:d + hold]
        if len(seg) >= hold and np.all(np.abs(seg - 1) <= band):
            return d, mu
    return int(days[-1]), mu

print("AUDITORIA DEL WARM-UP - convergencia por serie (Welch, MA=7d)")
print("-" * 64)
cuts = {}
norms = {}
for name, s in series.items():
    s_ma = ma(s)
    c, mu = cutoff(s_ma)
    cuts[name] = c
    norms[name] = (s_ma / mu) if mu > 0 else s_ma * 0
    print(f"  {name:22s} media_regimen={mu:7.1f}  corte={c:3d} dias")

print("\n[debug] Rampa inicial normalizada (dias 0-20) de los nodos lentos:")
for name in ["bano", "impregnado"]:
    print(f"  {name:11s}", " ".join(f"{norms[name].loc[d]:.2f}" for d in range(0, 21)))

cut_max = max(cuts.values())
welch_days = max(int(np.ceil((cut_max + 1) / 7.0) * 7), 7)   # criterio Welch (referencia)

# --- Estabilizacion de batch_volume_m3 POR REPLICA. El transitorio VARIA entre
#     replicas y, sobre todo, entre estaciones: las de bajo volumen al final de
#     la linea (bano, impregnado) tardan mas y son mas dispersas. Por eso el
#     warm-up NO se fija por replica: se usa UNO solo, conservador, que cubra a
#     la replica/estacion mas lenta (Welch / Law). ---
se_bv = U.load("station_events")
bvb = se_bv[(se_bv["state"] == "BUSY") & (se_bv["batch_volume_m3"] > 0)]


def _bvcut(t, v, reg, band=0.15, hold=25):
    roll = pd.Series(v).rolling(30, min_periods=10).median().values
    for i in range(len(roll)):
        seg = roll[i:i + hold]
        if len(seg) >= hold and np.all(np.abs(seg - reg) <= band * reg):
            return float(t[i])
    return None


per_rep_bv = {}
print("\nEstabilizacion de batch_volume_m3 por replica (h) [criterio del Apunte]:")
for stn in U.ALL_STATIONS:
    cs = []
    for r in range(5):
        d = bvb[(bvb["replication"] == r) & (bvb["station"] == stn)].sort_values("start_time_h")
        if len(d) < 40:
            cs.append(None); continue
        t = d["start_time_h"].to_numpy(); v = d["batch_volume_m3"].to_numpy()
        cs.append(_bvcut(t, v, float(np.median(v[t > 2000]))))
    per_rep_bv[stn] = cs
    print(f"  {stn:11s} " + ", ".join(f"r{r}=" + (f"{c:.0f}" if c else "-") for r, c in enumerate(cs)))
mx_bv = max([c for cs in per_rep_bv.values() for c in cs if c], default=0.0)

# --- WARM-UP PRINCIPAL adoptado = 216 h (~9 d): cubre la replica/estacion mas
#     lenta. Apunte (185.75 h) y Welch (14 d) quedan de referencia/seleccionables. ---
U.set_warmup_hours(U.DEFAULT_WARMUP_H)
warmup_h = U.warmup_start_h()
warmup_days = U.get_warmup_days()
print("-" * 64)
print(f"Maximo transitorio por replica/estacion (batch_volume) = {mx_bv:.0f} h")
print(f"Welch (ref, salida ensemble): {welch_days} d ({welch_days*24} h)")
print(f"WARM-UP PRINCIPAL adoptado = {warmup_h:.0f} h (~{warmup_h/24:.1f} d; "
      f"dia de corte mallas = {warmup_days}); Apunte={U.WARMUP_APUNTE_H} h disponible en el selector.")
print(f">> Persistido en {U.WARMUP_H_FILE}")

# --- WIP total (referencia de NO estacionariedad) ---
wip_tot = serie_prom(dwip, "day", "level_m3_mean")

# ======================================================================
# Figura 1: convergencia normalizada por estacion (el grafico pedido)
# ======================================================================
plt.rcParams.update({"font.size": 10})
fig, ax = plt.subplots(figsize=(11, 5.5))
pal = {"LINEA (throughput)": "#000000", "aserradero": "#c62828", "bano": "#1565c0",
       "secado": "#ef6c00", "drymill": "#6a1b9a", "impregnado": "#00897b"}
for name in series:
    lw = 2.6 if name == "LINEA (throughput)" else 1.6
    ax.plot(days, norms[name].values, label=f"{name} (corte {cuts[name]}d)",
            color=pal.get(name, "#777"), lw=lw,
            ls="-" if name == "LINEA (throughput)" else "-")
ax.axhspan(0.88, 1.12, color="#2e7d32", alpha=0.08)
ax.axhline(1.0, color="#2e7d32", ls=":", lw=1)
ax.axvspan(0, warmup_days, color="#c62828", alpha=0.12, label=f"WARM-UP = {warmup_days} d")
ax.axvline(warmup_days, color="#c62828", ls="--", lw=2)
ax.set_xlim(0, 120)
ax.set_ylim(0, 1.6)
ax.set_xlabel("Dia del horizonte")
ax.set_ylabel("Salida normalizada (m3_out / media de regimen)")
ax.set_title("Convergencia a estado estacionario por estacion (Welch, MA=7d)\n"
             "el warm-up se fija por la estacion mas lenta en estabilizarse")
ax.legend(fontsize=8, ncol=2, loc="lower right")
fig.tight_layout()
fig.savefig(U.OUT / "figuras" / "warmup_convergencia.png", dpi=120)
plt.close(fig)

# ======================================================================
# Figura 2: throughput estacionario vs WIP no estacionario (contraste)
# ======================================================================
fig, axes = plt.subplots(2, 1, figsize=(11, 7), sharex=True)
thr = series["LINEA (throughput)"]
axes[0].plot(days, thr, color="#90caf9", lw=0.8, label="promedio 5 replicas")
axes[0].plot(days, ma(thr), color="#0d47a1", lw=2, label="media movil 7d")
axes[0].axvspan(0, warmup_days, color="#c62828", alpha=0.10)
axes[0].axvline(warmup_days, color="#c62828", ls="--", label=f"warm-up = {warmup_days} d")
axes[0].set_ylabel("m3/dia"); axes[0].set_title("Throughput de la linea (ESTACIONARIO)")
axes[0].legend(loc="lower right", fontsize=8)
axes[1].plot(days, wip_tot, color="#90caf9", lw=0.8)
axes[1].plot(days, ma(wip_tot), color="#0d47a1", lw=2)
axes[1].axvspan(0, warmup_days, color="#c62828", alpha=0.10)
axes[1].axvline(warmup_days, color="#c62828", ls="--")
axes[1].set_ylabel("m3"); axes[1].set_xlabel("Dia del horizonte")
axes[1].set_title("WIP total del sistema (NO ESTACIONARIO: log_yard crece sin acotarse)")
fig.suptitle("Metodo de Welch - deteccion del periodo de calentamiento", y=0.99)
fig.tight_layout()
fig.savefig(U.OUT / "figuras" / "warmup_welch.png", dpi=120)
plt.close(fig)

# ======================================================================
# Figura 3: estabilizacion de batch_volume_m3 (BASE del corte del Apunte)
# ======================================================================
se = U.load("station_events")
bu = se[(se["state"] == "BUSY") & (se["batch_volume_m3"] > 0)].copy()
fig, ax = plt.subplots(figsize=(11, 5))
palb = {"aserradero": "#c62828", "bano": "#1565c0", "secado": "#ef6c00",
        "drymill": "#6a1b9a", "impregnado": "#00897b"}
for stn in U.ALL_STATIONS:
    d = bu[bu["station"] == stn].sort_values("start_time_h")
    if len(d) < 10:
        continue
    yroll = d["batch_volume_m3"].rolling(40, min_periods=10).median().to_numpy()
    ax.plot(d["start_time_h"].to_numpy(), yroll, color=palb.get(stn, "#777"), lw=1.4, label=stn)
ax.axvspan(0, warmup_h, color="#c62828", alpha=0.10)
ax.axvline(U.WARMUP_APUNTE_H, color="#9e9e9e", ls=":", lw=1.3, label=f"Apunte = {U.WARMUP_APUNTE_H:.0f} h")
ax.axvline(warmup_h, color="#c62828", ls="--", lw=2, label=f"principal = {warmup_h:.0f} h (9 d)")
ax.axvline(welch_days * 24, color="#2e7d32", ls=":", lw=1.5, label=f"Welch = {welch_days*24} h")
ax.set_xlim(0, 700)
ax.set_xlabel("Hora del horizonte (start_time_h)")
ax.set_ylabel("batch_volume_m3 (mediana movil 40 lotes)")
ax.set_title("Estabilizacion del tamaño de lote (batch_volume_m3) - base del warm-up del Apunte")
ax.legend(fontsize=8, ncol=3)
fig.tight_layout()
fig.savefig(U.OUT / "figuras" / "warmup_batchvolume.png", dpi=120)
plt.close(fig)
print(f">> Guardado: {U.OUT/'figuras'/'warmup_batchvolume.png'}")

# --- Exportar series de convergencia para el dashboard ---
conv = {"days": days.tolist(), "warmup_days": warmup_days, "warmup_h": warmup_h,
        "welch_days": welch_days, "apunte_h": U.WARMUP_APUNTE_H, "per_rep_bv": per_rep_bv,
        "cuts": cuts, "norm": {k: [float(x) for x in v.values] for k, v in norms.items()}}
import json
(U.OUT / "warmup_convergencia.json").write_text(json.dumps(conv, ensure_ascii=False), encoding="utf-8")

print(f">> Guardado: {U.OUT/'figuras'/'warmup_convergencia.png'}")
print(f">> Guardado: {U.OUT/'figuras'/'warmup_welch.png'}")
print(f">> Guardado: {U.OUT/'warmup_convergencia.json'}")
