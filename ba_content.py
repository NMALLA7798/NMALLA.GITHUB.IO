"""Page copy and tables for Project 3 (business analysis). Every figure is formatted from results.json."""


def pf(p):
    return "below 0.001" if p < 0.001 else f"{p:.3f}"


def sgn(v, d=1):
    return f"{'+' if v > 0 else '-' if v < 0 else ''}{abs(v):.{d}f}"


SHORT = ["Checklist rollout", "Shift social budget", "Early-warning outreach", "Win-back campaign", "Referral expansion"]


def make(BA, finding, K, sql_text):
    k, ex, rc, dc, val = BA["kpis"], BA["experiment"], BA["retention_check"], BA["decomp"], BA["value"]
    fun = {r["channel"]: r for r in BA["funnel"]}
    ue = {r["channel"]: r for r in BA["unit_econ"]}
    tr, ini = BA["trend"], BA["initiatives"]
    seg = {d: {r["segment"]: r for r in rows} for d, rows in BA["segments"].items()}
    a3 = lambda key: sum(r[key] for r in tr[:3]) / 3
    b3 = lambda key: sum(r[key] for r in tr[-3:]) / 3
    share0, share1, act0, act1 = a3("paid_social_share_pct"), b3("paid_social_share_pct"), a3("activation_pct"), b3("activation_pct")
    blended_return = sum(r["revenue6"] for r in BA["unit_econ"]) / sum(r["spend"] for r in BA["unit_econ"])
    n_total = ex["n_control"] + ex["n_variant"]
    i1, i2 = ini[0], ini[1]
    act = seg["7-day activation"]
    tk = seg["Support tickets in first 30 days"]
    ch = seg["Channel"]

    kpis = f"""
<div class="kpis">
  <div class="kpi"><span class="lab">Activation (7 days)</span><span class="val">{k['activation_pct']}%</span><span class="sub">of {int(k['signups']):,} signups, Jan to Aug 2025</span></div>
  <div class="kpi"><span class="lab">Signup to paid</span><span class="val">{k['conversion_pct']}%</span><span class="sub">after the 14-day trial</span></div>
  <div class="kpi"><span class="lab">90-day retention</span><span class="val">{k['retained_90d_pct']}%</span><span class="sub">of paying customers</span></div>
  <div class="kpi"><span class="lab">Paid social return</span><span class="val">${ue['Paid social']['return_per_dollar']:.2f}</span><span class="sub">6-month revenue per $1 spent</span></div>
</div>"""

    verdicts = [
        ("Retention after payment is falling", "Not supported",
         f"Month-3 retention averages {rc['first_half_avg']}% for earlier cohorts and {rc['second_half_avg']}% for later ones."),
        ("Acquisition quality is falling", "Supported",
         f"Activation fell from {act0:.1f}% to {act1:.1f}% as paid social grew from {share0:.1f}% to {share1:.1f}% of signups."),
        ("Early activation drives churn", "Supported",
         f"Six-month churn is {act['Not activated']['churn6_pct']}% without week-one activation and {act['Activated']['churn6_pct']}% with it."),
        ("An onboarding change can lift activation", "Supported",
         f"The A/B test shows +{ex['lift_pts']} points (95% CI {ex['lift_ci'][0]} to {ex['lift_ci'][1]})."),
    ]
    brief_rows = "".join(
        f"<tr><td>H{i + 1}. {h}</td><td><strong>{'&#10003; ' if v == 'Supported' else '&#10007; '}{v}</strong></td><td>{e}</td></tr>"
        for i, (h, v, e) in enumerate(verdicts))
    brief = f"""
<div class="brief">
  <div><p class="lab try">The ask (fictional stakeholder)</p>
  <p class="quote">Growth leadership: retention looks weak and paid social keeps growing. Where should we invest next quarter?</p>
  <p class="limits">I turned it into four testable hypotheses, defined the KPIs before touching the data, and let the results overturn the first one.</p></div>
  <div class="tbl-wrap"><table><thead><tr><th>Hypothesis</th><th>Verdict</th><th>Evidence</th></tr></thead><tbody>{brief_rows}</tbody></table></div>
</div>"""

    kpi_rows = [
        ("Activation rate", "Share of signups that complete a first workout within 7 days", "customers.activated_7d / Product", f"{k['activation_pct']}%"),
        ("Signup to paid", "Share of signups that start paying after the 14-day trial", "customers.converted / Growth", f"{k['conversion_pct']}%"),
        ("90-day retention", "Share of paying customers still subscribed 3 months after first payment", "paid_start_date, cancel_date / Customer success", f"{k['retained_90d_pct']}%"),
        ("6-month churn", "Share of paying customers who cancel within 6 months of first payment", "paid_start_date, cancel_date / Customer success", f"{BA['overall_churn6']}%"),
        ("Return on acquisition spend", "Revenue in the first 6 months divided by cost per signup times signups", "customers, channel_costs / Finance", f"${blended_return:.2f} per $1"),
        ("Average revenue per paying customer", "Mean monthly price of paying customers", "customers.monthly_price / Finance", f"${k['arpu']:.2f} a month"),
    ]
    kpi_table = ("<h3 class=\"sub\">KPI dictionary</h3><div class=\"tbl-wrap\"><table><thead><tr><th>KPI</th><th>Definition</th><th>Source / owner</th><th class=\"n\">Current</th></tr></thead><tbody>"
                 + "".join(f"<tr><td>{a}</td><td class=\"wrap\">{b}</td><td class=\"wrap\">{c}</td><td class=\"n\">{d}</td></tr>" for a, b, c, d in kpi_rows)
                 + "</tbody></table></div>")

    heat = """
<div class="heat-wrap" role="region" aria-label="Cohort retention heatmap, scrollable">
  <div id="heat"></div>
  <div class="heat-legend"><span>50%</span><span class="bar" id="heat-bar"></span><span>100% still subscribed</span></div>
</div>"""

    seg_sel = """
<div class="ctl"><span class="lab try">Interactive</span>
  <label for="seg-sel">Cut churn by</label>
  <select id="seg-sel"><option>Channel</option><option>7-day activation</option><option>Support tickets in first 30 days</option><option>Plan</option></select></div>"""

    ab_rows = [
        ("Customers", f"{ex['n_control']:,} control, {ex['n_variant']:,} checklist"),
        ("Activation (7 days)", f"{ex['act_control']}% vs {ex['act_variant']}%"),
        ("Lift", f"+{ex['lift_pts']} points, 95% CI {ex['lift_ci'][0]} to {ex['lift_ci'][1]}, p {pf(ex['p_value'])}"),
        ("Signup to paid", f"{ex['paid_control']}% vs {ex['paid_variant']}%, +{ex['paid_lift_pts']} points (CI {ex['paid_lift_ci'][0]} to {ex['paid_lift_ci'][1]})"),
        ("Guardrail: tickets per customer", f"{ex['tickets_control']} vs {ex['tickets_variant']}"),
        ("Split check (50/50)", f"p = {ex['srm_p']}, largest channel-mix gap {ex['max_mix_gap_pts']} points"),
        ("Smallest effect detectable", f"{ex['mde_pts']} points at 80% power"),
    ]
    ab_table = ("<div class=\"tbl-wrap\"><table><tbody>"
                + "".join(f"<tr><td>{a}</td><td class=\"wrap\">{b}</td></tr>" for a, b in ab_rows) + "</tbody></table></div>")

    def call(i):
        return "Do not do" if i["impact"] < 0 else ("Do now" if i["impact"] >= 20000 else "Pilot first")

    ini_rows = "".join(
        f"<tr><td>{SHORT[n]}</td><td class='n'>{'-' if i['impact'] < 0 else ''}${abs(i['impact']):,.0f}</td><td class='n'>{i['effort']}</td><td><strong>{call(i)}</strong></td><td class='wrap'>{i['basis']}</td></tr>"
        for n, i in enumerate(ini))
    ini_table = ("<div class=\"tbl-wrap\"><table><thead><tr><th>Initiative</th><th class=\"n\">Impact a year</th><th class=\"n\">Effort (1 to 5)</th><th>Call</th><th>Assumption</th></tr></thead><tbody>"
                 + ini_rows + "</tbody></table></div>")

    findings = "".join([
        finding("Retention is stable, so churn after payment is not the problem",
                f"<p>The first hypothesis was that retention is falling. Cohort retention says otherwise. Three months after the first payment, {rc['month3_min']}% to {rc['month3_max']}% of each cohort is still subscribed. "
                f"The average is {rc['first_half_avg']}% for the earlier half of cohorts and {rc['second_half_avg']}% for the later half.</p>"
                "<p>Rows with fewer columns are recent cohorts that have not had time to age.</p>",
                "", "Heatmap of retention by paid-start cohort and months since first payment",
                "Rows are cohorts by month of first payment. Hover a cell for the cohort size.", custom=heat),
        finding("Acquisition quality is slipping as paid social grows",
                f"<p>Paid social grew from {share0:.1f}% of signups in Q1 2024 to {share1:.1f}% in Q4 2025, and 7-day activation fell from {act0:.1f}% to {act1:.1f}%.</p>"
                f"<p>Comparing H1 2024 with H1 2025, signup-to-paid conversion slipped from {dc['start']}% to {dc['end']}%. The channel shift explains {sgn(dc['mix'])} points. "
                f"Falling conversion inside paid social ({dc['social_conv_A']}% to {dc['social_conv_B']}%) explains {sgn(dc['rate_social'])}, and the other channels add {sgn(dc['rate_other'])}.</p>",
                "c-trend", "Line chart of monthly paid social share of signups and activation rate"),
        finding("Each channel loses customers at a different step",
                f"<p>In January to August 2025, {fun['Paid social']['activation_pct']}% of paid-social signups activated, against {fun['Referral']['activation_pct']}% for referral. "
                f"Paid social also keeps the fewest customers to day 90: {fun['Paid social']['retained_pct_of_signups']}% of signups, against {fun['Referral']['retained_pct_of_signups']}% for referral.</p>"
                f"<p>Paid social returns ${ue['Paid social']['return_per_dollar']:.2f} of six-month revenue per $1 spent. Referral returns ${ue['Referral']['return_per_dollar']:.2f} and partners ${ue['Partner']['return_per_dollar']:.2f}.</p>",
                "c-funnel", "Grouped bar chart of funnel stages by acquisition channel", "Each bar is a share of that channel's signups."),
        finding("Activation is the strongest churn signal",
                f"<p>Among customers who started paying by June 2025, {act['Not activated']['churn6_pct']}% of those who did not activate in week one cancelled within six months, against {act['Activated']['churn6_pct']}% of activated customers.</p>"
                f"<p>Paid-social customers churn at {ch['Paid social']['churn6_pct']}% and referral customers at {ch['Referral']['churn6_pct']}%. Two or more support tickets in the first month also flag risk: {tk['2 or more']['churn6_pct']}% churn, against {tk['0 tickets']['churn6_pct']}% with none.</p>",
                "c-churn", "Bar chart of six-month churn by customer segment", f"Orange bars are above the all-customer average of {BA['overall_churn6']}%.", controls=seg_sel + '<p class="readout" id="seg-read" aria-live="polite"></p>'),
        finding(f"The onboarding checklist lifts activation by {ex['lift_pts']} points",
                f"<p>I tested the checklist on {n_total:,} signups from July to September 2025, split 50/50. Activation was {ex['act_variant']}% with the checklist and {ex['act_control']}% without. "
                f"Small tests tend to overstate winners, so I plan with the low end of the interval.</p>" + ab_table,
                "c-ab", "Bar chart of activation rate for control and checklist with 95 percent confidence whiskers", "Whiskers are 95% confidence intervals."),
        finding("One initiative clearly leads and one idea needs proof first",
                f"<p>I sized five initiatives from the data. Rolling out the checklist is worth about {K(i1['impact'])} of first-six-month revenue per year of signups (range {K(i1['impact_low'])} to {K(i1['impact_high'])}). "
                f"Moving paid-social budget to search loses money unless search absorbs it at {i2['breakeven_efficiency_pct']:.0f}% of its current efficiency or better, and I assumed 50%.</p>"
                "<p>The other three are small and worth piloting with a control group before scaling. Revenue counts only six months per customer, so every figure is conservative. Effort scores are my estimates.</p>" + ini_table,
                "c-prio", "Bubble chart of initiatives by effort and annual revenue impact", "Bubble size is the number of customers affected."),
    ])

    recs = f"""
<ol class="recs">
  <li><strong>Roll out the onboarding checklist to every signup.</strong> It is the only initiative with a clear, measured effect, worth about {K(i1['impact'])} a year, or {K(i1['impact_low'])} at the low end of the interval.</li>
  <li><strong>Hold paid-social spend flat until its activation recovers.</strong> It returns ${ue['Paid social']['return_per_dollar']:.2f} per $1 in six months and its customers churn at {ch['Paid social']['churn6_pct']}%.</li>
  <li><strong>Hold off on moving that budget to search.</strong> The move only pays if search keeps {i2['breakeven_efficiency_pct']:.0f}% of its current efficiency at higher spend. This data cannot show that, so test a small shift first.</li>
  <li><strong>Pilot referral expansion and early-warning outreach.</strong> Run each with a control group and decide on measured results.</li>
  <li><strong>Report four KPIs weekly:</strong> activation, signup to paid, 90-day retention and return per $1 by channel, using the definitions above.</li>
</ol>"""

    limits = ("The dataset is synthetic and the app is fictional. Channel costs per signup are assumptions. Business-case figures count only the first six months of revenue per customer and rest on the stated assumptions, "
              "so they rank initiatives and are not a forecast. The A/B test assumes the checklist effect is the same across channels, and the planned rollout should be monitored for that.")

    summary_text = (
        f"A fictional fitness app with {BA['totals']['signups']:,} signups over two years, a funnel, subscription records and an onboarding A/B test. "
        "I tested why growth economics look weaker and what to do first.")
    summary_results = [
        f"Retention after payment is stable ({rc['first_half_avg']}% vs {rc['second_half_avg']}% at month 3). The real leak is acquisition: activation fell from {act0:.1f}% to {act1:.1f}% as paid social grew to {share1:.1f}% of signups.",
        f"Activating in week one cuts six-month churn from {act['Not activated']['churn6_pct']}% to {act['Activated']['churn6_pct']}%. Paid social returns ${ue['Paid social']['return_per_dollar']:.2f} per $1 of spend.",
        f"The onboarding checklist lifts activation {ex['lift_pts']} points (95% CI {ex['lift_ci'][0]} to {ex['lift_ci'][1]}), worth about {K(i1['impact'])} a year in six-month revenue. Moving budget to search only pays if search holds {i2['breakeven_efficiency_pct']:.0f}% of its efficiency.",
    ]
    sql = sql_text
    return dict(kpis=kpis, brief=brief, kpi_table=kpi_table, findings=findings, recs=recs, limits=limits,
                summary_text=summary_text, summary_results=summary_results, sql=sql)
