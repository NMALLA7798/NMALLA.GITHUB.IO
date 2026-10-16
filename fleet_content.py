"""Page copy and tables for Project 4 (fleet management). Every figure is formatted from fleet/results.json."""

LANES = ["Long-haul", "Regional", "Urban"]


def d0(v, sign=False):
    pre = "-" if v < 0 else ("+" if sign else "")
    return f"{pre}${abs(v):,.0f}"


def make(FL, finding):
    cp, mt, st, fl = FL["cpm"], FL["maint"], FL["stats"], FL["fleet"]
    pb, lane = FL["payback_default"], st["lane"]
    A, C = cp["All"]["AI"], cp["All"]["Conventional"]
    ai_m, cv_m = mt["AI"], mt["Conventional"]
    mcpm_chg = (ai_m["cost_per_mile"] / cv_m["cost_per_mile"] - 1) * 100
    brk_chg = (ai_m["unplanned_per_100k"] / cv_m["unplanned_per_100k"] - 1) * 100
    prem = fl["premium"]
    conv_acq = sum(v for v in [0])  # placeholder to keep names explicit
    ages = FL["age"]
    n_urban_ai = sum(1 for v in FL["vehicles"] if v["type"] == "AI" and v["lane"] == "Urban")
    n_long_ai = sum(1 for v in FL["vehicles"] if v["type"] == "AI" and v["lane"] == "Long-haul")
    urban_loss_yr = -lane["Urban"]["diff"] * 12 * n_urban_ai
    watch_urban = sum(1 for w in FL["watch"] if w["lane"] == "Urban" and w["type"] == "AI")
    refresh = ai_m["kinds"]["Sensor refresh"]
    refresh_pct = refresh["cost"] / sum(k["cost"] for k in ai_m["kinds"].values()) * 100
    pay_l = pb["Long-haul"]["payback"]

    kpis = f"""
<div class="kpis">
  <div class="kpi"><span class="lab">Profit per vehicle-month</span><span class="val">{d0(A['profit_pvm'])} vs {d0(C['profit_pvm'])}</span><span class="sub">AI vs conventional, before adjusting for lane mix and age</span></div>
  <div class="kpi"><span class="lab">Unplanned breakdowns</span><span class="val">{brk_chg:+.0f}%</span><span class="sub">{ai_m['unplanned_per_100k']:.2f} vs {cv_m['unplanned_per_100k']:.2f} per 100,000 miles</span></div>
  <div class="kpi"><span class="lab">Maintenance cost per mile</span><span class="val">${ai_m['cost_per_mile']:.3f}</span><span class="sub">{mcpm_chg:+.0f}% vs ${cv_m['cost_per_mile']:.3f} conventional</span></div>
  <div class="kpi"><span class="lab">Acquisition premium</span><span class="val">{d0(prem)}</span><span class="sub">Pays back in {pay_l} months on long-haul lanes</span></div>
</div>"""

    # per-lane table
    rows = ""
    for l in LANES + ["All"]:
        a, c = cp[l]["AI"], cp[l]["Conventional"]
        name = "All lanes (mix differs)" if l == "All" else l
        rows += (f"<tr><td>{name}</td><td class='num'>{a['miles_pm']:,.0f} / {c['miles_pm']:,.0f}</td>"
                 f"<td class='num'>${a['total_cost']:.2f} / ${c['total_cost']:.2f}</td>"
                 f"<td class='num'>{d0(a['profit_pvm'])} / {d0(c['profit_pvm'])}</td></tr>")
    lane_table = ("<div class=\"tbl-wrap\"><table><thead><tr><th>Lane</th><th class='num'>Miles per month<br>AI / conv</th>"
                  "<th class='num'>Cost per mile<br>AI / conv</th><th class='num'>Profit per vehicle-month<br>AI / conv</th></tr></thead><tbody>"
                  + rows + "</tbody></table></div>")

    # maintenance kinds table
    krows = ""
    for k in ["Preventive", "Corrective", "Breakdown", "Sensor refresh"]:
        a, c = ai_m["kinds"][k], cv_m["kinds"][k]
        krows += (f"<tr><td>{k}</td><td class='num'>{a['per_100k']:.2f} / {c['per_100k']:.2f}</td>"
                  f"<td class='num'>{d0(a['avg_cost']) if a['events'] else '-'} / {d0(c['avg_cost']) if c['events'] else '-'}</td></tr>")
    maint_table = ("<div class=\"tbl-wrap\"><table><thead><tr><th>Event type</th><th class='num'>Per 100,000 miles<br>AI / conv</th>"
                   "<th class='num'>Average cost<br>AI / conv</th></tr></thead><tbody>" + krows + "</tbody></table></div>")

    watch_rows = "".join(f"<tr><td>{w['id']}</td><td>{w['type']}</td><td>{w['lane']}</td><td class='num'>{w['age']}</td><td class='num'>{d0(w['profit'])}</td></tr>" for w in FL["watch"])
    watch_table = ("<div class=\"tbl-wrap\"><table><thead><tr><th>Vehicle</th><th>Type</th><th>Lane</th><th class='num'>Age (months)</th>"
                   "<th class='num'>Profit, last 12 months</th></tr></thead><tbody>" + watch_rows + "</tbody></table></div>")

    lane_btns = "".join(f'<button type="button" data-l="{l}" aria-pressed="{"true" if l == "All" else "false"}">{l}</button>' for l in ["All"] + LANES)
    cpm_controls = f"""
<div class="ctl"><span class="lab try">Interactive</span><span id="fl-lane-lab" class="ctl-text">Lane</span>
  <div class="seg" id="fl-lane" role="group" aria-labelledby="fl-lane-lab">{lane_btns}</div></div>
<p class="readout" id="fl-cpm-read" aria-live="polite"></p>"""
    maint_btns = "".join(f'<button type="button" data-m="{k}" aria-pressed="{"true" if k == "events" else "false"}">{n}</button>'
                         for k, n in [("events", "Events per 100K miles"), ("cost", "Average cost per event"), ("down", "Downtime hours per 100K miles")])
    maint_controls = f"""
<div class="ctl"><span class="lab try">Interactive</span><span id="fl-m-lab" class="ctl-text">Measure</span>
  <div class="seg" id="fl-m" role="group" aria-labelledby="fl-m-lab">{maint_btns}</div></div>
<p class="readout" id="fl-m-read" aria-live="polite"></p>"""
    sc_btns = "".join(f'<button type="button" data-s="{l}" aria-pressed="{"true" if l == "All" else "false"}">{l}</button>' for l in ["All"] + LANES)
    scat_controls = f"""
<div class="ctl"><span class="lab try">Interactive</span><span id="fl-s-lab" class="ctl-text">Show lane</span>
  <div class="seg" id="fl-s" role="group" aria-labelledby="fl-s-lab">{sc_btns}</div></div>
<p class="readout" id="fl-s-read" aria-live="polite"></p>"""

    lane_radio = "".join(f'<button type="button" data-p="{l}" aria-pressed="{"true" if l == "Long-haul" else "false"}">{l}</button>' for l in LANES)
    calc_panel = f"""
<div class="scen" id="fl-calc">
  <p class="lab try">Interactive: should the next truck be AI-equipped?</p>
  <div class="ctl"><span id="fl-p-lab" class="ctl-text">Lane</span><div class="seg" id="fl-p" role="group" aria-labelledby="fl-p-lab">{lane_radio}</div></div>
  <div class="sl wide"><label for="fl-diesel">Diesel price</label><input type="range" id="fl-diesel" min="3" max="6" step="0.05" value="{FL['calc']['diesel_ttm']:.2f}"><output id="fl-diesel-out" for="fl-diesel"></output></div>
  <div class="sl wide"><label for="fl-prem">AI price premium</label><input type="range" id="fl-prem" min="20000" max="120000" step="1000" value="{prem:.0f}"><output id="fl-prem-out" for="fl-prem"></output></div>
  <div class="sl wide"><label for="fl-util">AI extra miles</label><input type="range" id="fl-util" min="-20" max="20" step="1" value="0"><output id="fl-util-out" for="fl-util"></output></div>
  <div class="sl wide"><label for="fl-soft">AI software fee</label><input type="range" id="fl-soft" min="500" max="3000" step="50" value="1650"><output id="fl-soft-out" for="fl-soft"></output></div>
  <div class="scen-out" aria-live="polite"><span class="lab">AI advantage over 7 years, discounted at 8%</span><span class="val" id="fl-npv"></span><span class="sub" id="fl-pay"></span></div>
  <button type="button" id="fl-reset" class="tbtn">Reset to fitted values</button>
</div>"""

    findings = "".join([
        finding(
            f"AI tractors earn {d0(lane['Long-haul']['diff'])} more per month on long-haul and lose {d0(abs(lane['Urban']['diff']))} on urban lanes",
            f"<p>Across the fleet an AI tractor makes {d0(A['profit_pvm'])} a month against {d0(C['profit_pvm'])}, but the lanes tell different stories. "
            f"On long-haul the AI unit runs {cp['Long-haul']['AI']['miles_pm'] / cp['Long-haul']['Conventional']['miles_pm'] * 100 - 100:.0f}% more miles, burns less fuel and spends less on drivers, which more than covers "
            f"its {d0(prem)} premium, software fee and extra depreciation. In dense urban work utilization barely moves, so the fixed costs of the technology are not recovered.</p>" + lane_table,
            "c-fl-cpm", "Stacked bar chart of cost per mile by cost category for AI and conventional tractors with revenue per mile",
            "Bars add up to total cost per mile; the line marks revenue per mile, so the gap is profit.", controls=cpm_controls),
        finding(
            f"The profit gap holds after adjusting for lane mix and age: {d0(st['adjusted'])} a month",
            f"<p>The naive gap is {d0(st['naive'])} per vehicle-month, but AI units are newer ({st['mean_age']['AI']:.0f} vs {st['mean_age']['Conventional']:.0f} months on average) and "
            f"{st['ai_share_longhaul'] * 100:.0f}% of them run long-haul against {st['conv_share_longhaul'] * 100:.0f}% of conventional units. A regression controlling for lane, age and season gives "
            f"{d0(st['adjusted'])} with a 95% interval of {d0(st['adj_lo'])} to {d0(st['adj_hi'])} (bootstrapped by vehicle, so one truck's months are not counted as independent).</p>"
            f"<p>By lane the picture is stark: long-haul {d0(lane['Long-haul']['diff'], True)}, regional {d0(lane['Regional']['diff'], True)} "
            f"(interval {d0(lane['Regional']['lo'])} to {d0(lane['Regional']['hi'])}, so not distinguishable from zero) and urban {d0(lane['Urban']['diff'], True)}.</p>",
            "c-fl-lane", "Bar chart of the AI minus conventional profit gap per vehicle-month by lane with 95 percent confidence whiskers",
            "Whiskers are 95% intervals from a vehicle-level bootstrap."),
        finding(
            f"Predictive maintenance cuts breakdowns {abs(brk_chg):.0f}%, but repairs cost more per event",
            f"<p>AI units log {ai_m['unplanned_per_100k']:.2f} unplanned breakdowns per 100,000 miles against {cv_m['unplanned_per_100k']:.2f}, and lose less time to the shop "
            f"({ai_m['downtime_per_vm']:.1f} vs {cv_m['downtime_per_vm']:.1f} hours a month). Condition-based servicing also stretches the preventive interval. "
            f"Offsetting that, corrective repairs average {d0(ai_m['kinds']['Corrective']['avg_cost'])} against {d0(cv_m['kinds']['Corrective']['avg_cost'])} because sensors and calibration add parts and labor, "
            f"and sensor refreshes take {refresh_pct:.0f}% of AI maintenance spend.</p>" + maint_table,
            "c-fl-maint", "Grouped bar chart comparing maintenance events by type for AI and conventional tractors",
            "Switch the measure to see frequency, cost per event or downtime.", controls=maint_controls),
        finding(
            "AI maintenance cost climbs faster with age and overtakes conventional after about two years",
            f"<p>For the first two years an AI tractor costs less per mile to maintain (${ages['AI'][0]:.2f} to ${ages['AI'][1]:.2f}, against ${ages['Conventional'][0]:.2f} and ${ages['Conventional'][1]:.2f}). "
            f"From month 24 the sensor and compute refresh cycle pushes it to ${ages['AI'][2]:.2f} per mile at 24 to 35 months and ${ages['AI'][3]:.2f} at 36 to 47, above conventional units' ${ages['Conventional'][2]:.2f} and ${ages['Conventional'][3]:.2f}. "
            "The 48+ month bucket is hidden for AI because only a handful of vehicle-months exist. Any business case that uses first-year maintenance savings overstates the benefit.</p>",
            "c-fl-age", "Line chart of maintenance cost per mile by vehicle age bucket for AI and conventional tractors",
            "Buckets with fewer than 100 vehicle-months are not drawn."),
        finding(
            f"{watch_urban} of the 8 weakest earners are urban AI tractors",
            f"<p>Each dot is one tractor's operating profit over the last 12 months. Every vehicle is profitable, but the lowest earners cluster in urban AI work "
            f"({n_urban_ai} units). Moving them to long-haul or swapping them for conventional units is worth about {d0(urban_loss_yr)} a year at the fitted urban gap.</p>" + watch_table,
            "c-fl-scat", "Scatter plot of vehicle age against trailing twelve month operating profit, colored by type",
            "Hover a dot for the vehicle id, lane and profit.", controls=scat_controls),
        finding(
            f"On long-haul an AI tractor pays back its premium in {pay_l} months; on regional and urban it does not",
            f"<p>The calculator projects each lane's cash flow over a 7-year life using the fitted per-mile economics, the age-driven maintenance slope, and residual values "
            f"({FL['calc']['cells']['Long-haul|AI']['resid'] * 100:.0f}% for AI, {FL['calc']['cells']['Long-haul|Conventional']['resid'] * 100:.0f}% for conventional). At today's diesel price the discounted 7-year advantage is "
            f"{d0(pb['Long-haul']['npv_adv'], True)} per truck on long-haul, {d0(pb['Regional']['npv_adv'], True)} on regional and {d0(pb['Urban']['npv_adv'], True)} on urban.</p>"
            "<p>Move the sliders to find the break-even: how much utilization advantage, premium or software fee the regional case needs to turn positive.</p>" + calc_panel,
            "c-fl-pay", "Line chart of cumulative cash advantage of an AI tractor over a conventional one across seven years",
            "The line starts at minus the extra purchase price and crosses zero at payback."),
    ])

    summary_text = (f"{fl['vehicles']} tractors ({fl['ai']} AI-equipped, {fl['conv']} conventional) over {fl['vehicle_months']:,} vehicle-months and {fl['events']:,} maintenance events. "
                    "I compared acquisition cost, operating cost, maintenance and profit, adjusted for lane and age, and built a model of the buy decision.")
    summary_results = [
        f"AI tractors earn {d0(st['adjusted'])} more per vehicle-month after adjusting for lane, age and season (95% interval {d0(st['adj_lo'])} to {d0(st['adj_hi'])}).",
        f"The gain is entirely long-haul ({d0(lane['Long-haul']['diff'], True)}). Regional is flat and urban loses {d0(abs(lane['Urban']['diff']))} per vehicle-month.",
        f"Unplanned breakdowns fall {abs(brk_chg):.0f}% and maintenance cost per mile {abs(mcpm_chg):.0f}%, but AI maintenance overtakes conventional after about two years as sensors age.",
        f"The {d0(prem)} premium pays back in {pay_l} months on long-haul. Buying AI for regional or urban lanes loses money over a 7-year life at current prices.",
    ]
    recs = f"""
<ol class="recs">
  <li><strong>Buy AI-equipped tractors for long-haul only.</strong> Payback is {pay_l} months and the 7-year advantage is {d0(pb['Long-haul']['npv_adv'])} per truck. Hold regional purchases until the premium or software fee falls.</li>
  <li><strong>Move or replace the {n_urban_ai} urban AI units.</strong> At the fitted gap they cost about {d0(urban_loss_yr)} a year against conventional units. Reassigning them to long-haul lanes is the cheaper fix.</li>
  <li><strong>Budget for the sensor refresh.</strong> Put an accrual for the month-30 to month-48 refresh into the AI business case; it is {refresh_pct:.0f}% of AI maintenance spend and absent from first-year numbers.</li>
  <li><strong>Negotiate the software fee.</strong> At $1,650 a month it is the single largest AI-specific operating cost; each $500 saved adds $6,000 per truck per year.</li>
</ol>"""
    limits = ("The data is synthetic and the carrier is fictional. 'AI' stands for AI-equipped tractors (driver-assist or autonomous-capable with AI predictive maintenance and routing), not fully driverless operation, "
              "and the planted effects are assumptions, not industry benchmarks. The payback model holds rates, revenue per mile and diesel flat, uses a straight-line age slope for maintenance, and ignores financing beyond an 8% discount rate, "
              "taxes and incentives. The bootstrap resamples vehicles, so it reflects fleet-level noise but not a change in freight market conditions.")
    return dict(kpis=kpis, findings=findings, recs=recs, limits=limits, summary_text=summary_text, summary_results=summary_results)
