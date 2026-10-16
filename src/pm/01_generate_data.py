"""
PM case study - step 1: SYNTHETIC exception tickets for a fictional fulfillment network.
No real company data. 24,000 tickets over 13 weeks at 5 sites; each ticket has a category, a manual handling time,
and an AI model confidence plus whether the model's proposed resolution would have been correct.
"""
import os
import numpy as np
import pandas as pd

rng = np.random.default_rng(2026)
HERE = os.path.dirname(os.path.abspath(__file__))
os.makedirs(f"{HERE}/data", exist_ok=True)
CATS = {  # share, mean manual minutes, confidence Beta(a,b), calibration offset
    "Quantity mismatch":         (0.28, 14, (7, 1.6), 0.00),
    "Label or ID error":         (0.22, 11, (8, 1.4), 0.00),
    "Damaged goods":             (0.18, 19, (5, 2.0), -0.05),
    "Location conflict":         (0.14, 16, (6, 1.8), -0.02),
    "Vendor documentation":      (0.12, 23, (4.5, 2.2), -0.04),
    "Hazmat or compliance":      (0.06, 38, (3.5, 2.5), -0.08),
}
SITES = ["Site A", "Site B", "Site C", "Site D", "Site E"]
n = 24000
cat = rng.choice(list(CATS), n, p=[v[0] for v in CATS.values()])
rows = []
for c in CATS:
    idx = np.where(cat == c)[0]
    share, mins, (a, b), off = CATS[c]
    conf = rng.beta(a, b, len(idx))
    correct = rng.random(len(idx)) < np.clip(conf + off, 0.05, 0.995)
    manual = rng.lognormal(np.log(mins) - 0.08, 0.4, len(idx))
    for i, cf, ok, m in zip(idx, conf, correct, manual):
        rows.append((i, c, cf, int(ok), m))
df = pd.DataFrame(rows, columns=["ticket", "category", "confidence", "ai_correct", "manual_minutes"]).sort_values("ticket")
df["site"] = rng.choice(SITES, n)
df["week"] = rng.integers(1, 14, n)
df["confidence"] = df.confidence.round(4); df["manual_minutes"] = df.manual_minutes.round(1)
df.to_csv(f"{HERE}/data/tickets.csv", index=False)
print(len(df), "tickets")
