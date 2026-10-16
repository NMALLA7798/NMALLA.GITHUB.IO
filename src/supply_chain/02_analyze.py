"""
Supply chain project - step 2: analysis.

  1. SQL layer      -> KPIs, supplier scorecard, OTIF trend, ABC classification
  2. Inventory risk -> Monte-Carlo test of the current reorder policy vs a
                       variability-aware safety-stock policy (Class A SKUs)
  3. Forecasting    -> rolling-origin backtest of 4 methods (WAPE)

Writes results.json, which feeds the portfolio page.
"""
import json
import os
import re
import sqlite3

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge

HERE = os.path.dirname(os.path.abspath(__file__))
rng = np.random.default_rng(7)
con = sqlite3.connect(os.path.join(HERE, "data", "supply_chain.db"))


def load_queries(path):
    text = open(path).read()
    parts = re.split(r"^-- name: (\w+)\s*$", text, flags=re.M)
    return {parts[i]: parts[i + 1] for i in range(1, len(parts), 2)}


Q = load_queries(os.path.join(HERE, "queries.sql"))
run = lambda name: pd.read_sql_query(Q[name], con)

# ------------------------------------------------------------------ 1. SQL
kpis = run("kpis").iloc[0].to_dict()
scorecard = run("supplier_scorecard")
monthly = run("monthly_otif")
country = run("country_summary")
abc = run("abc_classification")
lead = run("lead_time_by_supplier")

lt_stats = lead.groupby("supplier_id")["actual_lead_days"].agg(["mean", "std"]).rename(
    columns={"mean": "lt_mean", "std": "lt_std"})
scorecard = scorecard.merge(lt_stats, left_on="supplier_id", right_index=True)

# "At-risk suppliers": a plain business rule - OTIF below 60% over the period
thr = 60.0
problem = scorecard[scorecard.otif_pct < thr]
problem_spend_share = float(100 * problem.spend.sum() / scorecard.spend.sum())
problem_late_pos = int((problem.pos * (100 - problem.on_time_pct) / 100).sum())
all_late_pos = int((scorecard.pos * (100 - scorecard.on_time_pct) / 100).sum())

abc_counts = abc.groupby("abc_class").agg(skus=("sku", "count"), value=("value", "sum"))
abc_counts["sku_pct"] = (100 * abc_counts.skus / abc_counts.skus.sum()).round(1)
abc_counts["value_pct"] = (100 * abc_counts.value / abc_counts.value.sum()).round(1)

# ----------------------------------------- 2. Inventory policy simulation
products = pd.read_sql_query("SELECT * FROM products", con)
dem = pd.read_sql_query("SELECT * FROM weekly_demand", con)
wide = dem.pivot(index="week_start", columns="sku", values="units").sort_index()

Z95 = 1.645
TARGETS = {"90": 1.2816, "95": 1.645, "975": 1.96, "99": 2.3263}  # z-values for target cycle service levels
N_SIM = 4000
a_skus = abc[abc.abc_class == "A"]
po_lt = pd.read_sql_query(
    "SELECT sku, supplier_id, julianday(received_date) - julianday(order_date) AS lead_days "
    "FROM purchase_orders", con)
promised = pd.read_sql_query("SELECT supplier_id, promised_lead_days FROM suppliers", con).set_index("supplier_id")

rows = []
for _, r in a_skus.iterrows():
    w = wide[r.sku].values.astype(float)
    mu_w, sd_w = w.mean(), w.std(ddof=1)
    lts = po_lt[po_lt.supplier_id == r.supplier_id].lead_days.values
    lt_prom_w = promised.loc[r.supplier_id, "promised_lead_days"] / 7
    lt_mean_w, lt_sd_w = lts.mean() / 7, lts.std(ddof=1) / 7
    # CURRENT policy (what the data implies planners do): demand over the *promised*
    # lead time plus one week of cover.
    rop_now = mu_w * (lt_prom_w + 1)
    # PROPOSED: expected demand over the *actual* lead time + safety stock that
    # accounts for BOTH demand and lead-time variability.
    ss = Z95 * np.sqrt(lt_mean_w * sd_w ** 2 + (mu_w * lt_sd_w) ** 2)
    rop_new = mu_w * lt_mean_w + ss
    # Monte Carlo: bootstrap lead times + weekly demand, count cycles with a stockout
    W = rng.choice(w, size=(N_SIM, 12))
    cum = np.concatenate([np.zeros((N_SIM, 1)), W.cumsum(axis=1)], axis=1)
    lt_w = np.clip(rng.choice(lts, size=N_SIM) / 7, 0, 11.99)
    k = np.floor(lt_w).astype(int)
    frac = lt_w - k
    d_lt = cum[np.arange(N_SIM), k] + frac * W[np.arange(N_SIM), k]
    cost = products.set_index("sku").loc[r.sku, "unit_cost"]
    q_avg = mu_w * 6
    # same Monte Carlo draw, evaluated at several service-level targets (for the interactive selector)
    extra = {}
    for key, z in TARGETS.items():
        rop_t = mu_w * lt_mean_w + z * np.sqrt(lt_mean_w * sd_w ** 2 + (mu_w * lt_sd_w) ** 2)
        extra[f"sl_{key}"] = float((d_lt <= rop_t).mean())
        extra[f"inv_{key}"] = (q_avg / 2 + max(rop_t - mu_w * lt_mean_w, 0)) * cost
    rows.append({**extra,
        "sku": r.sku, "supplier_id": r.supplier_id,
        "sl_now": float((d_lt <= rop_now).mean()), "sl_new": float((d_lt <= rop_new).mean()),
        "inv_now": (q_avg / 2 + max(rop_now - mu_w * lt_mean_w, 0)) * cost,
        "inv_new": (q_avg / 2 + max(rop_new - mu_w * lt_mean_w, 0)) * cost,
        "stockout_cycles_now": float((d_lt > rop_now).sum()),
    })
sim = pd.DataFrame(rows)
sim["problem_supplier"] = sim.supplier_id.isin(problem.supplier_id)
inv_increase_pct = 100 * (sim.inv_new.sum() / sim.inv_now.sum() - 1)

# ---------------------------------------------------- 3. Forecast backtest
H = 13
woy = pd.to_datetime(wide.index).isocalendar().week.values.astype(float)


def features(idx):
    t = idx.astype(float)
    ang = 2 * np.pi * woy[idx] / 52
    return np.column_stack([t, np.sin(ang), np.cos(ang), np.sin(2 * ang), np.cos(2 * ang)])


def forecast_all(train_end, method):
    """Return (H x n_sku) forecast for weeks train_end .. train_end+H-1."""
    Y = wide.values.astype(float)
    tr = Y[:train_end]
    if method == "naive":          # repeat the last observed week
        return np.tile(tr[-1], (H, 1))
    if method == "ma4":            # 4-week moving average
        return np.tile(tr[-4:].mean(axis=0), (H, 1))
    if method == "seasonal_naive":  # same week last year
        return Y[train_end - 52: train_end - 52 + H]
    if method == "trend_season":   # trend + yearly seasonality regression
        idx_tr, idx_te = np.arange(train_end), np.arange(train_end, train_end + H)
        m = Ridge(alpha=1.0).fit(features(idx_tr), tr)   # one multi-output fit
        return np.clip(m.predict(features(idx_te)), 0, None)


methods = ["naive", "ma4", "seasonal_naive", "trend_season"]
labels = {"naive": "Naive (last week)", "ma4": "4-week moving avg",
          "seasonal_naive": "Seasonal naive (same week LY)", "trend_season": "Trend + seasonality regression"}
origins = [65, 78, 91]  # three rolling train/test splits, 13-week horizon each
a_idx = [wide.columns.get_loc(s) for s in a_skus.sku]
res = {m: {"wape_all": [], "wape_A": [], "wape_total": []} for m in methods}
for o in origins:
    actual = wide.values[o:o + H].astype(float)
    for m in methods:
        f = forecast_all(o, m)
        res[m]["wape_all"].append(np.abs(f - actual).sum() / actual.sum())
        res[m]["wape_A"].append(np.abs(f[:, a_idx] - actual[:, a_idx]).sum() / actual[:, a_idx].sum())
        res[m]["wape_total"].append(np.abs(f.sum(axis=1) - actual.sum(axis=1)).sum() / actual.sum())
fc_table = [{"method": labels[m], "key": m,
             "wape_sku_week": round(100 * float(np.mean(res[m]["wape_all"])), 1),
             "wape_class_A": round(100 * float(np.mean(res[m]["wape_A"])), 1),
             "wape_total_demand": round(100 * float(np.mean(res[m]["wape_total"])), 1)} for m in methods]
best = min(fc_table, key=lambda r: r["wape_sku_week"])
base = next(r for r in fc_table if r["key"] == "naive")

# chart series for the final origin (aggregate demand)
o = origins[-1]
weeks_te = list(wide.index[o:o + H])
actual_tot = wide.values[o:o + H].sum(axis=1)
series = {"weeks": weeks_te, "actual": [int(x) for x in actual_tot]}
for m in methods:
    series[m] = [int(x) for x in forecast_all(o, m).sum(axis=1)]
hist_tot = wide.values.sum(axis=1)
history = {"weeks": list(wide.index), "total": [int(x) for x in hist_tot]}

# ------------------------------------------------------------- write JSON
def r(x, n=1):
    return round(float(x), n)


targets = []
for key, label in [("90", "90%"), ("95", "95%"), ("975", "97.5%"), ("99", "99%")]:
    targets.append({
        "key": key, "label": label,
        "service_pct": r(100 * sim[f"sl_{key}"].mean()),
        "service_problem_pct": r(100 * sim[sim.problem_supplier][f"sl_{key}"].mean()),
        "service_other_pct": r(100 * sim[~sim.problem_supplier][f"sl_{key}"].mean()),
        "inv_increase_pct": r(100 * (sim[f"inv_{key}"].sum() / sim.inv_now.sum() - 1)),
        "inv_increase_usd": r(sim[f"inv_{key}"].sum() - sim.inv_now.sum(), 0),
    })


results = {
    "kpis": {k: (float(v) if isinstance(v, (int, float, np.floating, np.integer)) else v) for k, v in kpis.items()},
    "monthly_otif": monthly.to_dict("records"),
    "scorecard": scorecard.round(2).to_dict("records"),
    "country": country.to_dict("records"),
    "abc": {"counts": abc_counts.reset_index().round(1).to_dict("records"),
            "pareto": abc[["rnk", "cum_pct", "abc_class"]].to_dict("records")},
    "problem": {
        "ids": [int(x) for x in problem.supplier_id], "names": list(problem.supplier_name),
        "n": int(len(problem)), "of": int(len(scorecard)),
        "spend_share_pct": r(problem_spend_share),
        "late_po_share_pct": r(100 * problem_late_pos / all_late_pos),
        "otif_threshold": r(thr),
    },
    "sim": {
        "n_a_skus": int(len(sim)),
        "n_a_problem": int(sim.problem_supplier.sum()), "n_a_other": int((~sim.problem_supplier).sum()),
        "service_now_pct": r(100 * sim.sl_now.mean()), "service_new_pct": r(100 * sim.sl_new.mean()),
        "service_now_problem_pct": r(100 * sim[sim.problem_supplier].sl_now.mean()),
        "service_new_problem_pct": r(100 * sim[sim.problem_supplier].sl_new.mean()),
        "service_now_other_pct": r(100 * sim[~sim.problem_supplier].sl_now.mean()),
        "service_new_other_pct": r(100 * sim[~sim.problem_supplier].sl_new.mean()),
        "inventory_increase_pct": r(inv_increase_pct),
        "inventory_increase_usd": r(sim.inv_new.sum() - sim.inv_now.sum(), 0),
        "inventory_now_usd": r(sim.inv_now.sum(), 0),
        "targets": targets,
    },
    "forecast": {"table": fc_table, "best": best["method"], "best_key": best["key"],
                 "improvement_vs_naive_pct": r(100 * (1 - best["wape_sku_week"] / base["wape_sku_week"])),
                 "series": series, "history": history, "labels": labels},
}
with open(os.path.join(HERE, "results.json"), "w") as f:
    json.dump(results, f, indent=1, default=float)

# ------------------------------------------------------------ console recap
print("KPIs:", json.dumps(results["kpis"]))
print("\nWorst 6 suppliers:\n", scorecard[["supplier_name", "country", "pos", "spend_share_pct", "otif_pct", "avg_delay_days", "lt_std"]].head(6).to_string(index=False))
print("\nProblem suppliers:", results["problem"])
print("\nABC:\n", abc_counts)
print("\nSim:", json.dumps(results["sim"]))
print("\nForecast:\n", pd.DataFrame(fc_table).to_string(index=False))
print("improvement vs naive %:", results["forecast"]["improvement_vs_naive_pct"])
print("\nMonthly OTIF first/last:", monthly.otif_pct.iloc[[0, -1]].tolist())
print("\nCountry:\n", country.to_string(index=False))
