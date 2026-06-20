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
def cutoff(s_ma):
    """Fin del transitorio = primer dia en que la serie suavizada (que parte
    desde el sistema vacio) ALCANZA el 90% de su media de regimen. Las
    fluctuaciones posteriores son ruido, no warm-up, asi que no se exigen."""
    mu = s_ma.loc[150:364].mean()
    if mu <= 0:
        return 0, mu
    norm = s_ma / mu
    for d in days:
        if norm.loc[d] >= 0.90:
            return int(d), mu
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
warmup_days = int(np.ceil((cut_max + 1) / 7.0) * 7)
warmup_days = max(warmup_days, 7)
U.set_warmup_days(warmup_days)
print("-" * 64)
print(f"Corte mas tardio = dia {cut_max} ({max(cuts, key=cuts.get)})")
print(f"WARM-UP adoptado (redondeo a semana) = {warmup_days} dias (= {warmup_days*24} h)")
print(f">> Persistido en {U.WARMUP_FILE}")

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

# --- Exportar series de convergencia para el dashboard ---
conv = {"days": days.tolist(), "warmup_days": warmup_days, "cuts": cuts,
        "norm": {k: [float(x) for x in v.values] for k, v in norms.items()}}
import json
(U.OUT / "warmup_convergencia.json").write_text(json.dumps(conv, ensure_ascii=False), encoding="utf-8")

print(f">> Guardado: {U.OUT/'figuras'/'warmup_convergencia.png'}")
print(f">> Guardado: {U.OUT/'figuras'/'warmup_welch.png'}")
print(f">> Guardado: {U.OUT/'warmup_convergencia.json'}")
