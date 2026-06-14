"""
01_validacion_fallas.py
=================================================================
VALIDACION: "No tiene sentido que las maquinas fallen fuera de
horario laboral / en dias que no se trabaja."
=================================================================
El PDF establece que una falla "ocurre DURANTE el procesamiento de
un lote y detiene la operacion". Por lo tanto:

  * Estaciones que respetan turno (aserradero, bano, drymill):
    solo procesan dentro de la ventana operativa -> NO deberian
    registrar fallas fuera de turno ni en dias no operativos.

  * Estaciones 24/7 (secado, impregnado): operan de forma continua,
    por lo que SI pueden fallar fuera de turno / en dias no operativos
    de manera legitima.

Este script cruza failures.csv con calendar.csv (ventana operativa) y
con station_events.csv (estado real de la maquina en el instante de la
falla) para cuantificar y clasificar las inconsistencias.
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import cmpc_utils as U

pd.set_option("display.width", 160)
pd.set_option("display.max_columns", 40)

print("=" * 72)
print(" VALIDACION DE FALLAS vs CALENDARIO Y ESTADO DE MAQUINA")
print("=" * 72)

calendar = U.load("calendar")
failures = U.load("failures").copy()
events = U.load("station_events")

# ----------------------------------------------------------------------
# 0) Confirmar empiricamente que estaciones respetan turno
#    (presencia del estado OFF_SHIFT en station_events)
# ----------------------------------------------------------------------
off = (events[events["state"] == "OFF_SHIFT"]
       .groupby("station").size().reindex(U.ALL_STATIONS, fill_value=0))
print("\n[0] Intervalos OFF_SHIFT por estacion (confirma quien respeta turno):")
for st in U.ALL_STATIONS:
    tipo = "24/7" if st in U.CONTINUOUS_STATIONS else "turno"
    print(f"     {st:12s} OFF_SHIFT={int(off[st]):6d}   (clasificada como {tipo})")

# ----------------------------------------------------------------------
# 1) Adjuntar calendario y banderas de ventana operativa a cada falla
# ----------------------------------------------------------------------
fa = U.attach_calendar(failures, "failure_time_h", calendar)
fa["hour_of_day"] = U.hour_of_day(fa["failure_time_h"])
fa["station_type"] = np.where(fa["station"].isin(U.CONTINUOUS_STATIONS),
                              "24/7", "turno")

# Clasificacion de cada falla respecto de la ventana operativa
def clasifica(row):
    if not row["in_operating_day"]:
        return "DIA_NO_OPERATIVO"
    if not row["in_shift_window"]:
        return "FUERA_DE_TURNO"
    return "EN_TURNO"

fa["clasificacion_ventana"] = fa.apply(clasifica, axis=1)

# ----------------------------------------------------------------------
# 2) Estado real de la maquina justo ANTES de la falla
# ----------------------------------------------------------------------
ev_sorted = events.sort_values("start_time_h").reset_index(drop=True)
estados_prev = []
for _, r in fa.iterrows():
    estados_prev.append(
        U.state_at(ev_sorted, r["replication"], r["station"],
                   r["failure_time_h"], before=True))
fa["estado_pre_falla"] = estados_prev

# ----------------------------------------------------------------------
# 3) Resumen global
# ----------------------------------------------------------------------
print("\n[1] Clasificacion de TODAS las fallas segun ventana operativa:")
print(fa["clasificacion_ventana"].value_counts().to_string())

print("\n[2] Tabla cruzada estacion x clasificacion (conteo de fallas):")
tab = pd.crosstab(fa["station"], fa["clasificacion_ventana"])
tab = tab.reindex(U.ALL_STATIONS).fillna(0).astype(int)
# asegurar columnas
for c in ["EN_TURNO", "FUERA_DE_TURNO", "DIA_NO_OPERATIVO"]:
    if c not in tab.columns:
        tab[c] = 0
tab = tab[["EN_TURNO", "FUERA_DE_TURNO", "DIA_NO_OPERATIVO"]]
tab["TOTAL"] = tab.sum(axis=1)
tab["tipo"] = [("24/7" if s in U.CONTINUOUS_STATIONS else "turno") for s in tab.index]
print(tab.to_string())

# ----------------------------------------------------------------------
# 4) EL HALLAZGO CLAVE: fallas "imposibles" = estaciones de turno que
#    fallan fuera de la ventana operativa
# ----------------------------------------------------------------------
anomalas = fa[(fa["station_type"] == "turno") &
              (fa["clasificacion_ventana"] != "EN_TURNO")]
ok_turno = fa[(fa["station_type"] == "turno") &
              (fa["clasificacion_ventana"] == "EN_TURNO")]
n_turno = (fa["station_type"] == "turno").sum()

print("\n" + "=" * 72)
print(" [3] HALLAZGO PRINCIPAL")
print("=" * 72)
print(f"Fallas en estaciones de TURNO (aserradero/bano/drymill): {n_turno}")
print(f"  - dentro de turno (esperable) ............. {len(ok_turno)}")
print(f"  - FUERA de la ventana operativa (ANOMALAS): {len(anomalas)}"
      f"  ({len(anomalas)/max(n_turno,1)*100:.1f}%)")
print("\n    Desglose de las anomalas:")
print("   ", anomalas["clasificacion_ventana"].value_counts().to_dict())
print("\n    Estado de la maquina JUSTO ANTES de esas fallas anomalas:")
print("   ", anomalas["estado_pre_falla"].value_counts(dropna=False).to_dict())

# Comparacion: las 24/7 fuera de turno son legitimas
cont = fa[fa["station_type"] == "24/7"]
cont_fuera = cont[cont["clasificacion_ventana"] != "EN_TURNO"]
print(f"\nContraste - estaciones 24/7 (secado/impregnado): {len(cont)} fallas, "
      f"de las cuales {len(cont_fuera)} fuera de turno (LEGITIMAS por operar continuo).")

# ----------------------------------------------------------------------
# 5) Cruce con estado real: fallas que ocurren mientras la maquina
#    NO estaba operando (OFF_SHIFT / IDLE) -> inconsistencia fisica
# ----------------------------------------------------------------------
print("\n[4] Estado de la maquina justo ANTES de la falla (todas las estaciones):")
print(pd.crosstab(fa["station"], fa["estado_pre_falla"], dropna=False)
      .reindex(U.ALL_STATIONS).fillna(0).astype(int).to_string())

# ----------------------------------------------------------------------
# 6) Guardar resultados
# ----------------------------------------------------------------------
cols_out = ["replication", "station", "station_type", "failure_time_h", "day",
            "hour_of_day", "repair_duration_h", "is_operating_day",
            "planned_operating_hours", "shift_open_time_h", "shift_close_time_h",
            "clasificacion_ventana", "estado_pre_falla"]
fa[cols_out].to_csv(U.OUT / "tablas" / "fallas_clasificadas.csv", index=False)
tab.to_csv(U.OUT / "tablas" / "fallas_estacion_x_ventana.csv")
print(f"\n>> Guardado: {U.OUT/'tablas'/'fallas_clasificadas.csv'}")
print(f">> Guardado: {U.OUT/'tablas'/'fallas_estacion_x_ventana.csv'}")

# ----------------------------------------------------------------------
# 7) Figuras
# ----------------------------------------------------------------------
plt.rcParams.update({"font.size": 10, "figure.dpi": 110})

# --- Fig A: barras apiladas por estacion ---
fig, ax = plt.subplots(figsize=(9, 5))
plot_tab = tab[["EN_TURNO", "FUERA_DE_TURNO", "DIA_NO_OPERATIVO"]]
colors = ["#2e7d32", "#ef6c00", "#c62828"]
bottom = np.zeros(len(plot_tab))
x = np.arange(len(plot_tab))
for col, col_c in zip(plot_tab.columns, colors):
    ax.bar(x, plot_tab[col], bottom=bottom, label=col, color=col_c)
    bottom += plot_tab[col].to_numpy()
ax.set_xticks(x)
ax.set_xticklabels([f"{s}\n({'24/7' if s in U.CONTINUOUS_STATIONS else 'turno'})"
                    for s in plot_tab.index])
ax.set_ylabel("N de fallas (5 replicas)")
ax.set_title("Fallas por estacion segun ventana operativa\n"
             "(rojo/naranja en aserradero-bano-drymill = inconsistencia)")
ax.legend(title="Momento de la falla")
fig.tight_layout()
fig.savefig(U.OUT / "figuras" / "fallas_por_ventana.png")
plt.close(fig)

# --- Fig B: hora del dia de la falla (turno vs 24/7) ---
fig, axs = plt.subplots(1, 2, figsize=(12, 4.5), sharey=True)
for ax, tipo, sts in zip(
        axs, ["turno", "24/7"], [U.SHIFT_STATIONS, U.CONTINUOUS_STATIONS]):
    d = fa[fa["station"].isin(sts)]
    ax.hist(d["hour_of_day"], bins=np.arange(0, 25, 1),
            color="#1565c0", edgecolor="white")
    ax.axvspan(7, 23, color="#2e7d32", alpha=0.12, label="ventana 07-23")
    ax.set_title(f"Estaciones {tipo}: {', '.join(sts)}")
    ax.set_xlabel("Hora del dia de la falla (failure_time_h mod 24)")
    ax.set_xticks(range(0, 25, 2))
    ax.legend()
axs[0].set_ylabel("N de fallas")
fig.suptitle("Distribucion horaria de las fallas: las de TURNO deberian caer solo en 07-23",
             y=1.02)
fig.tight_layout()
fig.savefig(U.OUT / "figuras" / "fallas_hora_del_dia.png", bbox_inches="tight")
plt.close(fig)

print(f">> Guardado: {U.OUT/'figuras'/'fallas_por_ventana.png'}")
print(f">> Guardado: {U.OUT/'figuras'/'fallas_hora_del_dia.png'}")
print("\nOK - validacion de fallas completada.")
