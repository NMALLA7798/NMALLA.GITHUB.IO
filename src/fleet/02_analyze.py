"""Fleet project - step 2: run the SQL, build the cost, maintenance and profitability picture, test it, write results.json."""
import json
import os
import re
import sqlite3

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
con = sqlite3.connect(f"{HERE}/data/fleet.db")
txt = open(f"{HERE}/queries.sql").read()
parts = re.split(r"^-- name: (\w+)\s*$", txt, flags=re.M)
Q = {parts[i]: parts[i + 1] for i in range(1, len(parts), 2)}
q = lambda n: pd.read_sql(Q[n], con)
rng = np.random.default_rng(7)
TYPES = ["AI", "Conventional"]
LANES = ["Long-haul", "Regional", "Urban"]
R = {}

vm = q("vehicle_months")
veh = pd.read_sql("SELECT * FROM vehicles", con)
cl = q("cost_by_type_lane")

# ---------------------------------------------------------------- integrity checks
assert len(vm) == len(pd.read_sql("SELECT 1 FROM monthly_ops", con))
mx_total = pd.read_sql("SELECT SUM(cost) c FROM maintenance", con).c[0]
assert abs(vm.maint_cost.sum() - mx_total) < 0.01, "maintenance not fully joined"
cols = ["fuel", "driver", "maintenance", "insurance", "software", "other", "depreciation"]
assert abs((cl.revenue - cl[cols].sum(axis=1)).sum() - vm.profit.sum()) < 1, "profit identity"

# ---------------------------------------------------------------- cost per mile
def cpm(df):
    d = {c: float(df[c].sum() / df.miles.sum()) for c in cols}
    d["revenue"] = float(df.revenue.sum() / df.miles.sum())
    d["total_cost"] = sum(d[c] for c in cols)
    d["profit"] = d["revenue"] - d["total_cost"]
    d["miles_pm"] = float(df.miles.sum() / df.vehicle_months.sum())
    d["profit_pvm"] = float((df.revenue.sum() - df[cols].sum().sum()) / df.vehicle_months.sum())
    d["vehicle_months"] = int(df.vehicle_months.sum())
    return d
R["cpm"] = {"All": {t: cpm(cl[cl.type == t]) for t in TYPES}}
for l in LANES:
    R["cpm"][l] = {t: cpm(cl[(cl.type == t) & (cl.lane == l)]) for t in TYPES}
for l in R["cpm"]:
    for t in TYPES:
        c = R["cpm"][l][t]
        assert abs(c["revenue"] - c["total_cost"] - c["profit"]) < 1e-9

# ---------------------------------------------------------------- maintenance
mk = q("maintenance_by_kind"); mt = q("miles_by_type").set_index("type")
kinds = ["Preventive", "Corrective", "Breakdown", "Sensor refresh"]
R["maint"] = {}
for t in TYPES:
    miles = mt.loc[t, "miles"]; vms = mt.loc[t, "vehicle_months"]
    d = {"kinds": {}}
    for k in kinds:
        r = mk[(mk.type == t) & (mk.kind == k)]
        ev = int(r.events.sum()) if len(r) else 0
        d["kinds"][k] = dict(events=ev, per_100k=ev / miles * 1e5, avg_cost=float(r.cost.sum() / ev) if ev else 0.0,
                             cost=float(r.cost.sum()) if ev else 0.0, downtime=float(r.downtime_hours.sum()) if ev else 0.0)
    d["downtime_per_vm"] = float(sum(v["downtime"] for v in d["kinds"].values()) / vms)
    d["cost_per_mile"] = float(sum(v["cost"] for v in d["kinds"].values()) / miles)
    d["unplanned_per_100k"] = d["kinds"]["Breakdown"]["per_100k"]
    R["maint"][t] = d
ba = q("maintenance_by_age")
labels = ["0-11 months", "12-23", "24-35", "36-47", "48+"]
R["age"] = {"labels": labels, **{t: [None] * 5 for t in TYPES}, "n": {t: [0] * 5 for t in TYPES}}
for r in ba.itertuples():
    R["age"][r.type][r.bucket] = float(r.maintenance / r.miles)
    R["age"]["n"][r.type][r.bucket] = int(r.vehicle_months)
for t in TYPES:
    for i in range(5):
        if R['age']['n'][t][i] < 100:
            R['age'][t][i] = None
# per-type linear age slope of maintenance cost per mile (used by the calculator)
slope = {}
for t in TYPES:
    d = vm[(vm.type == t) & (vm.miles > 0)]
    a = d.groupby("age_months").agg(m=("maint_cost", "sum"), mi=("miles", "sum")); a = a[a.mi > 20000]
    x = a.index.values; y = (a.m / a.mi).values
    slope[t] = float(np.polyfit(x, y, 1, w=np.sqrt(a.mi.values))[0])
R["age_slope_per_month"] = slope

# ---------------------------------------------------------------- monthly trend
mp = q("monthly_profit")
R["trend"] = {"months": sorted(mp.month.unique().tolist()), **{t: mp[mp.type == t].sort_values("month").profit_per_vehicle.round(0).tolist() for t in TYPES}}

# ---------------------------------------------------------------- confounding: naive vs adjusted difference
vm["ai"] = (vm.type == "AI").astype(float)
vm["month_idx"] = pd.to_datetime(vm.month).dt.month
def design(df):
    X = [np.ones(len(df)), df.ai.values, (df.lane == "Regional").astype(float).values, (df.lane == "Urban").astype(float).values,
         df.age_months.values.astype(float), np.cos((df.month_idx.values - 11) / 12 * 2 * np.pi)]
    return np.column_stack(X)
def fit(df):
    b, *_ = np.linalg.lstsq(design(df), df.profit.values, rcond=None)
    return b[1]
naive = float(vm[vm.ai == 1].profit.mean() - vm[vm.ai == 0].profit.mean())
adj = float(fit(vm))
ids = vm.vehicle_id.unique(); groups = {i: g for i, g in vm.groupby("vehicle_id")}
boots = []
for _ in range(400):
    pick = rng.choice(ids, len(ids))
    boots.append(fit(pd.concat([groups[i] for i in pick])))
lo, hi = np.percentile(boots, [2.5, 97.5])
# per-lane difference with cluster bootstrap CI
lane_diff = {}
for l in LANES:
    sub = vm[vm.lane == l]
    g = {i: d for i, d in sub.groupby("vehicle_id")}; ids_l = np.array(list(g)); ai_flag = {i: g[i].ai.iloc[0] for i in ids_l}
    def diff(pick):
        d = pd.concat([g[i] for i in pick]); return d[d.ai == 1].profit.mean() - d[d.ai == 0].profit.mean()
    point = diff(ids_l)
    bs = []
    ai_ids, c_ids = ids_l[[ai_flag[i] == 1 for i in ids_l]], ids_l[[ai_flag[i] == 0 for i in ids_l]]
    for _ in range(400):
        bs.append(diff(np.concatenate([rng.choice(ai_ids, len(ai_ids)), rng.choice(c_ids, len(c_ids))])))
    l_lo, l_hi = np.percentile(bs, [2.5, 97.5])
    lane_diff[l] = dict(diff=float(point), lo=float(l_lo), hi=float(l_hi),
                        n_ai=int(len(ai_ids)), n_conv=int(len(c_ids)),
                        ai=float(sub[sub.ai == 1].profit.mean()), conv=float(sub[sub.ai == 0].profit.mean()))
R["stats"] = dict(naive=naive, adjusted=adj, adj_lo=float(lo), adj_hi=float(hi), lane=lane_diff,
                  ai_share_longhaul=float((veh[veh.type == "AI"].lane == "Long-haul").mean()),
                  conv_share_longhaul=float((veh[veh.type == "Conventional"].lane == "Long-haul").mean()),
                  mean_age={t: float(vm[vm.type == t].age_months.mean()) for t in TYPES})

# ---------------------------------------------------------------- vehicle scatter and watchlist
tt = q("vehicle_ttm")
R["vehicles"] = [dict(id=r.vehicle_id, type=r.type, lane=r.lane, age=int(r.age_months), profit=round(float(r.profit)),
                      maint=round(float(r.maintenance)), miles=int(r.miles)) for r in tt.itertuples()]
w = tt.sort_values("profit").head(8)
R["watch"] = [dict(id=r.vehicle_id, type=r.type, lane=r.lane, age=int(r.age_months), profit=round(float(r.profit)),
                   maint=round(float(r.maintenance))) for r in w.itertuples()]
R["ttm_counts"] = dict(n=int(len(tt)), loss=int((tt.profit < 0).sum()),
                       loss_ai=int(((tt.profit < 0) & (tt.type == "AI")).sum()), loss_conv=int(((tt.profit < 0) & (tt.type == "Conventional")).sum()))

# ---------------------------------------------------------------- calculator inputs (per lane and type)
dsl = q("diesel_price").set_index("month").diesel_per_gal
recent = vm[vm.month >= "2025-10-01"].copy()
price_ttm = float(dsl[dsl.index >= "2025-10-01"].mean())
vm["diesel"] = vm.month.map(dsl); vm["gal"] = vm.fuel_cost / vm.diesel
calc = {"diesel_ttm": price_ttm, "slope": slope, "rate": 0.08, "life_months": 84, "cells": {}}
for l in LANES:
    for t in TYPES:
        d = vm[(vm.lane == l) & (vm.type == t)]; r = recent[(recent.lane == l) & (recent.type == t)]
        vv = veh[(veh.lane == l) & (veh.type == t)]
        calc["cells"][f"{l}|{t}"] = dict(
            miles=float(d.miles.mean()), rev_pm=float(r.revenue.sum() / r.miles.sum()), gal_pm=float(d.gal.sum() / d.miles.sum()),
            driver_pm=float(d.driver_cost.sum() / d.miles.sum()), other_pm=float(d.other_cost.sum() / d.miles.sum()),
            maint_pm=float(d.maint_cost.sum() / d.miles.sum()), mean_age=float(d.age_months.mean()),
            ins=float(d.insurance.mean()), software=float(d.software_fee.mean()),
            acq=float(vv.acquisition_cost.mean()), resid=float(vv.residual_pct.mean()))
R["calc"] = calc
R["fleet"] = dict(vehicles=int(len(veh)), ai=int((veh.type == "AI").sum()), conv=int((veh.type == "Conventional").sum()),
                  vehicle_months=int(len(vm)), events=int(pd.read_sql("SELECT COUNT(*) c FROM maintenance", con).c[0]),
                  first="2023-10", last="2026-09", premium=float(veh[veh.type == "AI"].acquisition_cost.mean() - veh[veh.type == "Conventional"].acquisition_cost.mean()))
json.dump(R, open(f"{HERE}/results.json", "w"), indent=1)

# ---------------------------------------------------------------- print summary
f = lambda x: f"{x:,.2f}"
for l in R["cpm"]:
    print(l, {t: (round(R['cpm'][l][t]['revenue'], 2), round(R['cpm'][l][t]['total_cost'], 2), round(R['cpm'][l][t]['profit_pvm'])) for t in TYPES})
print("maint", {t: (round(R['maint'][t]['cost_per_mile'], 3), round(R['maint'][t]['unplanned_per_100k'], 2), round(R['maint'][t]['downtime_per_vm'], 1)) for t in TYPES})
print("age", R["age"]); print("slope", slope)
print("stats", {k: v for k, v in R["stats"].items() if k != "lane"}); print({l: (round(v['diff']), round(v['lo']), round(v['hi'])) for l, v in lane_diff.items()})
print("ttm", R["ttm_counts"], "premium", R["fleet"]["premium"])

# ---------------------------------------------------------------- calculator mirror (the page recomputes this live in JS)
def unit(cell, typ, p, age):
    c = calc["cells"][cell]
    m = c["miles"] * (1 + (p["util"] if typ == "AI" else 0))
    maint = max(0.03, c["maint_pm"] + calc["slope"][typ] * (age - c["mean_age"]))
    cash = m * (c["rev_pm"] - c["gal_pm"] * p["diesel"] - c["driver_pm"] - c["other_pm"] - maint) - c["ins"] - (p["software"] if typ == "AI" else c["software"])
    return cash
def project(lane, p):
    out = {}
    acq = {t: calc["cells"][f"{lane}|{t}"]["acq"] + (p["premium"] - R["fleet"]["premium"] if t == "AI" else 0) for t in TYPES}
    cum = {t: [-acq[t]] for t in TYPES}
    npv = {t: -acq[t] for t in TYPES}
    for mth in range(1, calc["life_months"] + 1):
        for t in TYPES:
            cash = unit(f"{lane}|{t}", t, p, mth)
            cum[t].append(cum[t][-1] + cash)
            npv[t] += cash / (1 + calc["rate"] / 12) ** mth
    for t in TYPES:
        resid = calc["cells"][f"{lane}|{t}"]["resid"] * acq[t]
        cum[t][-1] += resid; npv[t] += resid / (1 + calc["rate"] / 12) ** calc["life_months"]
    diff = [a - c for a, c in zip(cum["AI"], cum["Conventional"])]
    pay = next((i for i, v in enumerate(diff) if v >= 0), None)
    return dict(payback=pay, npv_adv=npv["AI"] - npv["Conventional"], cum_adv_end=diff[-1],
                monthly_adv=unit(f"{lane}|AI", "AI", p, 36) - unit(f"{lane}|Conventional", "Conventional", p, 36))
DEF = dict(diesel=price_ttm, premium=R["fleet"]["premium"], util=0.0, software=1650.0)
R["payback_default"] = {l: project(l, DEF) for l in LANES}
R["calc"]["defaults"] = DEF
json.dump(R, open(f"{HERE}/results.json", "w"), indent=1)
print("payback", {l: (v["payback"], round(v["npv_adv"]), round(v["monthly_adv"])) for l, v in R["payback_default"].items()})
print("watch", [(w["id"], w["lane"], w["profit"]) for w in R["watch"]])
print({k: round(v, 3) for k, v in calc["cells"]["Long-haul|AI"].items()})
print("diesel", price_ttm)
