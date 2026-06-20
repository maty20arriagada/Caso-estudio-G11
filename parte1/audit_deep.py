"""
Deep data integrity audit — CMPC Mulchen sawmill simulation
Checks all 7 items requested, printed to stdout (no file output).
"""

import sys
sys.path.insert(0, "/mnt/c/Users/Matias Arriagada R/Documents/Universidad/Quinto año universidad/Noveno semestre/Diseño de sistemas de producción/Tareas")

import pandas as pd
import numpy as np
from parte1.cmpc_utils import DATA, STATES, SHIFT_STATIONS, CONTINUOUS_STATIONS, ALL_STATIONS, HORIZON_H

warmup_h = 14 * 24  # 336 h as per RESUMEN

def load(name):
    return pd.read_csv(DATA / f"{name}.csv")

print("=" * 100)
print("DEEP DATA INTEGRITY AUDIT — CMPC Mulchen Sawmill Simulation")
print("=" * 100)

# =========================================================================
# 1. CALENDAR INTEGRITY
# =========================================================================
print("\n" + "=" * 100)
print("CHECK 1: Calendar integrity")
print("=" * 100)

cal = load("calendar")
print(f"\nCalendar shape: {cal.shape}")
print(f"Total days: {len(cal)}, Operating: {cal['is_operating_day'].sum()}, Non-operating: {(~cal['is_operating_day']).sum()}")

# 1a. Nulls in shift_open/close match non-operating days
null_open = cal["shift_open_time_h"].isna()
null_close = cal["shift_close_time_h"].isna()
print(f"\nNull shift_open_time_h: {null_open.sum()} rows ({null_open.sum()/len(cal)*100:.1f}%)")
print(f"Null shift_close_time_h: {null_close.sum()} rows ({null_close.sum()/len(cal)*100:.1f}%)")

non_op = ~cal["is_operating_day"]
print(f"Non-operating days: {non_op.sum()}")
null_match_nonop = ((null_open == non_op) & (null_close == non_op)).all()
print(f"Nulls exactly match non-operating days: {null_match_nonop}")

if not null_match_nonop:
    mismatches = cal[null_open != non_op]
    print(f"  MISMATCHES: {len(mismatches)} rows where null != non-operating")
    print(mismatches)

# 1b. Operating days have exactly 16h planned_operating_hours
op_days = cal[cal["is_operating_day"]]
op_hours_ok = (op_days["planned_operating_hours"] == 16.0).all()
print(f"\nAll operating days have planned_operating_hours == 16.0: {op_hours_ok}")
if not op_hours_ok:
    bad = op_days[op_days["planned_operating_hours"] != 16.0]
    print(f"  EXCEPTIONS: {bad[['day', 'planned_operating_hours']].to_string()}")

# Non-operating days have 0h
non_op_hours = cal.loc[~cal["is_operating_day"], "planned_operating_hours"]
non_op_ok = (non_op_hours == 0.0).all()
print(f"All non-operating days have planned_operating_hours == 0.0: {non_op_ok}")

# 1c. shift_open = 7 + 24*day, shift_close = 23 + 24*day for operating days
op_days = op_days.copy()
op_days["expected_open"] = 7.0 + 24.0 * op_days["day"]
op_days["expected_close"] = 23.0 + 24.0 * op_days["day"]
open_match = np.isclose(op_days["shift_open_time_h"], op_days["expected_open"]).all()
close_match = np.isclose(op_days["shift_close_time_h"], op_days["expected_close"]).all()
print(f"\nOperating days: shift_open == 7 + 24*day: {open_match}")
print(f"Operating days: shift_close == 23 + 24*day: {close_match}")

if not open_match:
    bad = op_days[~np.isclose(op_days["shift_open_time_h"], op_days["expected_open"])]
    print(f"  MISMATCHES (open): {bad[['day', 'shift_open_time_h', 'expected_open']].to_string()}")
if not close_match:
    bad = op_days[~np.isclose(op_days["shift_close_time_h"], op_days["expected_close"])]
    print(f"  MISMATCHES (close): {bad[['day', 'shift_close_time_h', 'expected_close']].to_string()}")

# =========================================================================
# 2. OFF_SHIFT HOURS INCONSISTENCY
# =========================================================================
print("\n" + "=" * 100)
print("CHECK 2: OFF_SHIFT hours inconsistency across shift stations")
print("=" * 100)

se = load("station_events")

# Compute OFF_SHIFT per (rep, station) for full horizon
def off_shift_by_station(events, warmup_h=0):
    """OFF_SHIFT hours per (rep, station) over [warmup_h, HORIZON_H]"""
    e = events[events["state"] == "OFF_SHIFT"].copy()
    start = np.maximum(e["start_time_h"].to_numpy(), warmup_h)
    end = np.minimum(e["end_time_h"].to_numpy(), HORIZON_H)
    e["dur_h"] = np.clip(end - start, 0, None)
    e = e[e["dur_h"] > 0]
    return e.groupby(["replication", "station"])["dur_h"].sum()

# Full horizon (warmup=0)
off_full = off_shift_by_station(se, warmup_h=0)
print(f"\nOFF_SHIFT hours per (rep, station) — full horizon [0, 8760):")
for s in SHIFT_STATIONS:
    vals = off_full.xs(s, level="station")
    print(f"  {s:12s}: mean={vals.mean():.1f}h, values={dict(vals)}")

# Stationary period only
off_stat = off_shift_by_station(se, warmup_h=warmup_h)
print(f"\nOFF_SHIFT hours per (rep, station) — stationary [{warmup_h}, 8760):")
for s in SHIFT_STATIONS:
    vals = off_stat.xs(s, level="station")
    print(f"  {s:12s}: mean={vals.mean():.1f}h, values={dict(vals)}")

# Expected OFF_SHIFT calculation
n_operating = cal["is_operating_day"].sum()
n_non_operating = (~cal["is_operating_day"]).sum()
print(f"\nCalendar: {n_operating} operating days, {n_non_operating} non-operating days")
print(f"Expected OFF_SHIFT (simple calc) = {n_non_operating}*24 + {n_operating}*8")
print(f"  = {n_non_operating}*24 + {n_operating}*(24-16)")
simple_expected = n_non_operating * 24 + n_operating * (24 - 16)
print(f"  = {n_non_operating*24} + {n_operating*8} = {simple_expected}h")

# BUT: after warmup, off_shift differs
n_op_after_warmup = cal.loc[cal["day"] >= 14, "is_operating_day"].sum()
n_nonop_after_warmup = cal.loc[cal["day"] >= 14, "is_operating_day"].shape[0] - n_op_after_warmup
print(f"After warmup (day >= 14): {n_op_after_warmup} op days, {n_nonop_after_warmup} non-op days")
expected_after_warmup = n_nonop_after_warmup * 24 + n_op_after_warmup * 8
print(f"Expected OFF_SHIFT after warmup: {n_nonop_after_warmup}*24 + {n_op_after_warmup}*8 = {expected_after_warmup}h")

# Why does aserradero have LESS off_shift? Because it finishes batches after shift close
# Analyze OFF_SHIFT intervals per station 
print("\n--- Why do OFF_SHIFT hours differ? ---")
for s in SHIFT_STATIONS:
    sub = se[(se["station"] == s) & (se["state"] == "OFF_SHIFT") & (se["start_time_h"] >= 0)]
    total_intervals = len(sub)
    total_off_h = sub["end_time_h"].sum() - sub["start_time_h"].sum()
    print(f"\n{s}: {total_intervals} OFF_SHIFT intervals")
    
    # Count OFF_SHIFT intervals that are "full" (spanning entire non-operating block)
    # vs "partial" (start late / end early due to batch overrun/underrun)
    day_of_start = np.floor(sub["start_time_h"].values / 24).astype(int)
    day_of_end = np.floor(sub["end_time_h"].values / 24).astype(int)
    
    # Merge with calendar to see if OFF_SHIFT starts/ends align with shift boundaries
    off_align_start = np.isclose(sub["start_time_h"].values % 24, 23.0, atol=1e-4) | np.isclose(sub["start_time_h"].values % 24, 0.0, atol=1e-4)
    off_align_end = np.isclose(sub["end_time_h"].values % 24, 7.0, atol=1e-4) | np.isclose(sub["end_time_h"].values % 24, 0.0, atol=1e-4)
    
    align_start_pct = off_align_start.mean() * 100
    align_end_pct = off_align_end.mean() * 100
    print(f"  OFF_SHIFT intervals aligned to shift boundaries: start={align_start_pct:.1f}%, end={align_end_pct:.1f}%")
    
    # Duration stats of OFF_SHIFT intervals
    durations = sub["end_time_h"].values - sub["start_time_h"].values
    print(f"  OFF_SHIFT interval durations: min={durations.min():.3f}h, max={durations.max():.3f}h, mean={durations.mean():.3f}h")
    
    # How many OFF_SHIFT intervals are short (batch overrun)
    short_count = (durations < 8).sum()
    print(f"  OFF_SHIFT intervals < 8h (partial): {short_count}/{total_intervals} ({short_count/total_intervals*100:.1f}%)")
    
    # Compare actual OFF_SHIFT hours to expected (based on pure calendar)
    # Expected: every non-op day = 24h off, every op day = 8h off (24-16)
    merge_day = pd.DataFrame({"day": np.arange(365)})
    merge_day["is_op"] = merge_day["day"].map(dict(zip(cal["day"], cal["is_operating_day"])))
    merge_day["expected_off"] = np.where(merge_day["is_op"], 8, 24)
    expected_total = merge_day["expected_off"].sum()
    
    # But we should exclude warmup period
    merge_day["expected_off_after_warmup"] = np.where(merge_day["day"] >= 14, merge_day["expected_off"], 0)
    expected_after_warmup = merge_day["expected_off_after_warmup"].sum()
    actual_after_warmup = off_stat.xs(s, level="station").mean()
    diff = actual_after_warmup - expected_after_warmup
    print(f"  Expected OFF_SHIFT (pure calendar, after warmup): {expected_after_warmup:.0f}h")
    print(f"  Actual OFF_SHIFT (mean, after warmup):           {actual_after_warmup:.0f}h")
    print(f"  Difference: {diff:+.0f}h ({diff/expected_after_warmup*100:+.2f}%)")
    
    # Explore the first OFF_SHIFT for each (rep, day) combination to see if aserradero starts later
    print(f"  --- Deep dive: first OFF_SHIFT per day for {s} (rep 0) ---")
    sub0 = sub[sub["replication"] == 0].sort_values("start_time_h")
    # Check if any OFF_SHIFT starts later than 23+24*day (i.e., batch overrun delayed the shift end)
    for day in range(0, 365, 20):  # sample every 20 days
        shift_close_expected = 23.0 + 24.0 * day
        shift_open_expected = 7.0 + 24.0 * (day + 1)
        # Find OFF_SHIFT intervals that should cover day's nights
        night_start = shift_close_expected
        night_end = shift_open_expected
        # Check if there's an OFF_SHIFT covering this period
        covering = sub0[(sub0["start_time_h"] <= night_start + 0.01) & (sub0["end_time_h"] >= night_end - 0.01)]
        if len(covering) == 0:
            # Find the actual gap between the last non-OFF state and the first non-OFF state
            print(f"    day {day}: NO clean OFF_SHIFT covering [{night_start:.0f}, {night_end:.0f})")

# Let's also check: does aserradero have BUSY/SETUP state during what should be OFF_SHIFT?
print("\n--- Checking for non-OFF_SHIFT activity during non-operating hours (aserradero vs bano vs drymill) ---")
for s in SHIFT_STATIONS:
    sub = se[(se["station"] == s) & (se["state"] != "OFF_SHIFT") & (se["state"] != "IDLE")].copy()
    hour_of_day = sub["start_time_h"] % 24
    day_of = np.floor(sub["start_time_h"] / 24).astype(int)
    sub["hour"] = hour_of_day
    sub["day"] = day_of
    sub = sub.merge(cal[["day", "is_operating_day", "shift_open_time_h", "shift_close_time_h"]], on="day", how="left")
    
    # Busy/setup outside shift window
    outside = sub[(sub["is_operating_day"]) & ((sub["start_time_h"] < sub["shift_open_time_h"]) | (sub["start_time_h"] > sub["shift_close_time_h"]))]
    total_h_outside = (outside["end_time_h"] - outside["start_time_h"]).sum()
    print(f"  {s}: Non-IDLE/OFF_SHIFT hours outside shift window (on op days): {total_h_outside:.2f}h in {len(outside)} intervals")

# =========================================================================
# 3. FAILURE DISTRIBUTION ACROSS REPLICAS
# =========================================================================
print("\n" + "=" * 100)
print("CHECK 3: Failure distribution across replicas")
print("=" * 100)

fail = load("failures")
print(f"\nTotal failures: {len(fail)}")

# Count failures per (replication, station)
fail_counts = fail.groupby(["replication", "station"]).size().unstack(fill_value=0)
print(f"\nFailure counts per (rep, station):")
print(fail_counts)

print(f"\nSummary per station:")
for st in ALL_STATIONS:
    counts = fail_counts[st] if st in fail_counts else pd.Series([0]*5)
    print(f"  {st:12s}: total={counts.sum():3.0f}, mean={counts.mean():.1f}, std={counts.std():.1f}, CV={counts.std()/max(counts.mean(),0.001):.2f}, min={counts.min():.0f}, max={counts.max():.0f}")

# Chi-squared test for station vs replication independence
from scipy.stats import chi2_contingency
print(f"\nChi-squared test (station x replication independence):")
contingency = pd.crosstab(fail["station"], fail["replication"])
print(contingency)
chi2, p, dof, expected = chi2_contingency(contingency)
print(f"  chi2={chi2:.2f}, p={p:.4f}, dof={dof}")
if p < 0.05:
    print("  -> SIGNIFICANT association: failure counts NOT evenly distributed across reps")
else:
    print("  -> No significant association: failure counts are evenly distributed across reps")

# Check per-station if any rep is outlier (deviation > 2 std from mean)
print(f"\nOutlier analysis (per station, any rep > 2 std from mean):")
for st in ALL_STATIONS:
    if st in fail_counts.columns:
        counts = fail_counts[st].values
        mean = counts.mean()
        std = counts.std()
        for ri, c in enumerate(counts):
            if std > 0 and abs(c - mean) > 2 * std:
                print(f"  *** {st}: rep {ri} has {c} failures (mean={mean:.1f}, std={std:.1f}) - outlier!")
    else:
        print(f"  {st}: no failures recorded")

# =========================================================================
# 4. DATA GAP CHECK — station_events continuity
# =========================================================================
print("\n" + "=" * 100)
print("CHECK 4: Data gap check — station_events continuity")
print("=" * 100)

se = load("station_events")
print(f"\nTotal station_events rows: {len(se)}")

# Check for gaps: for each (rep, station), sum of state durations should be exactly HORIZON_H
print("4a. Sum of all state durations per (rep, station) = 8760h?")
se_dur = se.copy()
se_dur["dur_h"] = se_dur["end_time_h"] - se_dur["start_time_h"]
totals = se_dur.groupby(["replication", "station"])["dur_h"].sum().reset_index()
totals["diff"] = abs(totals["dur_h"] - HORIZON_H)
max_diff = totals["diff"].max()
print(f"  Max deviation from 8760h: {max_diff:.6f}h")
if max_diff < 1e-6:
    print("  PASS: all total durations exactly 8760h")
else:
    bad = totals[totals["diff"] > 1e-6]
    print(f"  FAIL: {len(bad)} (rep,station) pairs deviate from 8760h")
    print(bad)

# Check for gaps between consecutive events: end_time_h of one should == start_time_h of next
print("\n4b. Checking for gaps between consecutive events (same rep, station):")
se_sort = se.sort_values(["replication", "station", "start_time_h"])
se_sort["next_start"] = se_sort.groupby(["replication", "station"])["start_time_h"].shift(-1)
se_sort["gap"] = se_sort["next_start"] - se_sort["end_time_h"]
se_sort["gap_abs"] = abs(se_sort["gap"])
gaps = se_sort[~se_sort["next_start"].isna()]

# With floating point, allow epsilon tolerance
max_gap = gaps["gap_abs"].max()
print(f"  Max gap between consecutive events: {max_gap:.2e}h")

if max_gap > 1e-7:
    big_gaps = gaps[gaps["gap_abs"] > 1e-7]
    print(f"  Found {len(big_gaps)} gaps > 1e-7h:")
    for _, row in big_gaps.head(20).iterrows():
        print(f"    rep={row['replication']}, {row['station']}: end={row['end_time_h']:.6f} -> next start={row['next_start']:.6f}, gap={row['gap']:.2e}")
    if len(big_gaps) > 20:
        print(f"    ... and {len(big_gaps)-20} more")
else:
    print("  PASS: no gaps found")

# Check specifically if there are OVERLAPS (negative gap)
overlaps = gaps[gaps["gap"] < -1e-7]
if len(overlaps) > 0:
    print(f"\n  OVERLAPS (negative gaps): {len(overlaps)}")
    for _, row in overlaps.head(20).iterrows():
        print(f"    rep={row['replication']}, {row['station']}: end={row['end_time_h']:.6f} > next start={row['next_start']:.6f}, overlap={-row['gap']:.2e}")
else:
    print("  No overlaps detected")

# =========================================================================
# 5. CROSS-CHECK THROUGHPUT NUMBERS
# =========================================================================
print("\n" + "=" * 100)
print("CHECK 5: Cross-check throughput (22158 m3/year from RESUMEN)")
print("=" * 100)

po = load("product_outputs")
bat = load("batches")
dt = load("daily_throughput")

# 5a. From product_outputs: total volume_m3 per product, mean across reps
print("5a. Throughput from product_outputs:")
po_stat = po[(po["exit_time_h"] >= warmup_h) & (po["exit_time_h"] < HORIZON_H)]
po_by_rep_prod = po_stat.groupby(["replication", "product"])["volume_m3"].sum().reset_index()
po_by_prod = po_by_rep_prod.groupby("product")["volume_m3"].agg(["mean", "std"])
po_total = po_by_rep_prod.groupby("replication")["volume_m3"].sum()
print(f"  P1: mean={po_by_prod.loc['P1', 'mean']:.0f} m3")
print(f"  P2: mean={po_by_prod.loc['P2', 'mean']:.0f} m3")
print(f"  P3: mean={po_by_prod.loc['P3', 'mean']:.0f} m3")
print(f"  TOTAL: mean={po_total.mean():.0f} +- {po_total.std():.0f} m3 (per rep values: {po_total.values})")

# 5b. From batches: last station in each route's volume_out_m3
print("\n5b. Throughput from batches (last station per route, stationary):")
bat_stat = bat[(bat["end_process_time_h"] >= warmup_h) & (bat["end_process_time_h"] < HORIZON_H)]

# Last station per route
route_last = {"P1": "bano", "P2": "drymill", "P3": "impregnado"}
bat_by_prod = {}
for prod, last_station in route_last.items():
    sub = bat_stat[(bat_stat["product"] == prod) & (bat_stat["station"] == last_station)]
    vol_by_rep = sub.groupby("replication")["volume_out_m3"].sum()
    print(f"  {prod} (from {last_station}): mean={vol_by_rep.mean():.1f} m3, values={vol_by_rep.values}")
    bat_by_prod[prod] = vol_by_rep.mean()

bat_total = sum(bat_by_prod.values())
print(f"  TOTAL from route-end batches: {bat_total:.0f} m3")

# 5c. From daily_throughput: sum of m3_out (route-end stations only — but P2+P3 share drymill)
print("\n5c. Throughput from daily_throughput (station-level m3_out):")
dt_stat = dt[dt["day"] >= 14]  # warmup days discarded
print("  Route-end station m3_out (daily_throughput):")
for st in ["bano", "drymill", "impregnado"]:
    sub = dt_stat[dt_stat["station"] == st]
    vol_by_rep = sub.groupby("replication")["m3_out"].sum()
    print(f"    {st:12s}: mean={vol_by_rep.mean():.1f} m3, values={list(vol_by_rep.values)}")
print("  NOTE: drymill m3_out includes BOTH P2 and P3 output; cannot separate by product.")
print("  bano = P1 only, impregnado = P3 only, so P2 = drymill - P3.")

# 5d. From batches: aserradero volume_in_m3
print("\n5d. Aserradero input from batches (volume_in_m3, stationary):")
aserr_in = bat_stat[bat_stat["station"] == "aserradero"]
vol_in_by_rep = aserr_in.groupby("replication")["volume_in_m3"].sum()
print(f"  Aserradero volume_in_m3: mean={vol_in_by_rep.mean():.0f} m3, values={vol_in_by_rep.values}")

# 5e. Cross: sum of m3_in for aserradero in daily_throughput
aserr_in_dt = dt_stat[dt_stat["station"] == "aserradero"].groupby("replication")["m3_in"].sum()
print(f"  Aserradero m3_in (daily_throughput): mean={aserr_in_dt.mean():.0f} m3, values={aserr_in_dt.values}")

# Compute total yield = total_out / total_in
total_in = vol_in_by_rep.mean()
total_out = po_total.mean()
print(f"\n  Overall yield ({total_out:.0f}/{total_in:.0f}): {total_out/total_in*100:.1f}%")

# =========================================================================
# 6. BLOCKED IS TRULY ZERO
# =========================================================================
print("\n" + "=" * 100)
print("CHECK 6: BLOCKED is truly zero across all stations")
print("=" * 100)

blocked = se[se["state"] == "BLOCKED"]
print(f"Total BLOCKED intervals in station_events: {len(blocked)}")
if len(blocked) > 0:
    print("BLOCKED rows:")
    print(blocked)
    blocked_dur = (blocked["end_time_h"] - blocked["start_time_h"]).sum()
    print(f"Total BLOCKED hours: {blocked_dur:.6f}")
    blocked_by_rep_station = blocked.groupby(["replication", "station"]).apply(
        lambda x: (x["end_time_h"] - x["start_time_h"]).sum()
    )
    print(blocked_by_rep_station)
else:
    print("CONFIRMED: Zero BLOCKED intervals in station_events.")

# Also check the kpis
print("\nBLOCKED in kpis_por_replica.csv:")
kpis_path = "/mnt/c/Users/Matias Arriagada R/Documents/Universidad/Quinto año universidad/Noveno semestre/Diseño de sistemas de producción/Tareas/parte1/output/tablas/kpis_por_replica.csv"
kpis = pd.read_csv(kpis_path)
blocked_in_kpis = kpis["f_BLOCKED"].sum()
print(f"  Sum of f_BLOCKED across all rep/station: {blocked_in_kpis:.2e}")

# Check RESUMEN table
sumario_path = "/mnt/c/Users/Matias Arriagada R/Documents/Universidad/Quinto año universidad/Noveno semestre/Diseño de sistemas de producción/Tareas/parte1/output/tablas/disponibilidad_resumen.csv"
sumario = pd.read_csv(sumario_path)
print(f"\nSummarized f_BLOCKED per station:")
for _, r in sumario.iterrows():
    print(f"  {r['station']:12s}: f_BLOCKED = {r['f_BLOCKED']:.2e}")

# =========================================================================
# 7. DAILY THROUGHPUT vs BATCHES CONSISTENCY
# =========================================================================
print("\n" + "=" * 100)
print("CHECK 7: daily_throughput vs batches consistency")
print("=" * 100)

# Match: sum of m3_in for aserradero across all days/reps vs volume_in_m3 for aserradero in batches
# (for stationary period)
print("7a. Aserradero m3_in (daily_throughput) vs volume_in_m3 (batches):")
dt_aserr = dt_stat[dt_stat["station"] == "aserradero"].groupby("replication")["m3_in"].sum()
bat_aserr = bat_stat[bat_stat["station"] == "aserradero"].groupby("replication")["volume_in_m3"].sum()
comparison = pd.DataFrame({"daily_throughput_m3_in": dt_aserr, "batches_volume_in": bat_aserr})
comparison["diff"] = comparison["daily_throughput_m3_in"] - comparison["batches_volume_in"]
comparison["diff_pct"] = comparison["diff"] / comparison["batches_volume_in"] * 100
print(comparison)
print(f"  Max diff: {comparison['diff'].abs().max():.4f} m3")

# Same for m3_out
print("\n7b. m3_out for route-end stations vs batches volume_out:")
for st in route_last.values():
    dt_out = dt_stat[dt_stat["station"] == st].groupby("replication")["m3_out"].sum()
    bat_out = bat_stat[bat_stat["station"] == st].groupby("replication")["volume_out_m3"].sum()
    comp = pd.DataFrame({"daily_throughput": dt_out, "batches": bat_out})
    comp["diff"] = comp["daily_throughput"] - comp["batches"]
    comp["diff_pct"] = comp["diff"] / comp["batches"] * 100
    print(f"  {st}:")
    print(f"    {comp.to_string().replace(chr(10), chr(10)+'    ')}")
    print(f"    Max |diff|: {comp['diff'].abs().max():.4f}")

# batches_processed in daily_throughput vs count of batches in station_events or batches.csv
print("\n7c. batches_processed (daily_throughput) vs batch count (batches.csv):")
for st in ALL_STATIONS:
    dt_bp = dt_stat[dt_stat["station"] == st].groupby("replication")["batches_processed"].sum()
    bat_cnt = bat_stat[bat_stat["station"] == st].groupby("replication").size()
    comp = pd.DataFrame({"daily_throughput_bp": dt_bp, "batches_count": bat_cnt})
    comp["diff"] = comp["daily_throughput_bp"] - comp["batches_count"]
    print(f"  {st:12s}: max diff = {comp['diff'].abs().max():.0f}")
    if comp["diff"].abs().max() > 0:
        print(f"    {comp.to_string().replace(chr(10), chr(10)+'    ')}")

print("\n" + "=" * 100)
print("END OF DEEP AUDIT")
print("=" * 100)
