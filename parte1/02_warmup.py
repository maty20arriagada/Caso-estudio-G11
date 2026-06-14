"""
02_warmup.py
=================================================================
Deteccion del periodo de calentamiento (warm-up) por el metodo
grafico de Welch (Law, "Simulation Modeling and Analysis";
Banks et al., "Discrete-Event System Simulation").

Idea: el sistema arranca VACIO (todos los buffers en 0). Hay un
transitorio mientras se llena la linea y los productos con ruta mas
larga (P3) empiezan a salir. Promediamos cada serie diaria sobre las
5 replicas, suavizamos con media movil y ubicamos el dia a partir del
cual la serie se estabiliza. Esos dias iniciales se descartan en los
KPIs estacionarios (scripts 03 y 04).
=================================================================
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import cmpc_utils as U

po = U.load("product_outputs")
dw = U.load("daily_wip")
days = np.arange(0, 365)
W = 7  # ventana de media movil = 1 semana (absorbe la estacionalidad semanal)


def serie_diaria_promedio(df, day_col, val_col, agg="sum"):
    """Serie val_col por dia, promediada sobre replicas."""
    p = (df.pivot_table(index=day_col, columns="replication",
                        values=val_col, aggfunc=agg)
         .reindex(days).fillna(0.0))
    return p.mean(axis=1)


# --- Serie 1: volumen terminado por dia (throughput de la linea) ---
po = po.copy()
po["day"] = U.day_of(po["exit_time_h"])
thr = serie_diaria_promedio(po, "day", "volume_m3", "sum")

# --- Serie 2: WIP total del sistema por dia (suma de buffers) ---
wip = serie_diaria_promedio(dw, "day", "level_m3_mean", "sum")

thr_s = thr.rolling(W, center=True, min_periods=1).mean()
wip_s = wip.rolling(W, center=True, min_periods=1).mean()

# --- Deteccion del corte sobre el throughput suavizado ---
# Media de regimen: segunda mitad del horizonte (claramente estacionaria)
mu = thr_s.loc[150:364].mean()
umbral = 0.90 * mu
# primer dia en que la serie suavizada alcanza el 90% del regimen y se mantiene
cut = 0
for d in days:
    if (thr_s.loc[d:] >= umbral).all():
        cut = d
        break
warmup_days = int(np.ceil((cut + 1) / 7.0) * 7)  # redondeo a semana completa
warmup_days = max(warmup_days, 7)                 # minimo prudente 1 semana

U.set_warmup_days(warmup_days)

print("DETECCION DE WARM-UP (Welch)")
print("-" * 50)
print(f"Throughput de regimen (mu, dias 150-364) ... {mu:8.1f} m3/dia")
print(f"Umbral 90% de mu ........................... {umbral:8.1f} m3/dia")
print(f"Primer dia >= umbral (sostenido) ........... dia {cut}")
print(f"WARM-UP adoptado (redondeo a semana) ....... {warmup_days} dias "
      f"(= {warmup_days*24} h)")
print(f">> Persistido en {U.WARMUP_FILE}")
print(f"\nThroughput primeros 21 dias (suavizado):")
print(thr_s.loc[:20].round(1).to_string())

# --- Figura ---
fig, axes = plt.subplots(2, 1, figsize=(11, 7), sharex=True)
for ax, raw, smooth, title, ylab in [
        (axes[0], thr, thr_s, "Throughput diario de la linea (volumen terminado)", "m3/dia"),
        (axes[1], wip, wip_s, "WIP total del sistema (suma de buffers)", "m3")]:
    ax.plot(days, raw, color="#90caf9", lw=0.8, label="promedio 5 replicas")
    ax.plot(days, smooth, color="#0d47a1", lw=2, label=f"media movil {W}d")
    ax.axvspan(0, warmup_days, color="#c62828", alpha=0.10)
    ax.axvline(warmup_days, color="#c62828", ls="--",
               label=f"corte warm-up = {warmup_days} d")
    ax.set_ylabel(ylab)
    ax.set_title(title)
    ax.legend(loc="lower right", fontsize=8)
axes[0].axhline(mu, color="#2e7d32", ls=":", lw=1)
axes[1].set_xlabel("Dia del horizonte")
fig.suptitle("Metodo de Welch - deteccion del periodo de calentamiento", y=0.99)
fig.tight_layout()
fig.savefig(U.OUT / "figuras" / "warmup_welch.png", dpi=120)
plt.close(fig)
print(f">> Guardado: {U.OUT/'figuras'/'warmup_welch.png'}")
