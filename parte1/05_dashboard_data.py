"""
05_dashboard_data.py
=================================================================
Calcula TODAS las metricas de la Parte 1 (por replica + agregados
media/IC95%) y las deja en un unico dict serializable a JSON, que
luego consume 05_dashboard_build.py para generar el HTML.
=================================================================
"""
import json
import numpy as np
import pandas as pd
import cmpc_utils as U

TCRIT = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571}
NREPS = 5
warmup_d = U.get_warmup_days()
warmup_h = U.warmup_start_h()
STAT_DAYS = 365 - warmup_d
ANN = 365.0 / STAT_DAYS                       # factor de anualizacion
DAYS = list(range(365))


def ci(vals):
    v = np.asarray(vals, float)
    v = v[~np.isnan(v)]
    if len(v) < 2:
        return float(v.mean()) if len(v) else 0.0, 0.0
    return float(v.mean()), float(TCRIT.get(len(v) - 1, 1.96) * v.std(ddof=1) / np.sqrt(len(v)))


def f(x):
    return None if (x is None or (isinstance(x, float) and np.isnan(x))) else float(x)


# ----------------------------------------------------------------------
# Carga
# ----------------------------------------------------------------------
events = U.load("station_events")
batches = U.load("batches")
failures = U.load("failures")
po = U.load("product_outputs")
dwip = U.load("daily_wip")
dthr = U.load("daily_throughput")
arr = U.load("log_arrivals")
cal = U.load("calendar")

# Tablas de fallas ya clasificadas (scripts 01/01b)
fcls = pd.read_csv(U.OUT / "tablas" / "fallas_clasificadas.csv")
fdiag = pd.read_csv(U.OUT / "tablas" / "fallas_anomalas_diagnostico.csv")

# ----------------------------------------------------------------------
# Bloques por (rep, station)
# ----------------------------------------------------------------------
M = U.state_matrix(events, warmup_h).reset_index()          # rep,station, estados
M["TOTAL"] = M[U.STATES].sum(axis=1)
M["SCHEDULED"] = M["TOTAL"] - M["OFF_SHIFT"]
M["util"] = M["BUSY"] / M["SCHEDULED"]
M["disp"] = np.where(M["BUSY"] + M["DOWN"] > 0, M["BUSY"] / (M["BUSY"] + M["DOWN"]), np.nan)

fa = failures[failures["failure_time_h"] >= warmup_h]
nfail = fa.groupby(["replication", "station"]).size().rename("nfail")
mttr = fa.groupby(["replication", "station"])["repair_duration_h"].mean().rename("mttr")

bst = batches[batches["start_process_time_h"] >= warmup_h]
yld = bst.groupby(["replication", "station"])[["volume_in_m3", "volume_out_m3"]].sum()
yld["yield"] = yld["volume_out_m3"] / yld["volume_in_m3"]

M = (M.set_index(["replication", "station"])
     .join(nfail).join(mttr).join(yld["yield"]).reset_index())
M["nfail"] = M["nfail"].fillna(0)
M["mtbf"] = np.where(M["nfail"] > 0, M["BUSY"] / M["nfail"], np.nan)
M["oee"] = M["disp"] * np.where(M["BUSY"] + M["SETUP"] > 0,
                                M["BUSY"] / (M["BUSY"] + M["SETUP"]), 0) * M["yield"]

# ----------------------------------------------------------------------
# Sankey (volumenes por rep), anualizados
# ----------------------------------------------------------------------
def vout_by(station, product, rep):
    s = bst[(bst["replication"] == rep) & (bst["station"] == station) & (bst["product"] == product)]
    return s["volume_out_m3"].sum() * ANN

def agg_station(station, rep):
    s = bst[(bst["replication"] == rep) & (bst["station"] == station)]
    return (s["volume_in_m3"].sum() * ANN, s["volume_out_m3"].sum() * ANN, s["scrap_m3"].sum() * ANN)

SANKEY_LINKS = ["trozos>aserradero", "aserradero>Mermas", "aserradero>bano",
                "aserradero>secado", "bano>Mermas", "bano>P1", "secado>Mermas",
                "secado>drymill", "drymill>Mermas", "drymill>P2",
                "drymill>impregnado", "impregnado>Mermas", "impregnado>P3"]

def sankey_for(rep):
    ase_in, ase_out, ase_scr = agg_station("aserradero", rep)
    bano_in, bano_out, bano_scr = agg_station("bano", rep)
    sec_in, sec_out, sec_scr = agg_station("secado", rep)
    dry_in, dry_out, dry_scr = agg_station("drymill", rep)
    imp_in, imp_out, imp_scr = agg_station("impregnado", rep)
    ase_P1 = vout_by("aserradero", "P1", rep)
    ase_P2 = vout_by("aserradero", "P2", rep)
    ase_P3 = vout_by("aserradero", "P3", rep)
    dry_P2 = vout_by("drymill", "P2", rep)
    dry_P3 = vout_by("drymill", "P3", rep)
    return {
        "trozos>aserradero": ase_in, "aserradero>Mermas": ase_scr,
        "aserradero>bano": ase_P1, "aserradero>secado": ase_P2 + ase_P3,
        "bano>Mermas": bano_scr, "bano>P1": bano_out,
        "secado>Mermas": sec_scr, "secado>drymill": sec_out,
        "drymill>Mermas": dry_scr, "drymill>P2": dry_P2,
        "drymill>impregnado": dry_P3, "impregnado>Mermas": imp_scr,
        "impregnado>P3": imp_out,
    }

# ----------------------------------------------------------------------
# Produccion por producto + lead time (boxplot)
# ----------------------------------------------------------------------
pst = po.copy()
pst["day"] = U.day_of(pst["exit_time_h"])
pst = pst[pst["day"] >= warmup_d]

def boxstats(x):
    x = np.asarray(x, float)
    if len(x) == 0:
        return [0, 0, 0, 0, 0]
    return [float(np.percentile(x, p)) for p in (5, 25, 50, 75, 95)]

def production_for(rep_filter):
    sub = pst if rep_filter is None else pst[pst["replication"] == rep_filter]
    out = {"vol": {}, "lead": {}}
    for p in ["P1", "P2", "P3"]:
        sp = sub[sub["product"] == p]
        if rep_filter is None:   # media anual por replica
            vol = sp.groupby("replication")["volume_m3"].sum().mean() * ANN
        else:
            vol = sp["volume_m3"].sum() * ANN
        out["vol"][p] = f(vol)
        out["lead"][p] = boxstats(sp["lead_time_h"])
    return out

# ----------------------------------------------------------------------
# Series diarias por rep (nivel buffers, throughput, arribos, proc)
# ----------------------------------------------------------------------
BUFFERS = sorted(dwip["buffer"].unique())

def series_rep(rep):
    th = (po[po["replication"] == rep].assign(day=U.day_of(po[po["replication"] == rep]["exit_time_h"]))
          .groupby("day")["volume_m3"].sum().reindex(DAYS).fillna(0).tolist())
    wip = {}
    for b in BUFFERS:
        wip[b] = (dwip[(dwip["replication"] == rep) & (dwip["buffer"] == b)]
                  .set_index("day")["level_m3_eod"].reindex(DAYS).ffill().fillna(0).tolist())
    ar = (arr[arr["replication"] == rep].assign(day=U.day_of(arr[arr["replication"] == rep]["arrival_time_h"]))
          .groupby("day")["volume_m3"].sum().reindex(DAYS).fillna(0).tolist())
    ai = (dthr[(dthr["replication"] == rep) & (dthr["station"] == "aserradero")]
          .set_index("day")["m3_in"].reindex(DAYS).fillna(0).tolist())
    return {"throughput": th, "wip": wip, "arrivals": ar, "aserradero_in": ai}

# ----------------------------------------------------------------------
# Fallas: clasificacion + histograma horario, por rep
# ----------------------------------------------------------------------
fmerge = fcls.merge(
    fdiag[["replication", "station", "failure_time_h", "inicio_lote_en_turno"]],
    on=["replication", "station", "failure_time_h"], how="left")

def classify_row(r):
    if r["clasificacion_ventana"] == "EN_TURNO":
        return "en_turno"
    if r["station_type"] == "24/7":
        return "cont"
    return "overrun" if r["inicio_lote_en_turno"] is True or r["inicio_lote_en_turno"] == True else "borde"

fmerge["cat"] = fmerge.apply(classify_row, axis=1)

def failures_for(rep_filter):
    sub = fmerge if rep_filter is None else fmerge[fmerge["replication"] == rep_filter]
    div = NREPS if rep_filter is None else 1
    by_station = {s: f(sub[sub["station"] == s].shape[0] / div) for s in U.ALL_STATIONS}
    cats = {c: f(sub[sub["cat"] == c].shape[0] / div) for c in ["en_turno", "cont", "overrun", "borde"]}
    hour_turno = np.histogram(sub[sub["station_type"] == "turno"]["hour_of_day"], bins=np.arange(0, 25))[0] / div
    hour_cont = np.histogram(sub[sub["station_type"] == "24/7"]["hour_of_day"], bins=np.arange(0, 25))[0] / div
    return {"by_station": by_station, "cats": cats,
            "hour_turno": [f(x) for x in hour_turno], "hour_cont": [f(x) for x in hour_cont],
            "total": f(sub.shape[0] / div)}

# ----------------------------------------------------------------------
# Ensamblado de una "vista" (rep concreto o promedio)
# ----------------------------------------------------------------------
def station_block(rep_filter):
    rows = []
    for st in U.ALL_STATIONS:
        if rep_filter is None:
            d = M[M["station"] == st]
            rec = {"station": st, "tipo": "24/7" if st in U.CONTINUOUS_STATIONS else "turno"}
            for k in ["util", "disp", "mtbf", "mttr", "yield", "oee"]:
                m, h = ci(d[k]); rec[k] = f(m); rec[k + "_ci"] = f(h)
            rec["nfail"] = f(d["nfail"].mean())
            tot = d["TOTAL"].mean()
            for s in U.STATES:
                rec[s] = f(d[s].mean() / tot * 100)
        else:
            d = M[(M["station"] == st) & (M["replication"] == rep_filter)].iloc[0]
            rec = {"station": st, "tipo": "24/7" if st in U.CONTINUOUS_STATIONS else "turno"}
            for k in ["util", "disp", "mtbf", "mttr", "yield", "oee"]:
                rec[k] = f(d[k]); rec[k + "_ci"] = 0.0
            rec["nfail"] = f(d["nfail"])
            for s in U.STATES:
                rec[s] = f(d[s] / d["TOTAL"] * 100)
        rows.append(rec)
    return rows

def series_block(rep_filter):
    if rep_filter is not None:
        return series_rep(rep_filter)
    allr = [series_rep(r) for r in range(NREPS)]
    th = np.mean([a["throughput"] for a in allr], axis=0).tolist()
    ar = np.mean([a["arrivals"] for a in allr], axis=0).tolist()
    ai = np.mean([a["aserradero_in"] for a in allr], axis=0).tolist()
    wip = {b: np.mean([a["wip"][b] for a in allr], axis=0).tolist() for b in BUFFERS}
    return {"throughput": th, "wip": wip, "arrivals": ar, "aserradero_in": ai}

def kpis_block(rep_filter, stations, prod, series, fails):
    ase = next(s for s in stations if s["station"] == "aserradero")
    prod_total = sum(v for v in prod["vol"].values() if v)
    th_day = float(np.sum(series["throughput"][warmup_d:]) / STAT_DAYS)
    ly = series["wip"]["log_yard"]
    slope = float(np.polyfit(range(warmup_d, 365), ly[warmup_d:], 1)[0])
    leadp3 = prod["lead"]["P3"][2]  # mediana P3
    k = {"prod_total": f(prod_total), "throughput_dia": f(th_day),
         "util_bottleneck": ase["util"], "disp_bottleneck": ase["disp"],
         "yield_bottleneck": ase["yield"], "oee_bottleneck": ase["oee"],
         "fallas_total": fails["total"], "logyard_slope": f(slope),
         "logyard_final": f(ly[-1]), "leadtime_p3": f(leadp3)}
    if rep_filter is None:  # IC para KPIs escalables
        k["prod_total_ci"] = f(ci([sum(production_for(r)["vol"].values()) for r in range(NREPS)])[1])
        k["util_bottleneck_ci"] = ase["util_ci"]
        k["disp_bottleneck_ci"] = ase["disp_ci"]
    return k

def build_view(rep_filter):
    stations = station_block(rep_filter)
    prod = production_for(rep_filter)
    series = series_block(rep_filter)
    fails = failures_for(rep_filter)
    sk = sankey_for(rep_filter) if rep_filter is not None else \
        {kln: float(np.mean([sankey_for(r)[kln] for r in range(NREPS)])) for kln in SANKEY_LINKS}
    kpis = kpis_block(rep_filter, stations, prod, series, fails)
    return {"stations": stations, "production": prod, "series": series,
            "failures": fails, "sankey": {k: f(v) for k, v in sk.items()}, "kpis": kpis}

views = {"avg": build_view(None)}
for r in range(NREPS):
    views[str(r)] = build_view(r)

DATA = {
    "meta": {
        "warmup_days": warmup_d, "stationary_days": STAT_DAYS, "nreps": NREPS,
        "stations": U.ALL_STATIONS, "continuous": U.CONTINUOUS_STATIONS,
        "states": U.STATES, "buffers": BUFFERS, "days": DAYS,
        "sankey_links": SANKEY_LINKS,
        "state_colors": {"BUSY": "#2e7d32", "SETUP": "#8e24aa", "IDLE": "#fbc02d",
                         "BLOCKED": "#e64a19", "DOWN": "#c62828", "OFF_SHIFT": "#b0bec5"},
        "product_colors": {"P1": "#4C72B0", "P2": "#55A868", "P3": "#8172B3"},
    },
    "views": views,
}

out = U.OUT / "dashboard_data.json"
out.write_text(json.dumps(DATA, ensure_ascii=False, allow_nan=False), encoding="utf-8")
print(f">> {out}  ({out.stat().st_size/1024:.0f} KB)")
print(f"   warmup={warmup_d} d, stationary={STAT_DAYS} d, buffers={BUFFERS}")
print(f"   KPIs(avg): produccion={views['avg']['kpis']['prod_total']:.0f} m3/año, "
      f"throughput={views['avg']['kpis']['throughput_dia']:.1f} m3/dia, "
      f"util_aserradero={views['avg']['kpis']['util_bottleneck']*100:.1f}%")
print(f"   Sankey(avg) trozos->aserradero={views['avg']['sankey']['trozos>aserradero']:.0f} m3/año")
