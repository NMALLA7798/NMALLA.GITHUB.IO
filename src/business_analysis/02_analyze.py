"""
Business analysis project - step 2: analysis.

  1. SQL layer      -> KPIs, funnel, cohort retention, churn drivers, unit economics
  2. Diagnosis      -> why blended 90-day retention fell (mix shift vs within-channel change)
  3. Experiment     -> onboarding-checklist A/B test: SRM check, z-test, confidence intervals, MDE
  4. Business case  -> five initiatives sized from the data, plotted as impact vs effort

Writes results.json, which feeds the portfolio page.
"""
import json
import math
import os
import re
import sqlite3

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
con = sqlite3.connect(os.path.join(HERE, "data", "business.db"))


def load_queries(path):
    parts = re.split(r"^-- name: (\w+)\s*$", open(path).read(), flags=re.M)
    return {parts[i]: parts[i + 1] for i in range(1, len(parts), 2)}


Q = load_queries(os.path.join(HERE, "queries.sql"))
run = lambda n: pd.read_sql_query(Q[n], con)
r1 = lambda x: round(float(x), 1)
r0 = lambda x: round(float(x), 0)
norm_sf = lambda z: 0.5 * math.erfc(z / math.sqrt(2))  # upper tail of N(0,1)

# ------------------------------------------------------------------ 1. SQL
kpis = run("overall_kpis").iloc[0].to_dict()
funnel = run("funnel_by_channel")
for a, b, name in [("activated", "signups", "activation_pct"), ("paid", "signups", "paid_pct"),
                   ("retained_90d", "signups", "retained_pct_of_signups")]:
    funnel[name] = (100 * funnel[a] / funnel[b]).round(1)
funnel["retained_pct_of_paid"] = (100 * funnel.retained_90d / funnel.paid).round(1)
funnel = funnel.sort_values("paid_pct")

coh = run("cohort_retention")
coh["ret"] = (100 * coh.active / coh.cohort_size).round(1)
cohorts = sorted(coh.cohort.unique())
heat = [{"cohort": c, "size": int(coh[(coh.cohort == c) & (coh.months_since == 0)].cohort_size.iloc[0]),
         "ret": [None if coh[(coh.cohort == c) & (coh.months_since == m)].empty else float(coh[(coh.cohort == c) & (coh.months_since == m)].ret.iloc[0])
                 for m in range(13)]} for c in cohorts]

seg = run("churn_by_segment")
ue = run("unit_economics")
va = run("value_by_activation").set_index("activated_7d")
trend = run("monthly_trend")
vol = run("base_volumes").set_index("channel")

# ------------------------------------------- 2. Diagnosis: mix shift vs rate
# Hypothesis from stakeholders: "retention is falling". Check it first, then look upstream.
m3 = [(h["cohort"], h["ret"][3]) for h in heat if h["ret"][3] is not None]
half = len(m3) // 2
retention_check = {
    "month3_min": r1(min(v for _, v in m3)), "month3_max": r1(max(v for _, v in m3)),
    "first_half_avg": r1(np.mean([v for _, v in m3[:half]])), "second_half_avg": r1(np.mean([v for _, v in m3[half:]])),
    "cohorts": len(m3),
}
cc = run("conversion_by_channel_period")
sA_n = cc[cc.period == "A"].set_index("channel").signups
sB_n = cc[cc.period == "B"].set_index("channel").signups
rA = cc[cc.period == "A"].set_index("channel").paid / sA_n
rB = cc[cc.period == "B"].set_index("channel").paid / sB_n
sA, sB = sA_n / sA_n.sum(), sB_n / sB_n.sum()
retA, retB = float((sA * rA).sum()), float((sB * rB).sum())
mix_effect = float(((sB - sA) * rA).sum())
rate_by_ch = sB * (rB - rA)
rate_social = float(rate_by_ch["Paid social"])
rate_other = float(rate_by_ch.sum() - rate_social)
assert abs((retB - retA) - (mix_effect + rate_social + rate_other)) < 1e-9, "decomposition must reconcile"
decomp = {
    "start": r1(100 * retA), "end": r1(100 * retB),
    "mix": r1(100 * mix_effect), "rate_social": r1(100 * rate_social), "rate_other": r1(100 * rate_other),
    "social_share_A": r1(100 * sA["Paid social"]), "social_share_B": r1(100 * sB["Paid social"]),
    "social_conv_A": r1(100 * rA["Paid social"]), "social_conv_B": r1(100 * rB["Paid social"]),
}

# ------------------------------------------------------------- 3. A/B test
ex = run("experiment").set_index("variant")
bal = run("experiment_balance").pivot(index="channel", columns="variant", values="n")
nC, nT = int(ex.loc["control", "n"]), int(ex.loc["checklist", "n"])
aC, aT = int(ex.loc["control", "activated"]), int(ex.loc["checklist", "activated"])
pC_, pT_ = aC / nC, aT / nT
diff = pT_ - pC_
se_unp = math.sqrt(pC_ * (1 - pC_) / nC + pT_ * (1 - pT_) / nT)
p_pool = (aC + aT) / (nC + nT)
z = diff / math.sqrt(p_pool * (1 - p_pool) * (1 / nC + 1 / nT))
p_val = 2 * norm_sf(abs(z))
ci = (diff - 1.96 * se_unp, diff + 1.96 * se_unp)
mde = 2.8 * math.sqrt(2 * p_pool * (1 - p_pool) / ((nC + nT) / 2))  # 80% power, alpha 0.05
srm_z = (nT - (nC + nT) / 2) / math.sqrt((nC + nT) / 4)
srm_p = 2 * norm_sf(abs(srm_z))
shares = bal.div(bal.sum())
max_mix_gap = float((shares["checklist"] - shares["control"]).abs().max() * 100)
wil = lambda k, n: ((k / n + 1.96 ** 2 / (2 * n)) / (1 + 1.96 ** 2 / n) - 1.96 / (1 + 1.96 ** 2 / n) * math.sqrt(k / n * (1 - k / n) / n + 1.96 ** 2 / (4 * n ** 2)),
                    (k / n + 1.96 ** 2 / (2 * n)) / (1 + 1.96 ** 2 / n) + 1.96 / (1 + 1.96 ** 2 / n) * math.sqrt(k / n * (1 - k / n) / n + 1.96 ** 2 / (4 * n ** 2)))
paidC, paidT = int(ex.loc["control", "paid"]), int(ex.loc["checklist", "paid"])
dp = paidT / nT - paidC / nC
se_p = math.sqrt((paidC / nC) * (1 - paidC / nC) / nC + (paidT / nT) * (1 - paidT / nT) / nT)
pp = (paidC + paidT) / (nC + nT)
zp = dp / math.sqrt(pp * (1 - pp) * (1 / nC + 1 / nT))
experiment = {
    "n_control": nC, "n_variant": nT,
    "act_control": r1(100 * pC_), "act_variant": r1(100 * pT_),
    "ci_control": [r1(100 * v) for v in wil(aC, nC)], "ci_variant": [r1(100 * v) for v in wil(aT, nT)],
    "lift_pts": r1(100 * diff), "lift_ci": [r1(100 * ci[0]), r1(100 * ci[1])],
    "lift_rel_pct": r1(100 * diff / pC_), "z": round(z, 2), "p_value": float(f"{p_val:.3g}"),
    "mde_pts": r1(100 * mde), "srm_p": round(srm_p, 3), "max_mix_gap_pts": round(max_mix_gap, 2),
    "paid_control": r1(100 * paidC / nC), "paid_variant": r1(100 * paidT / nT),
    "paid_lift_pts": r1(100 * dp), "paid_lift_ci": [r1(100 * (dp - 1.96 * se_p)), r1(100 * (dp + 1.96 * se_p))],
    "paid_p_value": float(f"{2 * norm_sf(abs(zp)):.3g}"),
    "tickets_control": float(ex.loc["control", "avg_tickets"]), "tickets_variant": float(ex.loc["checklist", "avg_tickets"]),
}

# ----------------------------------------------------- 4. Business case
conv_act = va.loc[1, "paid"] / va.loc[1, "signups"]
conv_non = va.loc[0, "paid"] / va.loc[0, "signups"]
rev_act = va.loc[1, "revenue6"] / va.loc[1, "paid"]
rev_non = va.loc[0, "revenue6"] / va.loc[0, "paid"]
value_per_activation = conv_act * rev_act - conv_non * rev_non  # 6-month revenue gained per extra activated signup
N12 = int(vol.signups_2025.sum())
ueg = ue.set_index("channel")
cost = pd.read_sql_query("SELECT * FROM channel_costs", con).set_index("channel").cost_per_signup

imp1 = {k: v * value_per_activation * N12 for k, v in
        {"low": ci[0], "mid": diff, "high": ci[1]}.items()}

social_spend = vol.loc["Paid social", "signups_2025"] * cost["Paid social"]
shift = 0.20 * social_spend
extra_search = 0.5 * shift / cost["Paid search"]           # assume search absorbs the budget at 50% efficiency
lost_social = shift / cost["Paid social"]
imp2 = extra_search * ueg.loc["Paid search", "revenue6_per_signup"] - lost_social * ueg.loc["Paid social", "revenue6_per_signup"]

breakeven_eff = (lost_social * ueg.loc["Paid social", "revenue6_per_signup"]) / (shift / cost["Paid search"] * ueg.loc["Paid search", "revenue6_per_signup"])
hi = seg[(seg.dimension == "Support tickets in first 30 days") & (seg.segment == "2 or more")].iloc[0]
n_hi = int(vol.paying_hi_tickets.sum())
arpu = float(kpis["arpu"])
saved = n_hi * hi.churn6_pct / 100 * 0.20                   # assume outreach cuts churn in this group by 20%
imp3 = saved * arpu * 6                                      # each saved customer stays 6 more months

churned = int(run("churned_2025").churned_2025.iloc[0])
recovered = churned * 0.04                                   # assume 4% win-back
imp4 = recovered * arpu * 6 - churned * 2.0                  # $2 campaign cost per churned customer contacted

extra_ref = 0.25 * vol.loc["Referral", "signups_2025"]       # assume +25% referral signups at constant cost
imp5 = extra_ref * (ueg.loc["Referral", "revenue6_per_signup"] - cost["Referral"])

initiatives = [
    {"name": "Roll out onboarding checklist", "impact": r0(imp1["mid"]), "impact_low": r0(imp1["low"]), "impact_high": r0(imp1["high"]),
     "effort": 2, "customers": N12, "basis": "Measured lift from the A/B test, applied to 2025 signup volume"},
    {"name": "Shift 20% of paid-social budget to search", "impact": r0(imp2), "effort": 1, "customers": int(round(lost_social)), "breakeven_efficiency_pct": r0(100 * breakeven_eff),
     "basis": "Assumes search absorbs the money at 50% of its current efficiency"},
    {"name": "Early-warning outreach (2+ early tickets)", "impact": r0(imp3), "effort": 3, "customers": n_hi,
     "basis": "Assumes outreach cuts churn 20% in the group and saved customers stay 6 more months"},
    {"name": "Win-back campaign for 2025 cancellations", "impact": r0(imp4), "effort": 2, "customers": churned,
     "basis": "Assumes 4% win-back at a $2 cost per customer contacted"},
    {"name": "Expand referral program by 25%", "impact": r0(imp5), "effort": 3, "customers": int(round(extra_ref)),
     "basis": "Assumes constant cost per signup; net of spend"},
]

# ------------------------------------------------------------ write JSON
seg_out = {}
for dim, g in seg.groupby("dimension", sort=False):
    seg_out[dim] = g[["segment", "customers", "churn6_pct"]].to_dict("records")
overall_churn6 = float(100 * (seg[seg.dimension == "Plan"].customers * seg[seg.dimension == "Plan"].churn6_pct).sum() / seg[seg.dimension == "Plan"].customers.sum() / 100)

results = {
    "kpis": {k: float(v) for k, v in kpis.items()},
    "totals": {k: int(v) for k, v in pd.read_sql_query("SELECT COUNT(*) AS signups, SUM(converted) AS paying FROM customers", con).iloc[0].items()},
    "funnel": funnel[["channel", "signups", "activation_pct", "paid_pct", "retained_pct_of_signups", "retained_pct_of_paid"]].to_dict("records"),
    "heat": heat,
    "segments": seg_out, "overall_churn6": r1(overall_churn6),
    "unit_econ": ue.to_dict("records"),
    "decomp": decomp, "retention_check": retention_check,
    "trend": trend.to_dict("records"),
    "experiment": experiment,
    "value": {"conv_act": r1(100 * conv_act), "conv_non": r1(100 * conv_non), "rev_act": r1(rev_act), "rev_non": r1(rev_non),
              "value_per_activation": r1(value_per_activation), "signups_2025": N12},
    "initiatives": initiatives,
}
with open(os.path.join(HERE, "results.json"), "w") as f:
    json.dump(results, f, indent=1, default=float)

# ------------------------------------------------------------ console recap
pd.options.display.float_format = "{:,.1f}".format
print("KPIs:", results["kpis"])
print("\nFunnel:\n", funnel[["channel", "signups", "activation_pct", "paid_pct", "retained_pct_of_signups", "retained_pct_of_paid"]].to_string(index=False))
print("\nUnit economics:\n", ue.to_string(index=False))
print("\nChurn by segment:\n", seg.to_string(index=False))
print("\nRetention check:", retention_check)
print("Decomposition:", decomp)
print("\nExperiment:", json.dumps(experiment))
print("\nValue:", results["value"])
print("\nInitiatives:")
for i in initiatives:
    print(f"  {i['name']:<48} impact ${i['impact']:>10,.0f}  effort {i['effort']}  customers {i['customers']:,}")
print("\nHeat sample:", heat[0]["cohort"], heat[0]["ret"][:7], "|", heat[-1]["cohort"], heat[-1]["ret"][:4])
print("Cohorts:", len(heat), "| trend first/last:", trend.iloc[[0, -1]].to_dict("records"))
