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
# Warm-up (periodo de calentamiento). Se almacena en HORAS para soportar
# el corte del Apunte de ideas (185.75 h, por estabilizacion de
# batch_volume_m3). warmup_start_h() es la unica fuente de verdad que
# usan todos los analisis; los intervalos que cruzan el corte se recortan.
# ----------------------------------------------------------------------
WARMUP_APUNTE_H = 185.75                # Apunte (estabilizacion batch_volume_m3)
WARMUP_INTER_H = 216.0                  # ~9 d: cubre la replica/estacion mas lenta (bano/impregnado ~210 h)
WARMUP_WELCH_H = 336.0                  # ~14 d: criterio Welch conservador (salida ensemble)
DEFAULT_WARMUP_H = WARMUP_INTER_H       # principal adoptado (decision del usuario)
WARMUP_H_FILE = OUT / "warmup_h.txt"
WARMUP_FILE = OUT / "warmup_days.txt"   # compatibilidad hacia atras (valor antiguo en dias)


def set_warmup_hours(h):
    WARMUP_H_FILE.write_text(repr(float(h)), encoding="utf-8")


def get_warmup_hours(default=DEFAULT_WARMUP_H):
    if WARMUP_H_FILE.exists():
        try:
            return float(WARMUP_H_FILE.read_text().strip())
        except ValueError:
            pass
    if WARMUP_FILE.exists():
        try:
            return int(WARMUP_FILE.read_text().strip()) * HOURS_PER_DAY
        except ValueError:
            pass
    return default


def set_warmup_days(n):                  # compatibilidad
    set_warmup_hours(float(n) * HOURS_PER_DAY)


def get_warmup_days(default=0):
    """Dia de corte para mallas diarias (ceil de las horas de warm-up)."""
    return int(np.ceil(get_warmup_hours() / HOURS_PER_DAY))


def warmup_start_h():
    return get_warmup_hours()


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


# ----------------------------------------------------------------------
# Helpers Factory Physics (Hopp & Spearman) - operan sobre state_matrix
# Convencion del Apunte: OFF_SHIFT se EXCLUYE de los denominadores.
# ----------------------------------------------------------------------
REQUIRED_STATES = ["BUSY", "DOWN", "IDLE", "SETUP", "BLOCKED"]   # tiempo requerido (sin OFF_SHIFT)
AVAIL_UP_STATES = ["BUSY", "IDLE", "SETUP", "BLOCKED"]           # "arriba" (todo salvo DOWN)


def required_time(m):
    """Tiempo requerido = BUSY+DOWN+IDLE+SETUP+BLOCKED (excluye OFF_SHIFT)."""
    return m[REQUIRED_STATES].sum(axis=1)


def availability_fp(m):
    """Disponibilidad operacional (Apunte/FP) = (req - DOWN)/req."""
    req = required_time(m)
    return np.where(req > 0, m[AVAIL_UP_STATES].sum(axis=1) / req, np.nan)


def availability_inherent(m):
    """Disponibilidad inherente = BUSY/(BUSY+DOWN) = MTBF/(MTBF+MTTR)."""
    den = m["BUSY"] + m["DOWN"]
    return np.where(den > 0, m["BUSY"] / den, np.nan)


def load_parametros():
    """Parametros de demanda/capacidad por nodo (parametros_demanda.json)."""
    import json
    p = BASE / "parte1" / "parametros_demanda.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
