"""
Builds portfolio.html from the two projects' results.json files.
Every figure in the page copy is formatted from those files, so the page
cannot drift from the code output.
"""
import html
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SC = json.load(open(os.path.join(HERE, "supply_chain", "results.json")))
FN = json.load(open(os.path.join(HERE, "finance", "results.json")))
BA = json.load(open(os.path.join(HERE, "business_analysis", "results.json")))
import sys
sys.path.insert(0, HERE)
import ba_content


def sql_block(path, name):
    text = open(path).read()
    parts = re.split(r"^-- name: (\w+)\s*$", text, flags=re.M)
    d = {parts[i]: parts[i + 1].strip() for i in range(1, len(parts), 2)}
    return html.escape(d[name])


# ----------------------------------------------------------------- formatters
def M(x, d=1, sign=False):
    pre = "-" if x < 0 else ("+" if sign else "")
    return f"{pre}${abs(x) / 1e6:,.{d}f}M"


def K(x):
    return f"${abs(x) / 1e3:,.0f}K"


def P(x, d=1, sign=False):
    pre = "-" if x < 0 else ("+" if sign else "")
    return f"{pre}{abs(x):.{d}f}%"


# =========================================================== SUPPLY CHAIN COPY
k = SC["kpis"]
prob = SC["problem"]
card = SC["scorecard"]
sim = SC["sim"]
fc = SC["forecast"]
abc = {r["abc_class"]: r for r in SC["abc"]["counts"]}
n_sku = sum(r["skus"] for r in abc.values())
big = max((r for r in card if r["supplier_id"] in prob["ids"]), key=lambda r: r["spend_share_pct"])
m3 = [m["otif_3mo_avg"] for m in SC["monthly_otif"][2:]]
months = SC["monthly_otif"]
ft = {r["key"]: r for r in fc["table"]}
best_key = fc["best_key"]
ab_n = abc["A"]["skus"] + abc["B"]["skus"]

sc_kpis = f"""
<div class="kpis">
  <div class="kpi"><span class="lab">On-time in-full</span><span class="val">{k['otif_pct']}%</span><span class="sub">{k['on_time_pct']}% on time, {k['in_full_pct']}% in full</span></div>
  <div class="kpi"><span class="lab">Purchase spend</span><span class="val">{M(k['total_spend'])}</span><span class="sub">{int(k['purchase_orders']):,} purchase orders, 24 suppliers</span></div>
  <div class="kpi"><span class="lab">Expedite premium</span><span class="val">{K(k['expedite_premium_paid'])}</span><span class="sub">paid to rush late orders</span></div>
  <div class="kpi"><span class="lab">Class A SKUs</span><span class="val">{abc['A']['skus']}</span><span class="sub">{abc['A']['sku_pct']}% of SKUs, {abc['A']['value_pct']}% of value</span></div>
</div>"""

scorecard_rows = "".join(
    f"<tr><td>{r['supplier_name']}</td><td>{r['country']}</td><td class='n'>{r['pos']}</td>"
    f"<td class='n'>{r['spend_share_pct']}%</td><td class='n'>{r['otif_pct']}%</td>"
    f"<td class='n'>{r['avg_delay_days']}</td><td class='n'>{r['lt_std']:.1f}</td></tr>"
    for r in sorted(card, key=lambda r: r["otif_pct"]))
scorecard_table = f"""
<details class="data-table"><summary>Supplier scorecard as a table</summary>
<div class="tbl-wrap"><table>
<thead><tr><th>Supplier</th><th>Country</th><th class="n">POs</th><th class="n">Spend share</th><th class="n">OTIF</th><th class="n">Avg delay (days)</th><th class="n">Lead-time SD (days)</th></tr></thead>
<tbody>{scorecard_rows}</tbody></table></div></details>"""

wape_rows = "".join(
    f"<tr{' class=\"best\"' if r['key'] == best_key else ''}><td>{r['method']}</td>"
    f"<td class='n'>{r['wape_sku_week']}%</td><td class='n'>{r['wape_class_A']}%</td><td class='n'>{r['wape_total_demand']}%</td></tr>"
    for r in fc["table"])
wape_table = f"""
<div class="tbl-wrap"><table>
<thead><tr><th>Method</th><th class="n">SKU-week WAPE</th><th class="n">Class A WAPE</th><th class="n">Total demand WAPE</th></tr></thead>
<tbody>{wape_rows}</tbody></table></div>"""

sc_recs = f"""
<ol class="recs">
  <li><strong>Put the {prob['n']} at-risk suppliers on corrective action.</strong> Start with {big['supplier_name']} ({big['country']}), which carries {big['spend_share_pct']}% of spend at {big['otif_pct']}% OTIF. Qualify a second source for its SKUs while the plan runs.</li>
  <li><strong>Replace promised-lead-time reorder points on Class A SKUs.</strong> Use safety stock built from actual lead-time and demand variability. Begin with the {sim['n_a_problem']} Class A SKUs sourced from at-risk suppliers, where simulated service rises from {sim['service_now_problem_pct']}% to {sim['service_new_problem_pct']}%.</li>
  <li><strong>Fund the inventory deliberately.</strong> The change adds about {K(sim['inventory_increase_usd'])} ({sim['inventory_increase_pct']}%) of Class A inventory. Weigh it against stockout losses and the {K(k['expedite_premium_paid'])} already spent on expediting.</li>
  <li><strong>Run the scorecard every month.</strong> The query is in this project. Track the 3-month OTIF average and each supplier's lead-time spread, since spread drives safety stock.</li>
</ol>"""

sc_limits = (
    "The dataset is synthetic. It was generated with realistic structure (seasonality, Pareto-shaped demand, a few unreliable suppliers), so the "
    "numbers show the method and not real supplier performance. The inventory simulation resamples historical lead times and weekly demand and treats them as independent. "
    "Inventory value counts average cycle stock plus safety stock and ignores holding and ordering costs.")

# ================================================================= FINANCE COPY
ytd = {r["bu"]: r for r in FN["ytd"]["rows"]}
tot = FN["ytd"]["total"]
br = FN["bridge"]["total"]
bru = {r["bu"]: r for r in FN["bridge"]["by_bu"]}
fy = FN["fy2026"]
sc_ = FN["scenarios"]
dso_story = FN["dso_story"]
bt = {r["bu"]: r for r in FN["backtest"]}
rev_var = 100 * (tot["rev_act"] / tot["rev_bud"] - 1)
gp_var = 100 * (tot["gp_act"] / tot["gp_bud"] - 1)
eb_var = 100 * (tot["ebitda_act"] / tot["ebitda_bud"] - 1)
eb_gap = tot["ebitda_act"] - tot["ebitda_bud"]
mg = {(r["bu"], r["qtr"]): r for r in FN["margin"]}
other_dso = [r["dso"] for r in FN["dso"] if r["bu"] != "Wholesale"]
ecom_rev_var = 100 * (ytd["E-commerce"]["rev_act"] / ytd["E-commerce"]["rev_bud"] - 1)
retail_rev_var = 100 * (ytd["Retail"]["rev_act"] / ytd["Retail"]["rev_bud"] - 1)
fy_rev_var = 100 * (fy["rev_outlook"] / fy["rev_budget"] - 1)
fy_eb_var = 100 * (fy["ebitda_outlook"] / fy["ebitda_budget"] - 1)
torn = {r["driver"]: r for r in FN["tornado"]}

fn_kpis = f"""
<div class="kpis">
  <div class="kpi"><span class="lab">Revenue, Jan to Sep 2026</span><span class="val">{M(tot['rev_act'])}</span><span class="sub">{P(rev_var, 1, True)} vs budget</span></div>
  <div class="kpi"><span class="lab">Gross profit</span><span class="val">{M(tot['gp_act'])}</span><span class="sub">{P(gp_var, 1, True)} vs budget</span></div>
  <div class="kpi"><span class="lab">EBITDA</span><span class="val">{M(tot['ebitda_act'])}</span><span class="sub">{P(eb_var, 1, True)} vs budget ({M(eb_gap, 1, True)})</span></div>
  <div class="kpi"><span class="lab">Wholesale DSO</span><span class="val">{dso_story['end']:.0f} days</span><span class="sub">up from {dso_story['start']:.0f} days in 2024</span></div>
</div>"""

bu_rows = "".join(
    f"<tr><td>{bu}</td><td class='n'>{P(100 * (r['rev_act'] / r['rev_bud'] - 1), 1, True)}</td>"
    f"<td class='n'>{M(r['ebitda_act'], 2)}</td><td class='n'>{M(r['ebitda_act'] - r['ebitda_bud'], 2, True)}</td></tr>"
    for bu, r in sorted(ytd.items(), key=lambda kv: kv[1]["ebitda_act"] - kv[1]["ebitda_bud"]))
bu_table = f"""
<div class="tbl-wrap"><table>
<thead><tr><th>Business unit</th><th class="n">Revenue vs budget</th><th class="n">EBITDA</th><th class="n">EBITDA vs budget</th></tr></thead>
<tbody>{bu_rows}</tbody></table></div>"""

bt_rows = "".join(
    f"<tr><td>{r['bu']}</td><td class='n'>{r['reg']}%</td><td class='n'>{r['snaive']}%</td></tr>"
    for r in FN["backtest"])
bt_table = f"""
<div class="tbl-wrap"><table>
<thead><tr><th>Revenue, Jan to Sep 2026</th><th class="n">Model MAPE</th><th class="n">Same month last year</th></tr></thead>
<tbody>{bt_rows}</tbody></table></div>"""

scen_tiles = f"""
<div class="kpis three">
  <div class="kpi"><span class="lab">Downside</span><span class="val">{M(sc_['Downside'])}</span><span class="sub">{M(sc_['Downside'] - sc_['Base'], 1, True)} vs base</span></div>
  <div class="kpi"><span class="lab">Base</span><span class="val">{M(sc_['Base'])}</span><span class="sub">next 12 months EBITDA</span></div>
  <div class="kpi"><span class="lab">Upside</span><span class="val">{M(sc_['Upside'])}</span><span class="sub">{M(sc_['Upside'] - sc_['Base'], 1, True)} vs base</span></div>
</div>"""

fn_recs = f"""
<ol class="recs">
  <li><strong>Reprice or re-source Retail.</strong> Unit costs are running well above the 2% plan and prices have not followed. Retail lost {M(abs(bru['Retail']['cost_effect']))} to cost and {M(abs(bru['Retail']['volume_effect']))} to volume, and is at {M(ytd['Retail']['ebitda_act'], 2)} EBITDA YTD against {M(ytd['Retail']['ebitda_bud'], 2)} budgeted.</li>
  <li><strong>Put a floor under E-commerce discounting.</strong> The unit added {M(bru['E-commerce']['volume_effect'])} of volume and gave back {M(abs(bru['E-commerce']['price_effect']))} in price. Test whether the volume still pays at the current discount depth.</li>
  <li><strong>Tighten Wholesale collections.</strong> Bringing DSO back toward {dso_story['start']:.0f} days would release about {M(dso_story['cash_trapped'], 2)} of cash.</li>
  <li><strong>Reforecast FY2026 now.</strong> EBITDA lands near {M(fy['ebitda_outlook'])} against a {M(fy['ebitda_budget'])} budget ({P(fy_eb_var, 1, True)}). Leadership should see that gap before Q4 closes.</li>
</ol>"""

fn_limits = (
    "The dataset is synthetic and the company is fictional. The forecast holds gross margin and marketing share at each unit's last six months, runs payroll and other costs at the last three months "
    "plus 3% a year, and fits revenue with a trend and yearly seasonality. The 80% interval comes from resampled model residuals, so it covers model error and leaves out shocks such as a lost customer. "
    "The tornado moves one driver at a time.")

skills = [
    ("SQL", "CTEs, window functions (RANK, LAG, moving averages), conditional aggregation, multi-table joins. All three projects start from a query file.", "All three projects"),
    ("Python", "pandas, NumPy and scikit-learn in scripts that rebuild every number from the raw tables.", "All three projects"),
    ("Forecasting", "Rolling-origin backtests, WAPE and MAPE, baseline comparison, bootstrap prediction intervals.", "Weekly demand, monthly revenue"),
    ("Simulation", "Monte Carlo test of a reorder policy using bootstrapped lead times and demand.", "Supply chain"),
    ("Variance analysis", "Price, volume, cost and opex bridge that reconciles exactly to the EBITDA variance, checked by an assertion.", "Finance"),
    ("Domain metrics", "OTIF, ABC classification, safety stock, supplier scorecards, DSO, gross margin, EBITDA.", "All three projects"),
    ("Scenario work", "Base, upside and downside cases and a one-driver-at-a-time sensitivity.", "Finance"),
    ("Business analysis", "Stakeholder framing, testable hypotheses, a KPI dictionary and a prioritized business case with stated assumptions.", "Project 3"),
    ("Experimentation", "A/B test checks (split balance, detectable effect), z-tests, confidence intervals and guardrail metrics.", "Project 3"),
    ("Cohort and funnel analysis", "Recursive-CTE cohorts, funnel by channel, churn segmentation and a mix-shift decomposition.", "Project 3"),
    ("Data visualization", "Sixteen chart types, one color system, uncertainty shown, light and dark themes, interactive controls.", "All three projects"),
    ("Communication", "Each section leads with the finding, ends with a recommendation and lists the limits of the data.", "All three projects"),
]
skills_html = "".join(
    f"<div class='skill'><h3>{n}</h3><p>{d}</p><span class='tag'>{w}</span></div>" for n, d, w in skills)


def pm(v):
    return f"{'+' if v > 0 else ''}{v:.1f}%"


sup_controls = """
<div class="ctl"><span class="lab try">Interactive</span>
  <label for="thr">Count a supplier as at-risk if OTIF is below <output id="thr-out" for="thr">60%</output></label>
  <input type="range" id="thr" min="40" max="80" step="1" value="60"></div>
<p class="readout" id="sup-read" aria-live="polite"></p>"""

svc_buttons = "".join(
    f'<button type="button" data-t="{t["key"]}" aria-pressed="{"true" if t["key"] == "95" else "false"}">{t["label"]}</button>'
    for t in sim["targets"])
svc_controls = f"""
<div class="ctl"><span class="lab try">Interactive</span>
  <span id="svc-lab" class="ctl-text">Target service level</span>
  <div class="seg" id="svc-seg" role="group" aria-labelledby="svc-lab">{svc_buttons}</div></div>
<p class="readout" id="svc-read" aria-live="polite"></p>"""

bu_options = "".join(f'<option value="{b}">{b}</option>' for b in ["Retail", "E-commerce", "Wholesale", "Subscriptions"])
bu_controls = f"""
<div class="ctl"><span class="lab try">Interactive</span>
  <label for="bu-sel">Show bridge for</label>
  <select id="bu-sel"><option value="All">All business units</option>{bu_options}</select></div>
<p class="readout" id="bu-read" aria-live="polite"></p>"""

scen_panel = """
<div class="scen">
  <p class="lab try">Interactive: build your own scenario</p>
  <div class="sl"><label for="sl-p">Price</label><input type="range" id="sl-p" min="-5" max="5" step="0.5" value="0"><output id="sl-p-out" for="sl-p">0.0%</output></div>
  <div class="sl"><label for="sl-v">Volume</label><input type="range" id="sl-v" min="-10" max="10" step="1" value="0"><output id="sl-v-out" for="sl-v">0.0%</output></div>
  <div class="sl"><label for="sl-c">Unit cost</label><input type="range" id="sl-c" min="-5" max="5" step="0.5" value="0"><output id="sl-c-out" for="sl-c">0.0%</output></div>
  <div class="sl"><label for="sl-m">Marketing</label><input type="range" id="sl-m" min="-20" max="20" step="1" value="0"><output id="sl-m-out" for="sl-m">0.0%</output></div>
  <div class="scen-out" aria-live="polite"><span class="lab">Next-12-month EBITDA</span><span class="val" id="sc-val"></span><span class="sub" id="sc-delta"></span></div>
  <button type="button" id="sc-reset" class="tbtn">Reset to base case</button>
</div>"""


def finding(title, body, cid, aria, caption="", tall=False, controls="", custom=""):
    cls = "chart tall" if tall else "chart"
    cap = f"<figcaption>{caption}</figcaption>" if caption else ""
    inner = custom if custom else f'<div class="{cls}"><canvas id="{cid}" role="img" aria-label="{aria}"></canvas></div>'
    return f"""
<article class="finding" id="f-{cid or 'c-heat'}">
  <div class="ftext"><h3>{title}</h3>{body}</div>
  <figure class="ffig">{controls}{inner}{cap}</figure>
</article>"""


sc_findings = "".join([
    finding(
        f"{prob['n']} of {prob['of']} suppliers fall below 60% OTIF",
        f"<p>Together they take {prob['spend_share_pct']}% of spend and cause {prob['late_po_share_pct']}% of late deliveries. "
        f"{big['supplier_name']} ({big['country']}) is the largest exposure: {big['spend_share_pct']}% of spend at {big['otif_pct']}% OTIF, "
        f"with a lead-time standard deviation of {big['lt_std']:.0f} days.</p>{scorecard_table}",
        "c-suppliers", "Bar chart of on-time in-full percentage for each of 24 suppliers, lowest first",
        "Orange bars fall below the at-risk threshold.", tall=True, controls=sup_controls),
    finding(
        "OTIF has not improved in two years",
        f"<p>The 3-month average moves between {min(m3):.1f}% and {max(m3):.1f}% from {months[2]['month']} to {months[-1]['month']} with no sustained improvement. "
        "January 2024 is left out because too few orders had arrived to measure.</p>",
        "c-otif", "Line chart of monthly OTIF percentage and its 3-month average"),
    finding(
        f"{abc['A']['skus']} SKUs make up {abc['A']['value_pct']}% of demand value",
        f"<p>Ranking by 2025 demand value puts {abc['A']['skus']} of {n_sku} SKUs ({abc['A']['sku_pct']}%) in Class A. Class B takes the next {abc['B']['skus']} SKUs to reach 95% of value. "
        f"The last {abc['C']['skus']} SKUs are {abc['C']['value_pct']}% of value, so they get the lightest controls.</p>",
        "c-pareto", "Pareto curve of cumulative demand value by SKU rank"),
    finding(
        "Planning on promised lead times leaves Class A under-protected",
        f"<p>I simulated 4,000 replenishment cycles for each of the {sim['n_a_skus']} Class A SKUs, sampling each supplier's real lead-time history. "
        f"The current rule (demand over the promised lead time plus one week) avoids a stockout in {sim['service_now_pct']}% of cycles, and in {sim['service_now_problem_pct']}% for SKUs from at-risk suppliers.</p>"
        f"<p>Safety stock built from lead-time and demand variability lifts service to {sim['service_new_pct']}%. "
        f"The cost is {sim['inventory_increase_pct']}% more Class A inventory value ({K(sim['inventory_increase_usd'])} on {M(sim['inventory_now_usd'], 2)}).</p>",
        "c-service", "Grouped bar chart comparing simulated cycle service level under the current and proposed policies",
        "Higher targets buy more service for more inventory.", controls=svc_controls),
    finding(
        f"Trend and seasonality regression cuts forecast error by {fc['improvement_vs_naive_pct']:.0f}%",
        f"<p>I tested four methods on three rolling 13-week windows. The regression has a weighted absolute percentage error (WAPE) of {ft[best_key]['wape_sku_week']}% per SKU-week "
        f"against {ft['naive']['wape_sku_week']}% for the naive baseline. On total weekly demand the gap is wider: {ft[best_key]['wape_total_demand']}% against {ft['naive']['wape_total_demand']}%. "
        "SKU-level error stays high because demand is lumpy, which is why safety stock still matters.</p>" + wape_table,
        "c-forecast", "Line chart of actual weekly demand against two forecasts over 13 weeks",
        "Last backtest window, total demand across all SKUs."),
])

fn_findings = "".join([
    finding(
        f"Revenue is on budget but EBITDA is {M(abs(eb_gap))} short",
        f"<p>Year to date, revenue is {P(rev_var, 1, True)} against budget, gross profit {P(gp_var, 1, True)} and EBITDA {P(eb_var, 1, True)}. "
        f"Volume beat plan by {M(br['volume_effect'])}. Price cost {M(abs(br['price_effect']))} and unit-cost inflation {M(abs(br['cost_effect']))}. "
        f"Marketing overspend added {M(abs(br['marketing_effect']))} and payroll and other costs {M(abs(br['payroll_other_effect']))}.</p>" + bu_table,
        "c-bridge", "Waterfall chart bridging budget EBITDA to actual EBITDA for 2026 year to date",
        "Bridge components sum exactly to the variance; the build script asserts it.", controls=bu_controls),
    finding(
        "Retail and E-commerce lose margin in different ways",
        f"<p>Retail gross margin fell from {mg[('Retail', '2023-Q1')]['gm_actual_pct']}% in 2023-Q1 to {mg[('Retail', '2026-Q3')]['gm_actual_pct']}% in 2026-Q3, against a "
        f"{mg[('Retail', '2026-Q3')]['gm_budget_pct']}% budget. Unit costs rose faster than the planned 2% and prices did not follow. Revenue is also {abs(retail_rev_var):.0f}% under plan, almost all of it volume.</p>"
        f"<p>E-commerce revenue is {ecom_rev_var:.0f}% over budget, yet EBITDA is only {K(ytd['E-commerce']['ebitda_act'] - ytd['E-commerce']['ebitda_bud'])} above. "
        f"Extra volume added {M(bru['E-commerce']['volume_effect'])} and discounting took back {M(abs(bru['E-commerce']['price_effect']))}.</p>",
        "c-margin", "Line chart of quarterly gross margin percentage by business unit",
        "Hover a point to see the budgeted margin for the same quarter."),
    finding(
        f"Wholesale customers now pay in {dso_story['end']:.0f} days, up from {dso_story['start']:.0f}",
        f"<p>Days sales outstanding rose from {dso_story['start']} days before mid-2024 to {dso_story['end']} days over the latest three months. "
        f"At current Wholesale sales that ties up about {M(dso_story['cash_trapped'], 2)} in receivables. "
        f"The other three units sit between {min(other_dso):.0f} and {max(other_dso):.0f} days.</p>",
        "c-dso", "Line chart of 3-month average days sales outstanding for Wholesale and the other units"),
    finding(
        f"The revenue model backtests at {bt['Total company']['reg']}% error and points to {M(fy['ebitda_outlook'])} FY2026 EBITDA",
        f"<p>I trained on data through December 2025 and predicted January to September 2026. Mean absolute percentage error (MAPE) on company revenue was {bt['Total company']['reg']}%, "
        f"against {bt['Total company']['snaive']}% for a same-month-last-year baseline.</p>"
        f"<p>Adding the fourth-quarter forecast to year-to-date actuals puts FY2026 revenue at {M(fy['rev_outlook'])} ({P(fy_rev_var, 1, True)} vs budget) "
        f"and EBITDA at {M(fy['ebitda_outlook'])} against a {M(fy['ebitda_budget'])} budget ({P(fy_eb_var, 1, True)}).</p>" + bt_table,
        "c-fan", "Line chart of monthly revenue with a 12-month forecast and an 80 percent interval band",
        "Shaded band is the 80% interval from resampled model residuals."),
    finding(
        "Price, unit cost and volume move EBITDA the most",
        f"<p>Holding other drivers fixed, a 2% price move changes next-12-month EBITDA by {M(torn['Price +/-2%']['up'])}, "
        f"a 3% unit-cost move by {M(torn['Unit cost inflation +/-3%']['up'])}, a 5% volume move by {M(torn['Volume +/-5%']['up'])} "
        f"and a 10% marketing move by {M(torn['Marketing spend +/-10%']['up'])}.</p>"
        "<p>Combining drivers gives the range below. Downside is price -2%, volume -5% and unit cost +3%. Upside is price +1%, volume +3% and unit cost -1%.</p>" + scen_tiles + scen_panel,
        "c-tornado", "Tornado chart of EBITDA sensitivity to price, unit cost, volume and marketing",
        "Favorable means costs lower, price higher, volume higher or marketing lower."),
])

# ------------------------------------------------------------------ chart data
def summary(text, results):
    items = "".join(f"<li>{r}</li>" for r in results)
    return f'<div class="summary"><div><h3>What I analyzed</h3><p>{text}</p></div><div><h3>Results</h3><ul>{items}</ul></div></div>'


summary1 = summary(
    f"Delivery records for 24 suppliers and 150 SKUs across {int(k['purchase_orders']):,} purchase orders and two years of demand. I looked for who delivers late or short, which SKUs matter most, and what a better reorder policy would cost.",
    [f"{k['otif_pct']}% of purchase orders arrive on time and in full. {prob['n']} of {prob['of']} suppliers fall below 60% and cause {prob['late_po_share_pct']}% of late deliveries.",
     f"{abc['A']['skus']} of {n_sku} SKUs ({abc['A']['sku_pct']}%) carry {abc['A']['value_pct']}% of demand value, so they get the tightest inventory controls.",
     f"A reorder rule that allows for lead-time variability lifts simulated service on those SKUs from {sim['service_now_pct']}% to {sim['service_new_pct']}% for {sim['inventory_increase_pct']}% more inventory ({K(sim['inventory_increase_usd'])}).",
     f"A trend and seasonality forecast has {fc['improvement_vs_naive_pct']:.0f}% less error than a naive forecast."])
summary2 = summary(
    "Budget and actual results for four business units from January 2023 to September 2026, focused on the 2026 year-to-date EBITDA shortfall and the outlook for the rest of the year.",
    [f"Revenue is {M(tot['rev_act'])} ({P(rev_var, 1, True)} vs budget) but EBITDA is {M(tot['ebitda_act'])} ({P(eb_var, 1, True)}), a {M(abs(eb_gap))} shortfall.",
     f"Price ({M(br['price_effect'], 1, True)}) and unit-cost inflation ({M(br['cost_effect'], 1, True)}) outweigh {M(br['volume_effect'], 1, True)} of extra volume. Retail and E-commerce carry the gap.",
     f"Wholesale customers pay in {dso_story['end']:.0f} days instead of {dso_story['start']:.0f}, tying up about {M(dso_story['cash_trapped'], 2)} of cash.",
     f"FY2026 EBITDA is heading for {M(fy['ebitda_outlook'])} against a {M(fy['ebitda_budget'])} budget. The revenue model backtests at {bt['Total company']['reg']}% error."])
ba = ba_content.make(BA, finding, K, None)
summary3 = summary(ba["summary_text"], ba["summary_results"])
ba_sql = sql_block(os.path.join(HERE, "business_analysis", "queries.sql"), "cohort_retention")

viz_rows = [
    ("Ranked bar with threshold", "Who fails the standard?", "Project 1", "c-suppliers"),
    ("Line with moving average", "Is performance trending?", "Project 1", "c-otif"),
    ("Pareto curve", "Where is value concentrated?", "Project 1", "c-pareto"),
    ("Grouped bars with selector", "What does each policy option buy?", "Project 1", "c-service"),
    ("Forecast comparison lines", "Which method predicts best?", "Project 1", "c-forecast"),
    ("Waterfall with filter", "Where did the variance come from?", "Project 2", "c-bridge"),
    ("Multi-line, direct labels", "Which unit is losing margin?", "Project 2", "c-margin"),
    ("Two-line comparison", "Is one group behaving differently?", "Project 2", "c-dso"),
    ("Fan chart with interval", "How uncertain is the outlook?", "Project 2", "c-fan"),
    ("Tornado with live sliders", "Which driver matters most?", "Project 2", "c-tornado"),
    ("Cohort heatmap", "Does retention change by cohort?", "Project 3", "c-heat"),
    ("Two-series trend", "Are two measures moving together?", "Project 3", "c-trend"),
    ("Grouped funnel bars", "Where does each channel lose people?", "Project 3", "c-funnel"),
    ("Segment bars with selector", "Which segment churns most?", "Project 3", "c-churn"),
    ("Bars with confidence whiskers", "Is the test result real?", "Project 3", "c-ab"),
    ("Bubble matrix", "What should we do first?", "Project 3", "c-prio"),
]
assert len(viz_rows) == 16
viz_table = ("<div class=\"tbl-wrap\"><table><thead><tr><th>Chart</th><th>Question it answers</th><th>See it in</th></tr></thead><tbody>"
             + "".join(f"<tr><td>{a}</td><td class=\"wrap\">{b}</td><td><a href=\"#f-{d}\">{c}</a></td></tr>" for a, b, c, d in viz_rows)
             + "</tbody></table></div>")
principles = [
    ("The title states the finding.", "Each chart sits under a headline such as \"OTIF has not improved in two years\", so the reader gets the point before reading the axes."),
    ("One color means one thing.", "Each business unit keeps its color across the charts that compare units. Orange marks the option or segment that needs attention."),
    ("Uncertainty stays visible.", "Forecasts carry an 80% interval, the A/B test carries confidence whiskers, and the business case shows a range."),
    ("Labels, a legend and a readout.", "Multi-series charts have direct labels and a legend, tooltips give exact values, and the controls print the numbers they change."),
    ("Honest axes.", "Bars start at zero. Lines may start higher, and the axis says so."),
    ("Built for any screen.", "Charts redraw for light and dark themes, fit a phone width, and the controls work with a keyboard."),
]
principles_html = "".join(f"<div class=\"principle\"><h3>{a}</h3><p>{b}</p></div>" for a, b in principles)

D = {
    "sc": {
        "scorecard": [{k_: r[k_] for k_ in ("supplier_id", "supplier_name", "country", "pos", "spend_share_pct",
                                              "otif_pct", "on_time_pct", "in_full_pct", "avg_delay_days")} for r in card],
        "problem": prob,
        "monthly": [{"month": m["month"], "otif": m["otif_pct"], "avg3": m["otif_3mo_avg"]} for m in months],
        "pareto": [{"x": r["rnk"], "y": r["cum_pct"]} for r in SC["abc"]["pareto"]],
        "abcA": abc["A"]["skus"], "abcAB": ab_n,
        "sim": sim,
        "fc": {"series": fc["series"], "labels": fc["labels"]},
    },
    "fn": {
        "bridge": {"total": br, "start": FN["bridge"]["start"], "end": FN["bridge"]["end"]},
        "margin": [{"bu": r["bu"], "qtr": r["qtr"], "a": r["gm_actual_pct"], "b": r["gm_budget_pct"]} for r in FN["margin"]],
        "monthly": [{"month": r["month"], "rev": r["rev_act"]} for r in FN["monthly"]],
        "dso": [{"bu": r["bu"], "month": r["month"], "v": r["dso_3mo"]} for r in FN["dso"]],
        "forecast": FN["forecast"],
        "tornado": FN["tornado"],
    },
}
D["ba"] = {"funnel": BA["funnel"], "heat": BA["heat"], "segments": BA["segments"], "overall_churn6": BA["overall_churn6"],
           "trend": BA["trend"], "experiment": BA["experiment"],
           "initiatives": [dict(i, short=ba_content.SHORT[n]) for n, i in enumerate(BA["initiatives"])]}
for _row in D["sc"]["scorecard"]:
    _row["spend"] = next(r["spend"] for r in card if r["supplier_id"] == _row["supplier_id"])
D["fn"]["by_bu"] = FN["bridge"]["by_bu"]
D["fn"]["ytd"] = [{"bu": r["bu"], "ebitda_bud": r["ebitda_bud"], "ebitda_act": r["ebitda_act"]} for r in FN["ytd"]["rows"]]

# ---------------------------------------------------------------------- CSS
CSS = r"""
/* Layout: one left-aligned column. Each project reads finding -> chart, then recommendations and limits. */
:root{
  --bg:#f9f9f7; --surface:#fcfcfb; --ink:#0b0b0b; --ink2:#52514e; --muted:#6c6a65;
  --line:#e1e0d9; --axis:#c3c2b7; --link:#1c5cab; --accent:#2a78d6; --code:#f1f0ec;
  --c1:#2a78d6; --c2:#eb6834; --c3:#1baf7a; --c4:#eda100;
  --good:#0ca30c; --bad:#d03b3b; --best:#e8f0fb;
  --font-sans:"IBM Plex Sans",system-ui,-apple-system,"Segoe UI",sans-serif;
  --font-mono:"IBM Plex Mono",ui-monospace,"SF Mono",Menlo,monospace;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --bg:#0d0d0d; --surface:#1a1a19; --ink:#f0efec; --ink2:#c3c2b7; --muted:#a09e97;
    --line:#2c2c2a; --axis:#383835; --link:#6da7ec; --accent:#3987e5; --code:#141413;
    --c1:#3987e5; --c2:#d95926; --c3:#199e70; --c4:#c98500; --best:#16263a; color-scheme:dark;
  }
}
:root[data-theme="dark"]{
  --bg:#0d0d0d; --surface:#1a1a19; --ink:#f0efec; --ink2:#c3c2b7; --muted:#a09e97;
  --line:#2c2c2a; --axis:#383835; --link:#6da7ec; --accent:#3987e5; --code:#141413;
  --c1:#3987e5; --c2:#d95926; --c3:#199e70; --c4:#c98500; --best:#16263a; color-scheme:dark;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth;scroll-padding-top:64px}
body{background:var(--bg);color:var(--ink);font-family:var(--font-sans);font-size:16px;line-height:1.6;
  padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));padding-block:0}
a{color:var(--link)}
a:focus-visible,summary:focus-visible{outline:2px solid var(--accent);outline-offset:3px}
.wrap{max-width:1100px;margin:0 auto}
nav{position:sticky;top:env(safe-area-inset-top,0px);z-index:5;background:var(--bg);border-bottom:1px solid var(--line);
  display:flex;align-items:center;justify-content:space-between;gap:24px;padding-block:14px;margin-inline:calc(-1 * max(16px,env(safe-area-inset-left,0px)));
  padding-inline:max(16px,env(safe-area-inset-left,0px))}
nav .brand{font-weight:600;white-space:nowrap}
nav .links{display:flex;gap:20px;overflow-x:auto;scrollbar-width:none}
nav .links a{color:var(--ink2);text-decoration:none;font-size:.9rem;white-space:nowrap}
nav .links a:hover{color:var(--ink)}
.lab,.tag,th,.eyebrow{font-family:var(--font-mono);font-size:.72rem;letter-spacing:.08em;text-transform:uppercase}
header.hero{padding-block:72px 56px;max-width:820px}
.eyebrow{color:var(--muted);margin:0 0 18px}
h1{font-size:clamp(2.3rem,6vw,3.7rem);line-height:1.05;letter-spacing:-.025em;font-weight:600;margin:0 0 20px;text-wrap:balance}
.lede{font-size:1.2rem;color:var(--ink2);margin:0 0 32px;max-width:62ch}
.jump{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:0;border-top:1px solid var(--line)}
.jump a{display:block;padding:20px 24px 20px 0;color:inherit;text-decoration:none;border-bottom:1px solid var(--line)}
.jump a:hover h2{color:var(--link)}
.jump h2{font-size:1.1rem;margin:0 0 6px}
.jump p{margin:0;color:var(--ink2);font-size:.95rem}
section{padding-block:64px;border-top:1px solid var(--line)}
section.first{border-top:0}
h2.sec{font-size:clamp(1.6rem,3.6vw,2.2rem);line-height:1.15;letter-spacing:-.02em;margin:0 0 12px;font-weight:600;text-wrap:balance}
p.intro{font-size:1.08rem;color:var(--ink2);max-width:68ch;margin:0 0 8px}
p.meta{font-family:var(--font-mono);font-size:.8rem;color:var(--muted);margin:0 0 32px}
.skills{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:32px 48px;margin-top:28px}
.skill h3{font-size:1.05rem;margin:0 0 6px}
.skill p{margin:0 0 8px;color:var(--ink2);font-size:.95rem;max-width:52ch}
.tag{color:var(--muted)}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:0;margin:8px 0 48px;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}
.kpi{display:flex;flex-direction:column;gap:2px;padding:20px 20px 20px 0}
.kpi+.kpi{padding-left:20px}
@media (min-width:700px){.kpi+.kpi{border-left:1px solid var(--line)}}
.kpi .lab{color:var(--muted)}
.kpi .val{font-size:2rem;font-weight:600;letter-spacing:-.02em;font-variant-numeric:tabular-nums;line-height:1.2}
.kpi .sub{color:var(--ink2);font-size:.88rem}
.kpis.three{grid-template-columns:repeat(auto-fit,minmax(150px,1fr));margin:20px 0 0}
.kpis.three .val{font-size:1.5rem}
.finding{display:grid;grid-template-columns:minmax(0,5fr) minmax(0,7fr);gap:40px;padding-block:36px;border-top:1px solid var(--line)}
.finding:first-of-type{border-top:0}
@media (max-width:900px){.finding{grid-template-columns:minmax(0,1fr);gap:20px}}
.ftext,.ffig{min-width:0}
.ftext h3{font-size:1.3rem;line-height:1.25;letter-spacing:-.01em;margin:0 0 12px;text-wrap:balance}
.ftext p{margin:0 0 12px;color:var(--ink2);max-width:60ch}
.ffig{margin:0}
.chart{position:relative;height:340px}
.chart.tall{height:600px}
figcaption{color:var(--muted);font-size:.85rem;margin-top:8px}
.tbl-wrap{overflow-x:auto;margin-top:16px}
table{border-collapse:collapse;width:100%;font-size:.88rem;font-variant-numeric:tabular-nums}
th,td{text-align:left;padding:8px 12px 8px 0;border-bottom:1px solid var(--line);white-space:nowrap}
th{color:var(--muted);font-weight:500}
th.n,td.n{text-align:right;padding-right:0;padding-left:12px}
tr.best td{background:var(--best)}
details.data-table{margin-top:12px}
details summary{cursor:pointer;color:var(--link);font-size:.9rem}
h3.sub{font-size:1.1rem;margin:40px 0 12px}
.recs{max-width:72ch;padding-left:1.2rem;margin:0}
.recs li{margin-bottom:12px;color:var(--ink2)}
.recs strong{color:var(--ink)}
.two{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:40px;margin-top:20px}
@media (max-width:900px){.two{grid-template-columns:minmax(0,1fr)}}
pre{background:var(--code);border:1px solid var(--line);border-radius:4px;padding:16px;margin:0;overflow-x:auto;font-family:var(--font-mono);font-size:.78rem;line-height:1.55;color:var(--ink)}
.limits{color:var(--ink2);max-width:60ch;margin:0}
.stack{font-family:var(--font-mono);font-size:.8rem;color:var(--muted);margin:0 0 4px}
ul.files{font-family:var(--font-mono);font-size:.85rem;color:var(--ink2);padding-left:1.1rem;margin:8px 0 0}
footer{border-top:1px solid var(--line);padding-block:48px 72px}
footer p{margin:0 0 8px;color:var(--ink2)}
.contact{font-family:var(--font-mono);font-size:.95rem;color:var(--ink);user-select:all}
.nav-r{display:flex;align-items:center;gap:16px;min-width:0}
.nav-r .links{min-width:0}
button,select,input[type=range]{font:inherit}
button:focus-visible,select:focus-visible,input:focus-visible{outline:2px solid var(--accent);outline-offset:3px}
.tbtn{font-family:var(--font-mono);font-size:.75rem;color:var(--ink);background:transparent;border:1px solid var(--axis);border-radius:4px;padding:6px 10px;cursor:pointer;white-space:nowrap}
.tbtn:hover{border-color:var(--ink2)}
.ctl{display:flex;flex-wrap:wrap;align-items:center;gap:8px 16px;margin:0 0 10px}
.ctl label,.ctl-text{font-size:.9rem;color:var(--ink)}
.ctl input[type=range]{width:min(220px,100%);accent-color:var(--accent)}
.try{color:var(--link);margin:0}
output{font-variant-numeric:tabular-nums;font-weight:600}
.readout{margin:0 0 12px;color:var(--ink2);font-size:.92rem;min-height:3em;max-width:68ch}
.readout strong{color:var(--ink);font-variant-numeric:tabular-nums}
.seg{display:inline-flex;border:1px solid var(--axis);border-radius:4px;overflow:hidden}
.seg button{font-family:var(--font-mono);font-size:.78rem;background:transparent;color:var(--ink);border:0;padding:7px 12px;cursor:pointer}
.seg button+button{border-left:1px solid var(--axis)}
.seg button[aria-pressed="true"]{background:var(--ink);color:var(--bg)}
select{background:var(--surface);color:var(--ink);border:1px solid var(--axis);border-radius:4px;padding:7px 10px;font-size:.9rem}
.scen{margin-top:20px;padding-top:16px;border-top:1px solid var(--line);display:grid;gap:10px}
.sl{display:grid;grid-template-columns:84px minmax(0,1fr) 56px;align-items:center;gap:12px}
.sl label{font-size:.9rem}
.sl input{width:100%;accent-color:var(--accent)}
.sl output{text-align:right;font-size:.9rem}
.scen-out{display:flex;flex-direction:column;gap:2px;margin-top:6px}
.scen-out .lab{color:var(--muted)}
.scen-out .val{font-size:2rem;font-weight:600;letter-spacing:-.02em;font-variant-numeric:tabular-nums;line-height:1.2}
.scen-out .sub{color:var(--ink2);font-size:.9rem}
#sc-reset{justify-self:start}
.hint{color:var(--muted);font-size:.9rem;margin:0 0 28px}
td.wrap{white-space:normal;min-width:180px}
.summary{display:grid;grid-template-columns:minmax(0,4fr) minmax(0,8fr);gap:32px;padding:24px 0;margin:0 0 8px;border-top:1px solid var(--line)}
@media (max-width:900px){.summary{grid-template-columns:minmax(0,1fr);gap:16px}}
.summary h3{font-size:.78rem;font-family:var(--font-mono);letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin:0 0 8px;font-weight:500}
.summary p{margin:0;color:var(--ink2);max-width:46ch}
.summary ul{margin:0;padding-left:1.1rem;color:var(--ink2)}
.summary li{margin-bottom:6px}
.brief{display:grid;grid-template-columns:minmax(0,4fr) minmax(0,8fr);gap:32px;margin:0 0 32px}
@media (max-width:900px){.brief{grid-template-columns:minmax(0,1fr);gap:16px}}
.brief .quote{font-size:1.1rem;color:var(--ink);margin:6px 0 12px;max-width:34ch}
#heat table{border-collapse:separate;border-spacing:2px;font-size:.72rem;width:auto;font-variant-numeric:tabular-nums}
#heat th,#heat td{padding:0;border:0;text-align:center;white-space:nowrap}
#heat thead th{color:var(--muted);height:22px;min-width:34px;font-weight:500}
#heat th.hc{text-align:left;color:var(--ink2);padding-right:8px;font-family:var(--font-mono);letter-spacing:0;text-transform:none;font-size:.72rem}
#heat td.hn{color:var(--muted);padding-right:8px;min-width:48px}
#heat td{height:22px;min-width:34px;border-radius:2px}
.heat-wrap{overflow-x:auto;padding-bottom:4px}
.heat-legend{display:flex;align-items:center;gap:10px;font-size:.78rem;color:var(--muted);margin-top:10px}
.heat-legend .bar{display:inline-block;height:10px;width:160px;border-radius:2px;flex:0 0 160px}
.principles{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:28px 44px;margin:28px 0 8px}
.principle h3{font-size:1.05rem;margin:0 0 6px}
.principle p{margin:0;color:var(--ink2);font-size:.95rem;max-width:46ch}
.email-row{display:flex;flex-wrap:wrap;align-items:center;gap:12px;margin:0 0 8px}
@media (prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
"""

# ---------------------------------------------------------------------- JS
JS = open(os.path.join(HERE, "page.js")).read()

# ----------------------------------------------------------------------- page
page = f"""<title>Nischal Malla Analytics Portfolio</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap">
<style>{CSS}</style>

<div class="wrap">
<nav>
  <span class="brand">Nischal Malla</span>
  <div class="nav-r"><div class="links"><a href="#skills">Skills</a><a href="#supply-chain">Supply chain</a><a href="#finance">Finance</a><a href="#business-analysis">Business analysis</a><a href="#visualization">Visualization</a><a href="#contact">Contact</a></div>
  <button type="button" id="theme-btn" class="tbtn">Dark mode</button></div>
</nav>

<header class="hero">
  <p class="eyebrow">Data analyst portfolio</p>
  <h1>Nischal Malla</h1>
  <p class="lede">I analyze operational and financial data in SQL and Python, test the result, and write it up as a recommendation a manager can act on.</p>
  <p class="hint">Every chart responds to hover. Controls marked Interactive let you change the question: move a threshold, pick a service target, filter by business unit, or build a scenario.</p>
  <div class="jump">
    <a href="#supply-chain"><h2>Supplier performance and inventory risk</h2><p>{prob['n']} suppliers miss 60% OTIF. A variability-aware reorder policy lifts simulated service on Class A SKUs from {sim['service_now_pct']}% to {sim['service_new_pct']}%.</p></a>
    <a href="#finance"><h2>Budget vs actual and outlook</h2><p>Revenue is on budget while EBITDA is {M(abs(eb_gap))} short. A price, volume and cost bridge shows where it went.</p></a>
    <a href="#business-analysis"><h2>Subscription growth and onboarding</h2><p>Retention is stable, so the leak is upstream. A tested onboarding checklist lifts activation {BA['experiment']['lift_pts']} points.</p></a>
  </div>
</header>

<section id="skills" class="first">
  <h2 class="sec">What the three projects show</h2>
  <p class="intro">Each of the three projects runs the full workflow: frame the question, model the data in SQL, analyze in Python, test the result, and state the limits. All datasets are synthetic and built to behave like real operating data, so the code and method are the point.</p>
  <div class="skills">{skills_html}</div>
</section>

<section id="supply-chain">
  <p class="eyebrow">Project 1</p>
  <h2 class="sec">Supplier performance and inventory risk</h2>
  <p class="intro">Where do late and short deliveries come from, and what would it cost to stop them hurting service?</p>
  <p class="meta">Synthetic data: 24 suppliers, 150 SKUs, {int(k['purchase_orders']):,} purchase orders, 104 weeks of demand (Jan 2024 to Dec 2025)</p>
  <p class="stack">SQL (CTEs, windows) / Python / pandas / scikit-learn / Monte Carlo</p>
  {summary1}
  {sc_kpis}
  {sc_findings}
  <h3 class="sub">Recommendations</h3>
  {sc_recs}
  <div class="two">
    <div><h3 class="sub" style="margin-top:0">The ABC query</h3><pre><code>{sql_block(os.path.join(HERE, 'supply_chain', 'queries.sql'), 'abc_classification')}</code></pre></div>
    <div><h3 class="sub" style="margin-top:0">Limits</h3><p class="limits">{sc_limits}</p>
      <ul class="files"><li>supply_chain/01_generate_data.py</li><li>supply_chain/queries.sql</li><li>supply_chain/02_analyze.py</li></ul></div>
  </div>
</section>

<section id="finance">
  <p class="eyebrow">Project 2</p>
  <h2 class="sec">Budget vs actual and outlook</h2>
  <p class="intro">Revenue is on plan. Why is EBITDA {M(abs(eb_gap))} short, and where is the year heading?</p>
  <p class="meta">Synthetic data: fictional omnichannel company, 4 business units, actuals Jan 2023 to Sep 2026, budget to Dec 2026</p>
  <p class="stack">SQL (conditional aggregation, LAG) / Python / scikit-learn / bootstrap intervals</p>
  {summary2}
  {fn_kpis}
  {fn_findings}
  <h3 class="sub">Recommendations</h3>
  {fn_recs}
  <div class="two">
    <div><h3 class="sub" style="margin-top:0">The EBITDA bridge query</h3><pre><code>{sql_block(os.path.join(HERE, 'finance', 'queries.sql'), 'ebitda_bridge')}</code></pre></div>
    <div><h3 class="sub" style="margin-top:0">Limits</h3><p class="limits">{fn_limits}</p>
      <ul class="files"><li>finance/01_generate_data.py</li><li>finance/queries.sql</li><li>finance/02_analyze.py</li></ul></div>
  </div>
</section>

<section id="business-analysis">
  <p class="eyebrow">Project 3</p>
  <h2 class="sec">Subscription growth, churn and onboarding</h2>
  <p class="intro">Retention looks weak and paid social keeps growing. Where should the business invest next quarter?</p>
  <p class="meta">Synthetic data: fictional fitness app, {BA['totals']['signups']:,} signups (Jan 2024 to Dec 2025), 14-day trial, three plans, one A/B test</p>
  <p class="stack">SQL (recursive CTE, set operations) / Python / A/B testing / cohort and funnel analysis</p>
  {summary3}
  {ba['kpis']}
  {ba['brief']}
  {ba['kpi_table']}
  {ba['findings']}
  <h3 class="sub">Recommendations</h3>
  {ba['recs']}
  <div class="two">
    <div><h3 class="sub" style="margin-top:0">The cohort retention query</h3><pre><code>{ba_sql}</code></pre></div>
    <div><h3 class="sub" style="margin-top:0">Limits</h3><p class="limits">{ba['limits']}</p>
      <ul class="files"><li>business_analysis/01_generate_data.py</li><li>business_analysis/queries.sql</li><li>business_analysis/02_analyze.py</li></ul></div>
  </div>
</section>

<section id="visualization">
  <p class="eyebrow">Visualization</p>
  <h2 class="sec">How I design charts</h2>
  <p class="intro">The three projects use {len(viz_rows)} chart types, each picked for the question it answers. Six rules apply to all of them.</p>
  <div class="principles">{principles_html}</div>
  <h3 class="sub">Chart index</h3>
  {viz_table}
</section>

<footer id="contact">
  <h2 class="sec">Contact</h2>
  <p>Open to mid-level data analyst roles.</p>
  <div class="email-row"><span class="contact" id="email-text">nischalmalla28@gmail.com</span><button type="button" id="copy-email" class="tbtn">Copy email</button></div>
  <p class="contact"><a href="https://www.linkedin.com/in/nischalmalla">linkedin.com/in/nischalmalla</a></p>
</footer>
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<script>
const D = {json.dumps(D, separators=(',', ':'))};
{JS}
</script>
"""
out = os.path.join(HERE, "portfolio.html")
open(out, "w").write(page)
open(os.path.join(HERE, "index.html"), "w").write(page)
os.makedirs(os.path.join(HERE, "assets"), exist_ok=True)
open(os.path.join(HERE, "assets", "page_script.js"), "w").write(f"const D = {json.dumps(D, separators=(',', ':'))};\n{JS}")
print("wrote", out, f"{len(page) / 1024:.0f} KB")
