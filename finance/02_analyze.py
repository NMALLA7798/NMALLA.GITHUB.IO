"""
Financial analysis project - step 2: analysis.

  1. SQL layer  -> YTD variance, EBITDA bridge (price/volume/cost/opex), margin trend, DSO
  2. Forecast   -> backtested revenue model per BU, 12-month outlook with an 80% interval
  3. Planning   -> FY2026 reforecast vs budget, scenarios, EBITDA sensitivity (tornado)

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
rng = np.random.default_rng(3)
con = sqlite3.connect(os.path.join(HERE, "data", "finance.db"))


def load_queries(path):
    parts = re.split(r"^-- name: (\w+)\s*$", open(path).read(), flags=re.M)
    return {parts[i]: parts[i + 1] for i in range(1, len(parts), 2)}


Q = load_queries(os.path.join(HERE, "queries.sql"))
run = lambda n: pd.read_sql_query(Q[n], con)

# ------------------------------------------------------------------ 1. SQL
ytd = run("ytd_variance")
bridge = run("ebitda_bridge")
qm = run("quarterly_margin")
monthly = run("monthly_company")
dso = run("dso")
acts = run("bu_monthly_actuals")

# integrity check: the bridge must reconcile exactly to the EBITDA variance
parts = ["volume_effect", "price_effect", "cost_effect", "marketing_effect", "payroll_other_effect"]
bridge_sql_2026 = bridge  # the SQL already restricts to 2026 YTD (Jan-Sep)
assert np.allclose(bridge_sql_2026[parts].sum(axis=1), bridge_sql_2026.total_ebitda_var, atol=1), "bridge does not reconcile"
assert np.allclose(bridge_sql_2026.total_ebitda_var.values, (ytd.ebitda_act - ytd.ebitda_bud).values, atol=1), \
    "bridge total != ytd variance"

tot = ytd[["rev_act", "rev_bud", "gp_act", "gp_bud", "ebitda_act", "ebitda_bud"]].sum()
bridge_tot = bridge_sql_2026[parts + ["total_ebitda_var"]].sum()

# DSO story
dso_w = dso[dso.bu == "Wholesale"]
ws_rev_month = float(acts[(acts.bu == "Wholesale") & (acts.month >= "2026-07-01")].revenue.mean())
dso_start = float(dso_w[dso_w.month <= "2024-05-01"].dso_raw.mean())
dso_end = float(dso_w[dso_w.month >= "2026-07-01"].dso_raw.mean())
cash_trapped = (dso_end - dso_start) / 30 * ws_rev_month

# ------------------------------------------------------------ 2. Forecasting
acts["month"] = pd.to_datetime(acts.month)
months_all = pd.date_range("2023-01-01", "2026-09-01", freq="MS")


def feats(dates, origin=pd.Timestamp("2023-01-01")):
    t = ((dates.year - origin.year) * 12 + dates.month - origin.month).values.astype(float)
    ang = 2 * np.pi * dates.month.values / 12
    return np.column_stack([t, np.sin(ang), np.cos(ang), np.sin(2 * ang), np.cos(2 * ang)])


def fit_predict(y, dates_tr, dates_te, model="reg"):
    if model == "snaive":
        s = pd.Series(y, index=dates_tr)
        return np.array([s.get(d - pd.DateOffset(years=1), np.nan) for d in dates_te])
    m = Ridge(alpha=0.1).fit(feats(dates_tr), np.log(y))
    return np.exp(m.predict(feats(dates_te)))


# backtest: train through Dec-2025, predict Jan-Sep 2026
bt = {"reg": [], "snaive": []}
bt_total = {"reg": np.zeros(9), "snaive": np.zeros(9)}
actual_total = np.zeros(9)
tr_d = pd.date_range("2023-01-01", "2025-12-01", freq="MS")
te_d = pd.date_range("2026-01-01", "2026-09-01", freq="MS")
bt_rows = []
for bu, g in acts.groupby("bu"):
    g = g.set_index("month")
    y_tr, y_te = g.loc[tr_d, "revenue"].values, g.loc[te_d, "revenue"].values
    row = {"bu": bu}
    for mdl in bt:
        f = fit_predict(y_tr, tr_d, te_d, mdl)
        # seasonal naive needs growth; it deliberately does not get any (it is the baseline)
        row[mdl] = round(float(np.mean(np.abs(f - y_te) / y_te) * 100), 1)
        bt_total[mdl] += f
    actual_total += y_te
    bt_rows.append(row)
for mdl in bt_total:
    bt_total[mdl] = round(float(np.mean(np.abs(bt_total[mdl] - actual_total) / actual_total) * 100), 1)
bt_rows.append({"bu": "Total company", "reg": bt_total["reg"], "snaive": bt_total["snaive"]})

# final model on all 45 months -> next 12 months (Oct-2026 .. Sep-2027)
fut_d = pd.date_range("2026-10-01", "2027-09-01", freq="MS")
N_BOOT = 2000
fc = {}
boot_total = np.zeros((N_BOOT, len(fut_d)))
for bu, g in acts.groupby("bu"):
    g = g.set_index("month").loc[months_all]
    y = g.revenue.values
    X, Xf = feats(months_all), feats(fut_d)
    m = Ridge(alpha=0.1).fit(X, np.log(y))
    resid = np.log(y) - m.predict(X)
    point = np.exp(m.predict(Xf))
    draws = np.exp(m.predict(Xf)[None, :] + rng.choice(resid, size=(N_BOOT, len(fut_d))))
    boot_total += draws
    # cost structure assumptions (transparent, trailing-window based)
    last6 = g.iloc[-6:]
    gm = 1 - last6.cogs.sum() / last6.revenue.sum()
    mk = last6.marketing.sum() / last6.revenue.sum()
    fixed0 = (g.iloc[-3:].payroll + g.iloc[-3:].other_opex).mean()
    fixed = np.array([fixed0 * (1 + 0.03 / 12) ** (k + 1) for k in range(len(fut_d))])
    fc[bu] = {"rev": point, "gm": gm, "mkt": mk, "fixed": fixed}

fc_total_rev = sum(v["rev"] for v in fc.values())
lo, hi = np.percentile(boot_total, [10, 90], axis=0)
ebitda_f = {bu: v["rev"] * v["gm"] - v["rev"] * v["mkt"] - v["fixed"] for bu, v in fc.items()}
ntm_ebitda = float(sum(e.sum() for e in ebitda_f.values()))
ntm_rev = float(fc_total_rev.sum())

# ----------------------------------------------- 3. Planning: FY26 + scenarios
q4 = slice(0, 3)  # Oct-Dec 2026 are the first three forecast months
q4_rev = float(fc_total_rev[q4].sum())
q4_ebitda = float(sum(e[q4].sum() for e in ebitda_f.values()))
bud_fy = pd.read_sql_query(
    "SELECT SUM(revenue) AS rev, SUM(revenue-cogs-payroll-marketing-other_opex) AS ebitda "
    "FROM pnl WHERE scenario='Budget' AND month BETWEEN '2026-01-01' AND '2026-12-01'", con).iloc[0]
fy_rev, fy_ebitda = float(tot.rev_act) + q4_rev, float(tot.ebitda_act) + q4_ebitda

cogs_ntm = sum(v["rev"] * (1 - v["gm"]) for v in fc.values()).sum()
mkt_ntm = sum(v["rev"] * v["mkt"] for v in fc.values()).sum()
contrib = sum(v["rev"] * (v["gm"] - v["mkt"]) for v in fc.values()).sum()


def scen(price=0.0, vol=0.0, cost=0.0):
    """NTM EBITDA under shocks: price % (flows 100% to EBITDA), volume % (at contribution margin), unit cost %."""
    rev = ntm_rev * (1 + vol)
    cogs = cogs_ntm * (1 + vol) * (1 + cost)
    mkt = mkt_ntm * (1 + vol)
    fixed = sum(v["fixed"].sum() for v in fc.values())
    return rev * (1 + price) - cogs - mkt - fixed


base = scen()
assert abs(base - ntm_ebitda) < 1, "scenario base must match forecast"
tornado = [
    ("Unit cost inflation +/-3%", scen(cost=-0.03) - base, scen(cost=0.03) - base),
    ("Price +/-2%", scen(price=0.02) - base, scen(price=-0.02) - base),
    ("Volume +/-5%", scen(vol=0.05) - base, scen(vol=-0.05) - base),
    ("Marketing spend +/-10%", 0.10 * mkt_ntm, -0.10 * mkt_ntm),
]
tornado = sorted(tornado, key=lambda r: -(abs(r[1]) + abs(r[2])))
scenarios = {
    "Downside": scen(price=-0.02, vol=-0.05, cost=0.03),
    "Base": base,
    "Upside": scen(price=0.01, vol=0.03, cost=-0.01),
}

# ------------------------------------------------------------- write JSON
f0 = lambda x: round(float(x), 0)
results = {
    "ytd": {"rows": ytd.round(0).to_dict("records"),
            "total": {k: f0(v) for k, v in tot.items()}},
    "bridge": {"by_bu": bridge_sql_2026.round(0).to_dict("records"),
               "total": {k: f0(v) for k, v in bridge_tot.items()},
               "start": f0(tot.ebitda_bud), "end": f0(tot.ebitda_act)},
    "margin": qm.to_dict("records"),
    "monthly": monthly.to_dict("records"),
    "dso": dso.to_dict("records"),
    "dso_story": {"start": round(dso_start, 1), "end": round(dso_end, 1),
                  "cash_trapped": f0(cash_trapped)},
    "backtest": bt_rows,
    "forecast": {
        "months": [d.strftime("%Y-%m") for d in fut_d],
        "rev": [f0(x) for x in fc_total_rev], "lo": [f0(x) for x in lo], "hi": [f0(x) for x in hi],
        "ntm_rev": f0(ntm_rev), "ntm_ebitda": f0(ntm_ebitda),
        "parts": {"rev": f0(ntm_rev), "cogs": f0(cogs_ntm), "mkt": f0(mkt_ntm),
                  "fixed": f0(sum(v["fixed"].sum() for v in fc.values())), "ebitda": f0(ntm_ebitda)},
        "assumptions": {bu: {"gm_pct": round(100 * v["gm"], 1), "mkt_pct": round(100 * v["mkt"], 1)} for bu, v in fc.items()},
    },
    "fy2026": {"rev_outlook": f0(fy_rev), "rev_budget": f0(bud_fy.rev),
               "ebitda_outlook": f0(fy_ebitda), "ebitda_budget": f0(bud_fy.ebitda)},
    "tornado": [{"driver": d, "up": f0(u), "down": f0(dn)} for d, u, dn in tornado],
    "scenarios": {k: f0(v) for k, v in scenarios.items()},
}
with open(os.path.join(HERE, "results.json"), "w") as fh:
    json.dump(results, fh, indent=1)

# ----------------------------------------------------------- console recap
pd.options.display.float_format = "{:,.0f}".format
print("YTD variance by BU:\n", ytd.assign(rev_var_pct=(100 * (ytd.rev_act / ytd.rev_bud - 1)).round(1),
      ebitda_var=ytd.ebitda_act - ytd.ebitda_bud).to_string(index=False))
print("\nTotals:", {k: f0(v) for k, v in tot.items()})
print("\nBridge by BU:\n", bridge_sql_2026.to_string(index=False))
print("\nBridge total:", {k: f0(v) for k, v in bridge_tot.items()})
print("\nDSO story:", results["dso_story"])
print("\nBacktest MAPE %:\n", pd.DataFrame(bt_rows).to_string(index=False))
print("\nFY2026:", results["fy2026"])
print("NTM:", results["forecast"]["ntm_rev"], results["forecast"]["ntm_ebitda"])
print("Assumptions:", results["forecast"]["assumptions"])
print("Tornado:", results["tornado"])
print("Scenarios:", results["scenarios"])
g = qm[qm.qtr.isin(["2023-Q1", "2025-Q3", "2026-Q3"])]
print("\nGM trend:\n", g.to_string(index=False))
