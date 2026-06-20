"""
Deep audit — additional detailed checks for OFF_SHIFT and failures
"""

import sys
sys.path.insert(0, "/mnt/c/Users/Matias Arriagada R/Documents/Universidad/Quinto año universidad/Noveno semestre/Diseño de sistemas de producción/Tareas")

import pandas as pd
import numpy as np
from parte1.cmpc_utils import DATA

def load(name):
    return pd.read_csv(DATA / f"{name}.csv")

cal = load("calendar")
se = load("station_events")
bat = load("batches")
po = load("product_outputs")

HORIZON = 8760.0
warmup_h = 336.0  # 14 days

# ===== CHECK 2 EXTRA: Detailed OFF_SHIFT cause for aserradero vs bano vs drymill
print("=" * 100)
print("CHECK 2 EXTRA: Breakdown of OFF_SHIFT differences")
print("=" * 100)

# For each shift station, compute: total OFF_SHIFT hours and compare to calendar expectation
# by looking at the start_time of BUSY/SETUP events that occur after shift close

for st in ["aserradero", "bano", "drymill"]:
    # Events for this station (after warmup)
    sub = se[(se["station"] == st) & (se["start_time_h"] >= warmup_h)]
    
    # Total OFF_SHIFT after warmup
    off = sub[sub["state"] == "OFF_SHIFT"]
    off_h = (off["end_time_h"] - off["start_time_h"]).sum()
    
    # Non-OFF_SHIFT, non-IDLE states (BUSY, SETUP, DOWN, BLOCKED)
    busy = sub[sub["state"].isin(["BUSY", "SETUP"])]
    busy_after_hours = 0
    busy_after_count = 0
    for _, row in busy.iterrows():
        t = row["start_time_h"]
        day = int(np.floor(t / 24))
        cal_row = cal[cal["day"] == day]
        if len(cal_row) == 0:
            continue
        cal_row = cal_row.iloc[0]
        t_in_day = t - 24 * day
        if cal_row["is_operating_day"] and t_in_day >= 23.0:
            # BUSY/SETUP started after shift close
            dur = row["end_time_h"] - row["start_time_h"]
            busy_after_hours += dur
            busy_after_count += 1
    
    # Also BUSY starting before shift close but extending past it (overrun)
    # We need to find BUSY intervals that cross 23:00
    overrun_hours = 0
    overrun_count = 0
    for _, row in busy.iterrows():
        t_start = row["start_time_h"]
        t_end = row["end_time_h"]
        day_start = int(np.floor(t_start / 24))
        day_end = int(np.floor(t_end / 24))
        start_in_day = t_start - 24 * day_start
        end_in_day = t_end - 24 * day_end
        
        cal_start = cal[cal["day"] == day_start].iloc[0] if len(cal[cal["day"] == day_start]) > 0 else None
        if cal_start is None or not cal_start["is_operating_day"]:
            continue
        
        # Check if this interval crosses 23:00 on the start day
        if start_in_day < 23.0 and t_end > (23.0 + 24 * day_start):
            overrun = t_end - (23.0 + 24 * day_start)
            overrun_hours += overrun
            overrun_count += 1
    
    # Merge BUSY at non-operating days
    busy_nonop = 0
    for _, row in busy.iterrows():
        day = int(np.floor(row["start_time_h"] / 24))
        cal_row = cal[cal["day"] == day]
        if len(cal_row) == 0 or not cal_row.iloc[0]["is_operating_day"]:
            busy_nonop += row["end_time_h"] - row["start_time_h"]
    
    expected_off = 50 * 24 + 301 * 8  # after warmup: 50 non-op, 301 op
    total_non_off_all = (sub["end_time_h"] - sub["start_time_h"]).sum() - off_h
    
    print(f"\n{st}:")
    print(f"  OFF_SHIFT hours (after warmup):           {off_h:>8.1f}h")
    print(f"  Expected from calendar:                   {expected_off:>8.1f}h")
    print(f"  Difference:                               {off_h - expected_off:>+8.1f}h")
    print(f"  BUSY/SETUP starting after 23:00:          {busy_after_hours:>8.1f}h in {busy_after_count} events")
    print(f"  BUSY/SETUP overrun past 23:00:            {overrun_hours:>8.1f}h in {overrun_count} events")
    print(f"  BUSY/SETUP on non-operating days:         {busy_nonop:>8.1f}h")
    
    # First OFF_SHIFT of each day — when does it actually start?
    off_sorted = off.sort_values("start_time_h")
    off_sorted["off_day"] = np.floor(off_sorted["start_time_h"] / 24).astype(int)
    first_off_per_day = off_sorted.groupby("off_day").first()
    first_off_per_day["start_h_in_day"] = first_off_per_day["start_time_h"] - 24 * first_off_per_day.index
    
    # After operating day: expected OFF_SHIFT to start at 23:00 = 23.0 on that day
    after_op_days = first_off_per_day[first_off_per_day.index.isin(cal[cal["is_operating_day"]]["day"])]
    if len(after_op_days) > 0:
        avg_start = after_op_days["start_h_in_day"].mean()
        max_start = after_op_days["start_h_in_day"].max()
        print(f"  OFF_SHIFT start on op days: avg={avg_start:.2f}h, max={max_start:.2f}h (expected 23.0h)")

# ===== CHECK 5 EXTRA: Why RESUMEN says 22158 but raw data gives 21308
print("\n" + "=" * 100)
print("CHECK 5 EXTRA: 22158 vs 21308 — warmup extrapolation")
print("=" * 100)

# Full horizon (no warmup exclusion)
po_full = po[(po["exit_time_h"] >= 0) & (po["exit_time_h"] < HORIZON)]
full_by_rep = po_full.groupby("replication")["volume_m3"].sum()
print(f"Full year (warmup included) total output: mean={full_by_rep.mean():.0f} m3")
print(f"  Per rep: {full_by_rep.values}")

# Stationary only
po_stat = po[(po["exit_time_h"] >= warmup_h) & (po["exit_time_h"] < HORIZON)]
stat_by_rep = po_stat.groupby("replication")["volume_m3"].sum()
print(f"Stationary period (day 14-364) total output: mean={stat_by_rep.mean():.0f} m3")
print(f"  Per rep: {stat_by_rep.values}")

# Extrapolate stationary to full year
stat_days = 365 - 14  # 351
full_days = 365
extrapolated = stat_by_rep * (full_days / stat_days)
print(f"Extrapolated to full year: mean={extrapolated.mean():.0f} m3")
print(f"  Per rep: {extrapolated.values}")

print(f"\n  Stationary total: {stat_by_rep.mean():.0f} m3 over {stat_days} days = {stat_by_rep.mean()/stat_days:.1f} m3/day")
print(f"  Extrapolated:     {extrapolated.mean():.0f} m3 over {full_days} days")
print(f"  Full year actual: {full_by_rep.mean():.0f} m3")
print(f"  RESUMEN claims:   ~22158 m3")

# Check: is 22158 the extrapolation from stationary?
print(f"\n  21308 * 365 / (365-14) = {21308 * 365 / 351:.0f}")

# ===== CHECK 3 EXTRA: Outlier analysis with z-score
print("\n" + "=" * 100)
print("CHECK 3 EXTRA: Per-station replication outlier detection (z-score)")
print("=" * 100)

fail = load("failures")
fail_counts = fail.groupby(["replication", "station"]).size().unstack(fill_value=0)
for st in fail_counts.columns:
    counts = fail_counts[st].values
    mean = counts.mean()
    std = counts.std()
    print(f"\n{st}: mean={mean:.1f}, std={std:.1f}")
    for ri, c in enumerate(counts):
        if std > 0:
            z = (c - mean) / std
            flag = " ***" if abs(z) > 2 else ""
            print(f"  rep {ri}: {c} failures (z={z:+.2f}){flag}")
        else:
            print(f"  rep {ri}: {c} failures (std=0)")

print("\n" + "=" * 100)
print("END OF EXTRA CHECKS")
print("=" * 100)
