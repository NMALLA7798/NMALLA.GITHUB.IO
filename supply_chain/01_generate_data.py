"""
Supply chain project - step 1: generate a realistic SYNTHETIC dataset.

Why synthetic: real procurement data is confidential. The generator bakes in
realistic structure (seasonality, a few problem suppliers, Pareto-shaped demand,
lead-time variability) so the analysis has real patterns to find.
Everything is seeded, so results are reproducible.

Tables written to data/supply_chain.db (SQLite) and data/*.csv:
  suppliers, products, purchase_orders, weekly_demand
"""
import os
import sqlite3

import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "data")
os.makedirs(OUT, exist_ok=True)

# ---------------------------------------------------------------- suppliers
# country -> (region, promised lead time in days)
COUNTRIES = {
    "China": ("Asia", 35), "Vietnam": ("Asia", 38), "India": ("Asia", 40),
    "Mexico": ("North America", 10), "USA": ("North America", 7),
    "Germany": ("Europe", 21), "Poland": ("Europe", 18), "Turkey": ("Europe", 24),
}
sup_rows = []
country_names = list(COUNTRIES)
for i in range(1, 25):
    c = country_names[(i - 1) % len(country_names)]
    region, lt = COUNTRIES[c]
    sup_rows.append({
        "supplier_id": i,
        "supplier_name": f"Supplier {i:02d}",
        "country": c,
        "region": region,
        "promised_lead_days": int(lt + rng.integers(-3, 4)),
        # hidden "truth" used only to simulate behaviour
        "p_late": float(np.clip(rng.normal(0.18, 0.06), 0.05, 0.35)),
        "late_mean_days": float(np.clip(rng.normal(5, 1.5), 2, 9)),
        "p_short": float(np.clip(rng.normal(0.08, 0.03), 0.02, 0.15)),
    })
suppliers = pd.DataFrame(sup_rows)
# Plant a few genuinely problematic suppliers - the analysis should find them.
for sid, (pl, lm, ps) in {5: (0.52, 12, 0.28), 11: (0.45, 9, 0.22), 18: (0.40, 14, 0.18)}.items():
    suppliers.loc[suppliers.supplier_id == sid, ["p_late", "late_mean_days", "p_short"]] = [pl, lm, ps]

# ----------------------------------------------------------------- products
N_SKU = 150
cats = ["Electronics", "Home & Garden", "Industrial", "Apparel", "Packaging"]
cat_cost = {"Electronics": 45, "Home & Garden": 18, "Industrial": 60, "Apparel": 12, "Packaging": 3}
skus = []
# Pareto-shaped annual demand so ABC classes emerge naturally
raw = rng.pareto(1.3, N_SKU) + 1
annual_units = (raw / raw.sum() * 900_000).astype(int) + 200
for i in range(N_SKU):
    cat = cats[rng.integers(0, len(cats))]
    skus.append({
        "sku": f"SKU-{i + 1:03d}",
        "category": cat,
        "unit_cost": round(float(cat_cost[cat] * rng.lognormal(0, 0.45)), 2),
        "annual_units": int(annual_units[i]),
        "supplier_id": int(rng.integers(1, 25)),
    })
products = pd.DataFrame(skus)

# ------------------------------------------------------------ weekly demand
weeks = pd.date_range("2024-01-01", periods=104, freq="W-MON")
t = np.arange(len(weeks))
season = 1 + 0.28 * np.sin(2 * np.pi * (weeks.isocalendar().week.values.astype(int) - 40) / 52)
trend = 1 + 0.12 * t / len(weeks)
dem_rows = []
for _, p in products.iterrows():
    mu = p.annual_units / 52 * season * trend
    # gamma-mixed Poisson = over-dispersed demand like real SKUs
    lam = mu * rng.gamma(shape=6, scale=1 / 6, size=len(weeks))
    units = rng.poisson(lam)
    dem_rows.append(pd.DataFrame({"sku": p.sku, "week_start": weeks.strftime("%Y-%m-%d"), "units": units}))
weekly_demand = pd.concat(dem_rows, ignore_index=True)

# ---------------------------------------------------------- purchase orders
po_rows, po_id = [], 1
cutoff = pd.Timestamp("2025-12-31")
sup_idx = suppliers.set_index("supplier_id")
for _, p in products.iterrows():
    s = sup_idx.loc[p.supplier_id]
    cycle_days = int(np.clip(rng.normal(42, 8), 21, 70))
    order_date = pd.Timestamp("2024-01-01") + pd.Timedelta(days=int(rng.integers(0, cycle_days)))
    while order_date < cutoff:
        qty = int(max(50, p.annual_units * cycle_days / 365 * rng.normal(1.0, 0.12)))
        promised = order_date + pd.Timedelta(days=int(s.promised_lead_days))
        late = rng.random() < s.p_late
        delay = int(round(rng.gamma(2.0, s.late_mean_days / 2.0))) if late else int(rng.integers(-2, 1))
        received = promised + pd.Timedelta(days=delay)
        short = rng.random() < s.p_short
        qty_recv = int(qty * (1 - rng.uniform(0.05, 0.35))) if short else qty
        # ~20% of late orders were expedited at a premium
        expedite = late and rng.random() < 0.20
        cost = p.unit_cost * qty_recv * (1.12 if expedite else 1.0)
        if received <= cutoff:
            po_rows.append({
                "po_id": po_id, "sku": p.sku, "supplier_id": int(p.supplier_id),
                "order_date": order_date.strftime("%Y-%m-%d"),
                "promised_date": promised.strftime("%Y-%m-%d"),
                "received_date": received.strftime("%Y-%m-%d"),
                "qty_ordered": qty, "qty_received": qty_recv,
                "unit_cost": p.unit_cost, "expedited": int(expedite),
                "total_cost": round(cost, 2),
            })
            po_id += 1
        order_date += pd.Timedelta(days=int(max(14, rng.normal(cycle_days, 4))))
purchase_orders = pd.DataFrame(po_rows)

# ----------------------------------------------------------------- persist
public_suppliers = suppliers[["supplier_id", "supplier_name", "country", "region", "promised_lead_days"]]
tables = {"suppliers": public_suppliers, "products": products,
          "purchase_orders": purchase_orders, "weekly_demand": weekly_demand}
db = os.path.join(OUT, "supply_chain.db")
if os.path.exists(db):
    os.remove(db)
con = sqlite3.connect(db)
for name, df in tables.items():
    df.to_sql(name, con, index=False)
    df.to_csv(os.path.join(OUT, f"{name}.csv"), index=False)
con.close()
for name, df in tables.items():
    print(f"{name:16s} {len(df):>8,} rows")
