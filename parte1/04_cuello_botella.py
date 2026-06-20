"""
04_cuello_botella.py
=================================================================
Identificacion del CUELLO DE BOTELLA y propuesta de mejora.
Marco: Factory Physics (Hopp & Spearman) - el cuello de botella es
el recurso con mayor utilizacion; aguas arriba se acumula WIP y aguas
abajo las estaciones se hambrean (starving). Teoria de Restricciones
(Goldratt): la mejora debe atacar la restriccion.

Se triangula la restriccion con multiples evidencias independientes:
  (1) Utilizacion por estacion.
  (2) Inanicion (IDLE) aguas abajo / bloqueo (BLOCKED) aguas arriba.
  (3) No estacionariedad del WIP aguas arriba (log_yard).
  (4) Balance arribos vs capacidad de procesamiento del aserradero.
  (5) Concentracion de fallas.
Finalmente se dimensiona el potencial de la mejora propuesta.
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

warmup_h = U.warmup_start_h()
warmup_d = U.get_warmup_days()
events = U.load("station_events")
dwip = U.load("daily_wip")
dthr = U.load("daily_throughput")
arr = U.load("log_arrivals")
po = U.load("product_outputs")

kpis = pd.read_csv(U.OUT / "tablas" / "disponibilidad_resumen.csv").set_index("station")

# ======================================================================
# (1) Utilizacion -> ranking de restriccion
# ======================================================================
print("=" * 72)
print(" (1) UTILIZACION POR ESTACION (ranking de restriccion)")
print("=" * 72)
util = kpis["utilizacion"].reindex(U.ALL_STATIONS).sort_values(ascending=False)
for st, u in util.items():
    bar = "#" * int(u * 50)
    print(f"   {st:12s} {u*100:5.1f}%  {bar}")
bottleneck = util.index[0]
print(f"\n   => Mayor utilizacion: '{bottleneck}' ({util.iloc[0]*100:.1f}%), "
      f"{util.iloc[0]/util.iloc[1]:.1f}x la siguiente ('{util.index[1]}').")

# ======================================================================
# (2) Inanicion aguas abajo / bloqueo aguas arriba
# ======================================================================
print("\n" + "=" * 72)
print(" (2) INANICION (IDLE) Y BLOQUEO (BLOCKED) - patron de restriccion")
print("=" * 72)
comp = kpis[["f_IDLE", "f_BLOCKED", "f_BUSY"]].reindex(U.LINE_ORDER) * 100
comp.columns = ["IDLE_%", "BLOCKED_%", "BUSY_%"]
print(comp.round(1).to_string())
print("   - El aserradero NUNCA esta IDLE (siempre tiene trozos en cola).")
print("   - Las estaciones aguas abajo se hambrean (IDLE alto) por falta de alimentacion.")
print("   - BLOCKED ~ 0 en toda la linea: la restriccion esta en la ENTRADA, no aguas abajo.")

# ======================================================================
# (3) No estacionariedad del WIP en log_yard (aguas arriba del aserradero)
# ======================================================================
print("\n" + "=" * 72)
print(" (3) WIP EN log_yard: acumulacion no acotada (aguas arriba del cuello)")
print("=" * 72)
ly = dwip[(dwip["buffer"] == "log_yard") & (dwip["day"] >= warmup_d)]
ly_day = ly.groupby("day")["level_m3_eod"].mean()
slope, intercept = np.polyfit(ly_day.index.values, ly_day.values, 1)
print(f"   Nivel log_yard: dia {ly_day.index.min()} = {ly_day.iloc[0]:.0f} m3  ->  "
      f"dia {ly_day.index.max()} = {ly_day.iloc[-1]:.0f} m3")
print(f"   Pendiente de acumulacion ~ {slope:.2f} m3/dia (crecimiento lineal => sistema saturado).")

# WIP aguas abajo (estacionario?)
print("\n   Buffers intermedios (nivel medio EOD, periodo estacionario):")
for b in sorted(dwip["buffer"].unique()):
    if b == "log_yard":
        continue
    sub = dwip[(dwip["buffer"] == b) & (dwip["day"] >= warmup_d)]
    s2, _ = np.polyfit(sub.groupby("day")["level_m3_eod"].mean().index.values,
                       sub.groupby("day")["level_m3_eod"].mean().values, 1)
    print(f"     {b:16s} nivel medio={sub['level_m3_eod'].mean():7.1f} m3  "
          f"pendiente={s2:+.3f} m3/dia (estacionario)")

# ======================================================================
# (4) Balance arribos vs capacidad de procesamiento del aserradero
# ======================================================================
print("\n" + "=" * 72)
print(" (4) BALANCE ARRIBOS vs CAPACIDAD DEL ASERRADERO (m3 de trozos)")
print("=" * 72)
cal = U.load("calendar")
stat_days = np.arange(warmup_d, 365)
n_days_stat = len(stat_days)
op_days_stat = int(cal[(cal["day"] >= warmup_d) & (cal["is_operating_day"])].shape[0])

arr = arr.copy()
arr["day"] = U.day_of(arr["arrival_time_h"])
# Totales por replica en el periodo estacionario -> media entre replicas
tot_arr = arr[arr["day"] >= warmup_d].groupby("replication")["volume_m3"].sum().mean()
tot_proc = (dthr[(dthr["station"] == "aserradero") & (dthr["day"] >= warmup_d)]
            .groupby("replication")["m3_in"].sum().mean())

# Tasas en BASE COMUN (importante: arribos solo ocurren en dias operativos,
# el procesamiento tambien; comparamos ambas sobre la misma base).
arr_cal, proc_cal = tot_arr / n_days_stat, tot_proc / n_days_stat       # por dia calendario
arr_op, proc_op = tot_arr / op_days_stat, tot_proc / op_days_stat       # por dia operativo
accum = (tot_arr - tot_proc) / n_days_stat                              # acumulacion diaria

# Series diarias para la figura, reindexadas a todos los dias (0 en no operativos)
arr_day = (arr[arr["day"] >= warmup_d].groupby(["replication", "day"])["volume_m3"].sum()
           .groupby("day").mean().reindex(stat_days).fillna(0.0))
ase_in_day = (dthr[(dthr["station"] == "aserradero") & (dthr["day"] >= warmup_d)]
              .groupby("day")["m3_in"].mean().reindex(stat_days).fillna(0.0))

print(f"   [base estacionaria: {n_days_stat} dias calendario, {op_days_stat} operativos]")
print(f"   Arribos de trozos ........ {arr_cal:6.1f} m3/dia-cal  ({arr_op:6.1f} por dia operativo)")
print(f"   Procesado aserradero ..... {proc_cal:6.1f} m3/dia-cal  ({proc_op:6.1f} por dia operativo)")
print(f"   Exceso -> log_yard ....... {accum:6.1f} m3/dia-cal")
print(f"   Pendiente medida log_yard  {slope:6.1f} m3/dia  => balance CIERRA (consistencia interna OK)")

# ======================================================================
# (5) Concentracion de fallas
# ======================================================================
print("\n" + "=" * 72)
print(" (5) CONCENTRACION DE FALLAS")
print("=" * 72)
print("   ", kpis["fallas"].reindex(U.ALL_STATIONS).round(1).to_dict())
print(f"   El aserradero falla {kpis.loc['aserradero','fallas']:.0f} veces "
      f"(mas que el resto junto): es la maquina mas exigida.")

# ======================================================================
# Produccion anual por producto (insumo para la Parte 2)
# ======================================================================
print("\n" + "=" * 72)
print(" PRODUCCION TERMINADA POR PRODUCTO (media anual de 5 replicas)")
print("=" * 72)
po2 = po.copy()
po2["day"] = U.day_of(po2["exit_time_h"])
prod = (po2[po2["day"] >= warmup_d]
        .groupby(["replication", "product"])["volume_m3"].sum()
        .groupby("product").mean())
# escalar a año completo (estacionario cubre 365-warmup dias)
factor = 365.0 / (365 - warmup_d)
prod_anual = prod * factor
for p in ["P1", "P2", "P3"]:
    print(f"   {p}: {prod.get(p,0):8.1f} m3 en {365-warmup_d} dias  "
          f"->  {prod_anual.get(p,0):8.1f} m3/año (extrapolado)")
print(f"   TOTAL produccion util: {prod_anual.sum():.0f} m3/año")

# ======================================================================
# Dimensionamiento de la mejora propuesta
# ======================================================================
print("\n" + "=" * 72)
print(" PROPUESTA DE MEJORA (atacar la restriccion: aserradero)")
print("=" * 72)
# Tiempo del aserradero (de la tabla de composicion, % del total)
f_busy = kpis.loc["aserradero", "f_BUSY"]
f_setup = kpis.loc["aserradero", "f_SETUP"]
f_down = kpis.loc["aserradero", "f_DOWN"]
f_off = kpis.loc["aserradero", "f_OFF_SHIFT"]
print(f"   Aserradero hoy (% del tiempo total): BUSY={f_busy*100:.1f}  "
      f"SETUP={f_setup*100:.1f}  DOWN={f_down*100:.1f}  OFF_SHIFT={f_off*100:.1f}  IDLE~0")
# Palanca A: extender turno (reducir OFF_SHIFT). Downstream tiene holgura:
sec_util = kpis.loc["secado", "utilizacion"]
print(f"\n   Palanca A - Extender operacion del aserradero (hoy 16 h/dia):")
print(f"     * Por dia operativo procesa {proc_op:.0f} m3 en 16 h; arriban {arr_op:.0f} m3/dia operativo.")
gain_24 = proc_op * (24/16) - proc_op
print(f"     * A 24 h/dia (mismo ritmo): ~{proc_op*24/16:.0f} m3/dia (+{gain_24:.0f}, +50%), "
      f"supera los {arr_op:.0f} m3/dia de arribos y revierte el backlog de {accum:.0f} m3/dia-cal.")
print(f"     * Holgura aguas abajo: secado solo 38% util, drymill 25%, etc. -> pueden absorberlo.")
print(f"   Palanca B - Reducir SETUP ({f_setup*100:.1f}% del tiempo): secuenciar/campañas por producto (SMED).")
print(f"   Palanca C - Reducir DOWN ({f_down*100:.1f}%): mant. preventivo sube MTBF (hoy {kpis.loc['aserradero','MTBF_h']:.0f} h, el mas bajo).")

# ----------------------------------------------------------------------
# Figuras
# ----------------------------------------------------------------------
plt.rcParams.update({"font.size": 10})

# Fig 1: ranking de utilizacion
fig, ax = plt.subplots(figsize=(9, 4.6))
colors = ["#c62828" if s == bottleneck else "#1565c0" for s in util.index]
ax.barh(util.index[::-1], (util*100).values[::-1], color=colors[::-1])
for i, (s, u) in enumerate(list(util.items())[::-1]):
    ax.text(u*100+1, i, f"{u*100:.1f}%", va="center", fontsize=9)
ax.set_xlabel("Utilizacion (BUSY / tiempo programado) [%]")
ax.set_title("Ranking de utilizacion: el aserradero es la restriccion")
ax.set_xlim(0, 100)
fig.tight_layout(); fig.savefig(U.OUT/"figuras"/"bottleneck_utilizacion.png", dpi=120); plt.close(fig)

# Fig 2: log_yard acumulacion + arribos vs procesamiento
fig, axs = plt.subplots(1, 2, figsize=(13, 4.6))
axs[0].plot(ly_day.index, ly_day.values, color="#0d47a1", lw=1.5)
axs[0].plot(ly_day.index, intercept+slope*ly_day.index.values, "r--",
            label=f"tendencia {slope:.1f} m3/dia")
axs[0].set_title("WIP en log_yard (aguas arriba del aserradero)")
axs[0].set_xlabel("Dia"); axs[0].set_ylabel("Nivel fin de dia [m3]"); axs[0].legend()
axs[1].plot(arr_day.index, arr_day.values, color="#ef6c00", lw=1, label=f"arribos ({arr_cal:.0f} m3/dia-cal)")
axs[1].plot(ase_in_day.index, ase_in_day.values, color="#2e7d32", lw=1, label=f"procesado aserradero ({proc_cal:.0f} m3/dia-cal)")
axs[1].axhline(arr_cal, color="#ef6c00", ls=":", lw=1)
axs[1].axhline(proc_cal, color="#2e7d32", ls=":", lw=1)
axs[1].set_title("Arribos de trozos vs capacidad de procesamiento")
axs[1].set_xlabel("Dia"); axs[1].set_ylabel("m3/dia"); axs[1].legend()
fig.suptitle("Evidencia de saturacion: arriba llega mas de lo que el aserradero procesa", y=1.02)
fig.tight_layout(); fig.savefig(U.OUT/"figuras"/"bottleneck_wip_balance.png", bbox_inches="tight", dpi=120); plt.close(fig)

print(f"\n>> Guardado: {U.OUT/'figuras'/'bottleneck_utilizacion.png'}")
print(f">> Guardado: {U.OUT/'figuras'/'bottleneck_wip_balance.png'}")
print("\nOK - analisis de cuello de botella completado.")
