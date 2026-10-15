"""
Business analysis project - step 1: generate a realistic SYNTHETIC dataset.

A fictional consumer fitness app ("FitLoop") with a 14-day free trial and three
monthly plans. 24 months of signups (Jan 2024 - Dec 2025), observed to 31 Dec 2025.

Stories planted for the analysis to uncover:
  * Paid-social share of signups doubles while its activation rate falls, so blended
    retention drops even though most channels are stable (a mix-shift story).
  * Activating within 7 days is the strongest predictor of staying.
  * Early support tickets flag customers who are about to churn.
  * An onboarding-checklist A/B test (Jul-Sep 2025) lifts activation by a few points.

Tables -> data/business.db and data/*.csv:  customers, channel_costs
"""
import os
import sqlite3

import numpy as np
import pandas as pd

rng = np.random.default_rng(21)
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "data")
os.makedirs(OUT, exist_ok=True)

END = pd.Timestamp("2025-12-31")
CHANNELS = ["Paid social", "Paid search", "Organic", "Referral", "Partner"]
# channel mix at the start (m=0) and end (m=23) of the window; each sums to 1
MIX0 = np.array([0.20, 0.22, 0.28, 0.16, 0.14])
MIX1 = np.array([0.38, 0.20, 0.20, 0.10, 0.12])
ACT0 = np.array([0.30, 0.38, 0.47, 0.54, 0.42])  # 7-day activation probability, start
ACT1 = np.array([0.20, 0.38, 0.47, 0.54, 0.42])  # paid social quality falls as spend scales
CH_CHURN = dict(zip(CHANNELS, [1.30, 1.00, 0.85, 0.70, 1.10]))
PLANS = ["Basic", "Plus", "Premium"]
PLAN_P = [0.30, 0.50, 0.20]
PRICE = {"Basic": 9.99, "Plus": 14.99, "Premium": 24.99}
PLAN_CHURN = {"Basic": 1.15, "Plus": 1.0, "Premium": 0.8}
SEASON = {1: 1.25, 2: 1.10, 3: 1.0, 4: 0.95, 5: 0.95, 6: 0.9, 7: 0.9, 8: 0.95, 9: 1.05, 10: 1.0, 11: 0.95, 12: 0.85}
COST = {"Paid social": 20.0, "Paid search": 22.0, "Organic": 2.0, "Referral": 8.0, "Partner": 11.0}  # $ per signup
EXP_START, EXP_END = pd.Timestamp("2025-07-01"), pd.Timestamp("2025-09-30")
CHECKLIST_LIFT = 0.05  # true effect of the onboarding checklist on 7-day activation

rows, cid = [], 1
for m, month_start in enumerate(pd.date_range("2024-01-01", "2025-12-01", freq="MS")):
    n = rng.poisson((450 + 28 * m) * SEASON[month_start.month])
    w = m / 23
    mix = MIX0 * (1 - w) + MIX1 * w
    act_p = ACT0 * (1 - w) + ACT1 * w
    days_in_month = month_start.days_in_month
    for _ in range(n):
        ch_i = rng.choice(len(CHANNELS), p=mix)
        ch = CHANNELS[ch_i]
        signup = month_start + pd.Timedelta(days=int(rng.integers(0, days_in_month)))
        variant = None
        p_act = act_p[ch_i]
        if EXP_START <= signup <= EXP_END:
            variant = "checklist" if rng.random() < 0.5 else "control"
            if variant == "checklist":
                p_act += CHECKLIST_LIFT
        activated = int(rng.random() < p_act)
        plan = rng.choice(PLANS, p=PLAN_P)
        tickets = int(min(rng.poisson(0.45 + 0.55 * (1 - activated) + (0.15 if ch == "Paid social" else 0)), 6))
        converted = int(rng.random() < (0.60 if activated else 0.12))
        paid_start = signup + pd.Timedelta(days=14) if converted else pd.NaT
        cancel = pd.NaT
        if converted and paid_start <= END:
            base = 0.055 * CH_CHURN[ch] * PLAN_CHURN[plan] * np.exp(-0.85 * activated) * (1 + 0.20 * min(tickets, 4))
            k = 0
            while True:  # decide at each monthly boundary whether the customer cancels
                haz = base * (1.6 if k == 0 else 1.3 if k == 1 else 1.0)
                if rng.random() < min(haz, 0.95):
                    cancel = paid_start + pd.DateOffset(months=k) + pd.Timedelta(days=int(rng.integers(1, 28)))
                    break
                k += 1
                if paid_start + pd.DateOffset(months=k) > END:
                    break
            if pd.notna(cancel) and cancel > END:
                cancel = pd.NaT
        rows.append({
            "customer_id": cid, "signup_date": signup.strftime("%Y-%m-%d"), "channel": ch, "plan": plan,
            "activated_7d": activated, "tickets_30d": tickets, "converted": converted,
            "paid_start_date": paid_start.strftime("%Y-%m-%d") if pd.notna(paid_start) else None,
            "cancel_date": cancel.strftime("%Y-%m-%d") if pd.notna(cancel) else None,
            "exp_variant": variant, "monthly_price": PRICE[plan],
        })
        cid += 1

customers = pd.DataFrame(rows)
channel_costs = pd.DataFrame({"channel": list(COST), "cost_per_signup": list(COST.values())})

db = os.path.join(OUT, "business.db")
if os.path.exists(db):
    os.remove(db)
con = sqlite3.connect(db)
customers.to_sql("customers", con, index=False)
channel_costs.to_sql("channel_costs", con, index=False)
con.close()
customers.to_csv(os.path.join(OUT, "customers.csv"), index=False)
channel_costs.to_csv(os.path.join(OUT, "channel_costs.csv"), index=False)
print(f"customers {len(customers):,} rows | paying {int(customers.converted.sum()):,} | cancelled {customers.cancel_date.notna().sum():,}")
print(customers.groupby("channel").agg(n=("customer_id", "count"), act=("activated_7d", "mean"), conv=("converted", "mean")).round(3))
print(customers[customers.exp_variant.notna()].groupby("exp_variant").agg(n=("customer_id", "count"), act=("activated_7d", "mean")).round(3))
