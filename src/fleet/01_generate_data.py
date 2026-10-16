"""
Fleet management project - step 1: generate a realistic SYNTHETIC dataset.

A fictional freight carrier ("Ridgeline Freight") runs 120 tractors: 60 conventional diesel
and 60 AI-equipped (driver-assist / autonomous-capable, AI predictive maintenance and routing).
Monthly operating records for Oct 2023 - Sep 2026, plus every maintenance event.

Stories planted for the analysis to find (and to be honest about):
  * AI tractors cost ~$72K more to buy and carry a $1,650/month software and connectivity fee.
  * They run more miles per month on long-haul lanes (less idle time) and burn less fuel.
  * Predictive maintenance cuts unplanned breakdowns, but sensor repairs are dearer per event and
    maintenance cost climbs faster with age (sensor / compute refresh after ~30 months).
  * In dense urban work the AI premium does not pay: little utilisation gain, more curb-strike repairs.
  * Confounders: AI units are newer and skew to long-haul lanes, so a naive average flatters them.

Tables -> data/fleet.db and data/*.csv: vehicles, monthly_ops, maintenance
"""
import os
import sqlite3

import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "data")
os.makedirs(OUT, exist_ok=True)

months = pd.date_range("2023-10-01", "2026-09-01", freq="MS")
N_EACH = 60
LANES = ["Long-haul", "Regional", "Urban"]
LANE_MIX = {"AI": [0.55, 0.30, 0.15], "Conventional": [0.35, 0.40, 0.25]}

BASE_MILES = {"Long-haul": 11000, "Regional": 8500, "Urban": 5500}
UTIL = {"AI": {"Long-haul": 1.22, "Regional": 1.12, "Urban": 0.97}, "Conventional": {l: 1.0 for l in LANES}}
RPM = {"Long-haul": 2.45, "Regional": 2.75, "Urban": 3.60}                  # revenue per mile, 2023 level
MPG = {"Conventional": {"Long-haul": 6.8, "Regional": 6.3, "Urban": 5.6},
       "AI": {"Long-haul": 7.4, "Regional": 6.75, "Urban": 5.7}}
DRIVER = {"Conventional": {"Long-haul": 0.80, "Regional": 0.82, "Urban": 1.05},
          "AI": {"Long-haul": 0.64, "Regional": 0.74, "Urban": 1.04}}
OTHER_PM = 0.12
INSURANCE = {"Conventional": 1450, "AI": 1650}
SOFTWARE = {"Conventional": 95, "AI": 1650}
ACQ = {"Long-haul": 165000, "Regional": 158000, "Urban": 150000}
AI_PREMIUM = 72000
RESID = {"Conventional": 0.28, "AI": 0.22}
LIFE_M = 84

# ---------------------------------------------------------------- vehicles
rows = []
for typ in ["Conventional", "AI"]:
    lo, hi = (("2020-06-01", "2025-06-01") if typ == "Conventional" else ("2022-06-01", "2025-06-01"))
    span = pd.date_range(lo, hi, freq="MS")
    for i in range(N_EACH):
        lane = rng.choice(LANES, p=LANE_MIX[typ])
        acq_date = span[rng.integers(0, len(span))]
        cost = ACQ[lane] * rng.normal(1, 0.04) + (AI_PREMIUM * rng.normal(1, 0.05) if typ == "AI" else 0)
        rows.append(dict(vehicle_id=f"{'A' if typ == 'AI' else 'C'}{i + 1:03d}", type=typ, lane=lane,
                         acquisition_date=acq_date.strftime("%Y-%m-%d"), acquisition_cost=round(cost, -2),
                         residual_pct=RESID[typ], life_months=LIFE_M))
veh = pd.DataFrame(rows)

# diesel price index by month ($/gal) with a gentle drift and noise
diesel = pd.Series(3.85 + 0.0075 * np.arange(len(months)) + rng.normal(0, 0.08, len(months)), index=months).round(3)

# ---------------------------------------------------------------- operations and maintenance
ops, mx = [], []
event_id = 0
for v in veh.itertuples():
    acq = pd.Timestamp(v.acquisition_date)
    typ, lane = v.type, v.lane
    ai = typ == "AI"
    miles_since_pm = rng.uniform(0, 20000)
    pm_interval = 31000 if ai else 25000
    for mi, m in enumerate(months):
        age = (m.year - acq.year) * 12 + (m.month - acq.month)
        if age < 0:
            continue
        season = 1 + 0.06 * np.cos((m.month - 11) / 12 * 2 * np.pi)
        potential = BASE_MILES[lane] * UTIL[typ][lane] * season * rng.normal(1, 0.07)
        # --- maintenance events this month (rates per 10,000 miles)
        ten = potential / 10000
        events = []
        miles_since_pm += potential
        while miles_since_pm >= pm_interval:
            miles_since_pm -= pm_interval
            events.append(("Preventive", rng.lognormal(np.log(780 if not ai else 860), 0.2), 6 if not ai else 5))
        corr_rate = (0.20 * (1 + 0.012 * age)) if not ai else (0.16 * (1 + 0.016 * age))
        if ai and lane == "Urban":
            corr_rate *= 1.30
        for _ in range(rng.poisson(corr_rate * ten)):
            events.append(("Corrective", rng.lognormal(np.log(2400 if not ai else 2900), 0.45), rng.uniform(8, 20)))
        brk_rate = (0.055 * (1 + 0.012 * age)) if not ai else (0.028 * (1 + 0.020 * age))
        for _ in range(rng.poisson(brk_rate * ten)):
            events.append(("Breakdown", rng.lognormal(np.log(6800), 0.4), rng.uniform(20, 40)))
        if ai and age >= 30 and rng.random() < 0.015:
            events.append(("Sensor refresh", rng.lognormal(np.log(18500), 0.15), 48))
        down = sum(e[2] for e in events)
        for kind, cost, hrs in events:
            event_id += 1
            mx.append(dict(event_id=event_id, vehicle_id=v.vehicle_id, month=m.strftime("%Y-%m-01"), kind=kind,
                           cost=round(float(cost), 2), downtime_hours=round(float(hrs), 1)))
        miles = max(0.0, potential * (1 - min(down, 400) / 650))
        price_idx = 1 + 0.025 * mi / 12
        revenue = miles * RPM[lane] * price_idx * rng.normal(1, 0.04)
        fuel = miles / MPG[typ][lane] * diesel[m] * rng.normal(1, 0.02)
        driver = miles * DRIVER[typ][lane] * (1 + 0.03 * mi / 12)
        other = miles * OTHER_PM * rng.normal(1, 0.05)
        dep = v.acquisition_cost * (1 - v.residual_pct) / v.life_months
        ops.append(dict(vehicle_id=v.vehicle_id, month=m.strftime("%Y-%m-01"), miles=round(miles), revenue=round(revenue, 2),
                        fuel_cost=round(fuel, 2), driver_cost=round(driver, 2), insurance=INSURANCE[typ],
                        software_fee=SOFTWARE[typ], other_cost=round(other, 2), depreciation=round(dep, 2),
                        downtime_hours=round(down, 1), age_months=age))
ops = pd.DataFrame(ops)
mx = pd.DataFrame(mx)

veh.to_csv(f"{OUT}/vehicles.csv", index=False)
ops.to_csv(f"{OUT}/monthly_ops.csv", index=False)
mx.to_csv(f"{OUT}/maintenance.csv", index=False)
con = sqlite3.connect(f"{OUT}/fleet.db")
veh.to_sql("vehicles", con, if_exists="replace", index=False)
ops.to_sql("monthly_ops", con, if_exists="replace", index=False)
mx.to_sql("maintenance", con, if_exists="replace", index=False)
pd.DataFrame({"month": [m.strftime("%Y-%m-01") for m in months], "diesel_per_gal": diesel.values}).to_sql("diesel", con, if_exists="replace", index=False)
con.close()
print(len(veh), "vehicles,", len(ops), "vehicle-months,", len(mx), "maintenance events")
