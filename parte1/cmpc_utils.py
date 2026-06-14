"""
cmpc_utils.py
=================================================================
Modulo compartido - Caso de Estudio CMPC Mulchen (Parte 1)
=================================================================
Centraliza rutas, carga de datos, clasificacion de estaciones y
utilidades de calendario/turnos para que todos los scripts de
analisis usen exactamente los mismos supuestos.
"""

from pathlib import Path
import numpy as np
import pandas as pd

# ----------------------------------------------------------------------
# Rutas
# ----------------------------------------------------------------------
BASE = Path(__file__).resolve().parent.parent       # .../Tareas
DATA = BASE / "data"
OUT = BASE / "parte1" / "output"
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "figuras").mkdir(parents=True, exist_ok=True)
(OUT / "tablas").mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------
# Convenciones del sistema productivo (segun PDF "Caso de Estudio")
# ----------------------------------------------------------------------
# Estaciones que respetan el calendario de turnos (solo inician lotes
# dentro de las horas operativas planificadas):
SHIFT_STATIONS = ["aserradero", "bano", "drymill"]
# Estaciones que operan de forma continua 24/7 (pueden iniciar/operar
# en cualquier momento, incluso fuera de turno y dias no operativos):
CONTINUOUS_STATIONS = ["secado", "impregnado"]
ALL_STATIONS = ["aserradero", "bano", "secado", "drymill", "impregnado"]

# Orden fisico de la linea (aguas arriba -> aguas abajo)
LINE_ORDER = ["aserradero", "bano", "secado", "drymill", "impregnado"]

# Ruteo de productos (PDF):
ROUTES = {
    "P1": ["aserradero", "bano"],                                  # madera verde tratada
    "P2": ["aserradero", "secado", "drymill"],                     # madera seca clasificada
    "P3": ["aserradero", "secado", "drymill", "impregnado"],       # madera impregnada
}

# Estados posibles en station_events
STATES = ["BUSY", "SETUP", "IDLE", "BLOCKED", "DOWN", "OFF_SHIFT"]
# Estados que cuentan como "tiempo disponible programado" (no off-shift)
SCHEDULED_STATES = ["BUSY", "SETUP", "IDLE", "BLOCKED", "DOWN"]

HORIZON_H = 8760.0       # 365 dias * 24 h
HOURS_PER_DAY = 24.0

# Periodo de calentamiento (warm-up). El PDF indica que se descartan
# las primeras warmup_days*24 h, pero parameters.csv NO fue entregado.
# Se deja configurable; por defecto None (sin descarte) hasta confirmar.
WARMUP_DAYS = None       # <-- ajustar cuando se confirme el valor real


# ----------------------------------------------------------------------
# Carga de datos
# ----------------------------------------------------------------------
def load_all():
    """Carga todos los CSV disponibles en un dict de DataFrames."""
    dfs = {}
    for path in sorted(DATA.glob("*.csv")):
        dfs[path.stem] = pd.read_csv(path)
    return dfs


def load(name):
    return pd.read_csv(DATA / f"{name}.csv")


# ----------------------------------------------------------------------
# Utilidades de calendario / turnos
# ----------------------------------------------------------------------
def day_of(time_h):
    """Dia del horizonte (0..364) al que pertenece un instante absoluto."""
    return np.floor(np.asarray(time_h, dtype=float) / HOURS_PER_DAY).astype(int)


def attach_calendar(df, time_col, calendar):
    """
    A un DataFrame con una columna de tiempo absoluto le adjunta la
    informacion de calendario del dia correspondiente y banderas de
    ventana operativa.

    Devuelve copia con columnas nuevas:
      day, is_operating_day, planned_operating_hours,
      shift_open_time_h, shift_close_time_h,
      in_operating_day, in_shift_window, outside_operating_window
    """
    out = df.copy()
    out["day"] = day_of(out[time_col])
    cal = calendar[["day", "is_operating_day", "planned_operating_hours",
                    "shift_open_time_h", "shift_close_time_h"]]
    out = out.merge(cal, on="day", how="left")

    t = out[time_col].to_numpy()
    is_op = out["is_operating_day"].fillna(False).to_numpy()
    open_h = out["shift_open_time_h"].to_numpy()
    close_h = out["shift_close_time_h"].to_numpy()

    tol = 1e-9
    in_window = is_op & (t >= open_h - tol) & (t <= close_h + tol)
    out["in_operating_day"] = is_op
    out["in_shift_window"] = in_window
    out["outside_operating_window"] = ~in_window
    return out


def hour_of_day(time_h):
    """Hora del dia [0,24) de un instante absoluto."""
    return np.mod(np.asarray(time_h, dtype=float), HOURS_PER_DAY)


def state_at(events, rep, station, t, before=True):
    """
    Devuelve el estado de (rep, station) en el instante t.
    before=True usa t- (estado JUSTO ANTES de t), util para saber
    que hacia la maquina cuando se gatillo una falla en t.
    """
    eps = 1e-6 if before else 0.0
    tq = t - eps
    sub = events[(events["replication"] == rep) & (events["station"] == station)]
    hit = sub[(sub["start_time_h"] <= tq) & (sub["end_time_h"] > tq)]
    if len(hit):
        return hit.iloc[0]["state"]
    return None


def reps(df):
    return sorted(df["replication"].unique())


# ----------------------------------------------------------------------
# Warm-up (periodo de calentamiento) - persistido en disco para que
# todos los scripts usen el mismo valor detectado por Welch (script 02).
# ----------------------------------------------------------------------
WARMUP_FILE = OUT / "warmup_days.txt"


def set_warmup_days(n):
    WARMUP_FILE.write_text(str(int(n)), encoding="utf-8")


def get_warmup_days(default=0):
    if WARMUP_FILE.exists():
        try:
            return int(WARMUP_FILE.read_text().strip())
        except ValueError:
            return default
    return default


def warmup_start_h():
    return get_warmup_days() * HOURS_PER_DAY


# ----------------------------------------------------------------------
# Descomposicion de tiempos por estado (con recorte de warm-up)
# ----------------------------------------------------------------------
def state_durations(events, warmup_h=None, horizon_h=HORIZON_H):
    """
    Horas por (replication, station, state) en el periodo estacionario
    [warmup_h, horizon_h]. Recorta los intervalos que cruzan el limite de
    warm-up para contar solo la fraccion estacionaria.
    """
    if warmup_h is None:
        warmup_h = warmup_start_h()
    e = events.copy()
    start = np.maximum(e["start_time_h"].to_numpy(), warmup_h)
    end = np.minimum(e["end_time_h"].to_numpy(), horizon_h)
    e["dur_h"] = np.clip(end - start, 0, None)
    e = e[e["dur_h"] > 0]
    return (e.groupby(["replication", "station", "state"])["dur_h"]
            .sum().reset_index())


def state_matrix(events, warmup_h=None):
    """Pivot (replication, station) x state -> horas. Columnas en orden STATES."""
    g = state_durations(events, warmup_h)
    m = (g.pivot_table(index=["replication", "station"], columns="state",
                       values="dur_h", aggfunc="sum")
         .reindex(columns=STATES).fillna(0.0))
    return m
