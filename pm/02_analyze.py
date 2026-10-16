"""PM case study - step 2: threshold simulation, RICE prioritisation, experiment sizing -> results.json"""
import json, os
import numpy as np
import pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
df = pd.read_csv(f"{HERE}/data/tickets.csv")
WEEKS = 13
LABOR = 32.0          # loaded $ per hour (assumption)
REWORK_MIN = 45.0     # extra minutes to undo a wrong auto-resolution (assumption)
ESCALATION = 18.0     # $ penalty per wrong auto-resolution for customer / vendor fallout (assumption)
REVIEW_MIN = 1.0      # spot-check minutes per auto-resolved ticket
R = {"assumptions": dict(labor=LABOR, rework_min=REWORK_MIN, escalation=ESCALATION, review_min=REVIEW_MIN, weeks=WEEKS)}
R["baseline"] = dict(tickets=len(df), per_week=len(df) / WEEKS, minutes=float(df.manual_minutes.sum()), mean_min=float(df.manual_minutes.mean()),
                     hours_per_week=float(df.manual_minutes.sum() / 60 / WEEKS))
R["by_category"] = [dict(category=c, tickets=int(len(g)), share=float(len(g) / len(df)), mean_min=float(g.manual_minutes.mean()),
                         mean_conf=float(g.confidence.mean()), accuracy=float(g.ai_correct.mean())) for c, g in df.groupby("category")]
def sim(t, hazmat_guard=True, rework=REWORK_MIN, labor=LABOR):
    d = df[df.confidence >= t]
    if hazmat_guard: d = d[d.category != "Hazmat or compliance"]
    n = len(d); ok = int(d.ai_correct.sum()); wrong = n - ok
    saved = d[d.ai_correct == 1].manual_minutes.sum() - REVIEW_MIN * n
    lost = wrong * rework
    net_min = saved - lost
    net_usd = net_min / 60 * labor - wrong * ESCALATION
    return dict(t=t, coverage=n / len(df), precision=ok / n if n else 1.0, auto=n / WEEKS, wrong_pw=wrong / WEEKS,
                hours_saved_pw=net_min / 60 / WEEKS, net_usd_pw=net_usd / WEEKS)
grid = [round(x, 2) for x in np.arange(0.50, 0.995, 0.01)]
R["curve"] = [sim(t) for t in grid]
R["curve_noguard"] = [sim(t, False) for t in grid]
best = max(R["curve"], key=lambda r: r["net_usd_pw"])
ok97 = [r for r in R["curve"] if r["precision"] >= 0.97]
launch = max(ok97, key=lambda r: r["net_usd_pw"])
R["best"] = best; R["launch"] = launch
R["per_cat_launch"] = []
for c, g in df.groupby("category"):
    d = g[g.confidence >= launch["t"]]
    R["per_cat_launch"].append(dict(category=c, coverage=float(len(d) / len(g)), precision=float(d.ai_correct.mean()) if len(d) else None))
R["hazmat_noguard_precision"] = next(r for r in R["curve_noguard"] if r["t"] == launch["t"])["precision"]
# site / week stability of the launch threshold
d = df[(df.confidence >= launch["t"]) & (df.category != "Hazmat or compliance")]
R["by_site"] = [dict(site=s, precision=float(g.ai_correct.mean()), n=int(len(g))) for s, g in d.groupby("site")]
# experiment sizing: detect a reduction in median-ish mean time to resolution
sd = float(df.manual_minutes.std())
def n_per_arm(delta, sd, alpha=0.05, power=0.8):
    from statistics import NormalDist
    z = NormalDist().inv_cdf
    return int(np.ceil(2 * (sd * (z(1 - alpha / 2) + z(power)) / delta) ** 2))
R["experiment"] = dict(sd=sd, mde_min=1.0, n_per_arm=n_per_arm(1.0, sd), n_per_arm_2=n_per_arm(2.0, sd), weekly_tickets_per_site=len(df) / WEEKS / 5)
# assist mode: suggestion shown on every non-hazmat ticket; agent saves 35% of handling time when it is right, loses 10% checking when wrong
ASSIST_SAVE, ASSIST_LOSS = 0.35, 0.10
d = df[df.category != "Hazmat or compliance"]
a_min = (d[d.ai_correct == 1].manual_minutes.sum() * ASSIST_SAVE - d[d.ai_correct == 0].manual_minutes.sum() * ASSIST_LOSS)
R["assist"] = dict(save=ASSIST_SAVE, loss=ASSIST_LOSS, hours_pw=float(a_min / 60 / WEEKS), accuracy=float(d.ai_correct.mean()), usd_pw=float(a_min / 60 / WEEKS * LABOR))
# RICE: reach = tickets per week affected
reach_all = R["baseline"]["per_week"]
feat = [
 ("Auto-resolve high-confidence tickets", reach_all * launch["coverage"], 2.0, 0.8, 5.0),
 ("Suggested resolution for agents", reach_all * 0.85, 1.0, 0.8, 3.0),
 ("Duplicate ticket detection", reach_all * 0.12, 0.5, 0.9, 1.0),
 ("Vendor document reader", reach_all * 0.12, 1.0, 0.5, 4.0),
 ("Root-cause weekly digest", reach_all * 0.30, 0.5, 0.8, 1.5),
 ("Photo capture for damage claims", reach_all * 0.18, 1.0, 0.7, 2.5),
 ("Teams alerts for stuck tickets", reach_all * 0.25, 0.5, 0.9, 0.5),
]
R["rice"] = [dict(name=n, reach=round(r), impact=i, confidence=c, effort=e) for n, r, i, c, e in feat]
for f in R["rice"]: f["score"] = f["reach"] * f["impact"] * f["confidence"] / f["effort"]
json.dump(R, open(f"{HERE}/results.json", "w"), indent=1, default=float)
print("baseline", R["baseline"]); print("best", best); print("launch", launch)
print(R["per_cat_launch"]); print("hazmat noguard prec", R["hazmat_noguard_precision"]); print(R["experiment"])
print([(f["name"], round(f["score"])) for f in sorted(R["rice"], key=lambda x: -x["score"])])
print(R["by_site"])
