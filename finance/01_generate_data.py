"""
Financial analysis project - step 1: generate a realistic SYNTHETIC dataset.

A mid-size omnichannel company ("Northwind Goods" - fictional) with four business
units. 45 months of actuals (Jan 2023 - Sep 2026) and a budget through Dec 2026,
in tidy (long) format so it behaves like a real warehouse table.

Stories planted for the analysis to uncover:
  * Retail      - volume below plan AND unit costs inflating faster than budget -> margin erosion
  * E-commerce  - volume beats plan but discounting erodes price; marketing overspend
  * Wholesale   - customers paying slower: DSO drifts up, cash gets trapped in receivables
  * Subscriptions - high margin, growth slightly below the aggressive plan

Tables -> data/finance.db and data/*.csv:  pnl (units, price, costs by month/BU/scenario), ar (receivables)
"""
import os
import sqlite3

import numpy as np
import pandas as pd

rng = np.random.default_rng(11)
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "data")
os.makedirs(OUT, exist_ok=True)

months = pd.date_range("2023-01-01", "2026-12-01", freq="MS")
LAST_ACTUAL = pd.Timestamp("2026-09-01")

# per-BU assumptions ---------------------------------------------------------
BU = {
    #            base_units price  unit_cost g_plan g_act  infl_act payroll other  mkt%  season_amp season_peak_month
    "Retail":        dict(u=42000, p=48.0, c=29.0, gp=0.02, ga=-0.015, infl=0.045, pay=380_000, oth=130_000, mkt=0.06, amp=0.30, pk=11),
    "E-commerce":    dict(u=30000, p=55.0, c=30.0, gp=0.18, ga=0.24,   infl=0.025, pay=250_000, oth=80_000,  mkt=0.09, amp=0.28, pk=11),
    "Wholesale":     dict(u=25000, p=36.0, c=26.0, gp=0.06, ga=0.05,   infl=0.035, pay=110_000, oth=50_000,  mkt=0.02, amp=0.12, pk=8),
    "Subscriptions": dict(u=9000,  p=29.0, c=6.0,  gp=0.25, ga=0.21,   infl=0.020, pay=90_000,  oth=30_000,  mkt=0.12, amp=0.03, pk=1),
}
BUDGET_INFL = 0.02      # planned unit-cost inflation, all BUs
BUDGET_PRICE_UP = 0.015  # planned annual price increase
BUDGET_PAY_UP = 0.03     # planned annual payroll growth

rows, ar_rows = [], []
for bu, a in BU.items():
    for i, m in enumerate(months):
        t = i / 12.0
        season = 1 + a["amp"] * np.cos(2 * np.pi * (m.month - a["pk"]) / 12)
        # ---------------- budget (smooth, planned)
        b_units = a["u"] * season * (1 + a["gp"]) ** t
        b_price = a["p"] * (1 + BUDGET_PRICE_UP) ** t
        b_cost = a["c"] * (1 + BUDGET_INFL) ** t
        b_rev = b_units * b_price
        b_pay = a["pay"] * (1 + BUDGET_PAY_UP) ** t
        b_oth = a["oth"] * (1 + 0.02) ** t
        b_mkt = a["mkt"] * b_rev
        rows.append(dict(month=m, bu=bu, scenario="Budget", units=b_units, price=b_price, unit_cost=b_cost,
                         payroll=b_pay, marketing=b_mkt, other_opex=b_oth))
        if m > LAST_ACTUAL:
            continue
        # ---------------- actual (noisy, with planted stories)
        units = a["u"] * season * (1 + a["ga"]) ** t * rng.lognormal(0, 0.035)
        price = b_price * (1 + rng.normal(0, 0.006))
        if bu == "E-commerce":  # discounting ramps up from Jan 2025
            k = (m.year - 2025) * 12 + m.month  # 1 in Jan 2025
            if k >= 1:
                price *= 1 - min(0.05, 0.0025 * k)
        if bu == "Wholesale":
            price *= 1.005
        cost = a["c"] * (1 + a["infl"]) ** t * (1 + rng.normal(0, 0.008))
        pay = b_pay * (1 + rng.normal(0.01, 0.015))
        oth = b_oth * (1 + rng.normal(0.0, 0.04))
        over = rng.normal(0.0, 0.03)
        if bu == "E-commerce":  # CAC push: marketing overspend ramps from Jul 2025
            k = (m.year - 2025) * 12 + m.month - 6
            if k > 0:
                over += min(0.25, 0.012 * k)
        mkt = b_mkt * (1 + over)
        rows.append(dict(month=m, bu=bu, scenario="Actual", units=units, price=price, unit_cost=cost,
                         payroll=pay, marketing=mkt, other_opex=oth))
        # ---------------- receivables
        base_dso = {"Retail": 3, "E-commerce": 4, "Subscriptions": 5}.get(bu)
        if bu == "Wholesale":
            drift = np.clip((i - 17) / (44 - 17), 0, 1)  # drift starts Jun 2024
            base_dso = 38 + 17 * drift
        dso = base_dso * (1 + rng.normal(0, 0.04))
        ar_rows.append(dict(month=m, bu=bu, ar_balance=dso / 30 * units * price))

pnl = pd.DataFrame(rows)
# round the drivers FIRST, then derive revenue/cogs from the stored values,
# so units x price == revenue exactly (a real table would reconcile the same way)
pnl = pnl.round({"units": 0, "price": 3, "unit_cost": 3, "payroll": 2, "marketing": 2, "other_opex": 2})
pnl["revenue"] = (pnl.units * pnl.price).round(2)
pnl["cogs"] = (pnl.units * pnl.unit_cost).round(2)
pnl["month"] = pnl.month.dt.strftime("%Y-%m-%d")
pnl = pnl[["month", "bu", "scenario", "units", "price", "unit_cost", "revenue", "cogs", "payroll", "marketing", "other_opex"]]
ar = pd.DataFrame(ar_rows)
ar["month"] = ar.month.dt.strftime("%Y-%m-%d")
ar["ar_balance"] = ar.ar_balance.round(2)

db = os.path.join(OUT, "finance.db")
if os.path.exists(db):
    os.remove(db)
con = sqlite3.connect(db)
pnl.to_sql("pnl", con, index=False)
ar.to_sql("ar", con, index=False)
con.close()
pnl.to_csv(os.path.join(OUT, "pnl.csv"), index=False)
ar.to_csv(os.path.join(OUT, "ar.csv"), index=False)
print(f"pnl {len(pnl):,} rows | ar {len(ar):,} rows")
print(pnl.groupby("scenario").revenue.sum().round(0).to_dict())
