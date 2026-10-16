"""Builds the personal site: index (home), pm (product case study) and projects (analytics case studies)."""
import html, json, os, re
import site_common as C
HERE = os.path.dirname(os.path.abspath(__file__))
PM = json.load(open(f"{HERE}/pm/results.json"))
SC = json.load(open(f"{HERE}/supply_chain/results.json"))
FN = json.load(open(f"{HERE}/finance/results.json"))
BA = json.load(open(f"{HERE}/business_analysis/results.json"))
FL = json.load(open(f"{HERE}/fleet/results.json"))
OUT = f"{HERE}/site"; os.makedirs(OUT, exist_ok=True)
pc = lambda x, d=1: f"{x * 100:.{d}f}%"
usd = lambda x: ("-" if x < 0 else "") + f"${abs(x):,.0f}"
BL, LA, AS = PM["baseline"], PM["launch"], PM["assist"]
ASM = PM["assumptions"]

NAV = lambda base="": f"""
<nav class="top"><div class="wrap">
  <a class="brand" href="{base or 'index.html'}">Nischal Malla</a><span class="tag">Operations · Analytics · AI · Product</span>
  <div class="links"><a href="index.html#work">Work</a><a href="projects.html">Analytics</a><a href="pm.html">Product case</a><a href="index.html#experience">Experience</a><a href="index.html#skills">Skills</a><a href="index.html#contact">Contact</a>
  <button type="button" id="theme" class="theme">Dark mode</button></div></div></nav>"""

FOOT = f"""<footer><div class="wrap"><span>© Nischal Malla. Case-study data is synthetic unless stated. Figures from my employers are not shown.</span><span><a href="{C.LINKEDIN}" rel="noopener">LinkedIn</a></span></div></footer>"""

# ------------------------------------------------------------------ HOME
sc_k, prob = SC["kpis"], SC["problem"]
ytd = FN["ytd"]["total"]; eb_gap = (ytd["ebitda_bud"] - ytd["ebitda_act"]) / 1e6
fl_pb = FL["payback_default"]["Long-haul"]["payback"]
fl_urb = FL["stats"]["lane"]["Urban"]["diff"]
skills = {
 "SQL": ("At Amazon I analyze SQL-driven event data and turn it into client-ready reports. In my case studies: recursive-CTE cohorts, window functions, ABC classification and EBITDA bridges.", "See the SQL in the case studies", "projects.html#business-analysis"),
 "Tableau": ("I build and maintain Tableau and Excel dashboards that track operational metrics and action items for tiered decision-making at Amazon.", "How I design charts", "projects.html#visualization"),
 "Excel": ("Daily tool for budgets, action logs and KPI tracking across a $3.5M+ program budget.", "See a budget vs actual analysis", "projects.html#finance"),
 "Power BI": ("At Keller Williams I built Power BI and Excel dashboards to log action items, track ROI and escalate risks, cutting manual reporting by 20%.", "Experience", "#experience"),
 "Python": ("pandas, NumPy and scikit-learn for forecasting backtests, Monte Carlo simulation, bootstrap intervals and the AI threshold model in my product case.", "See the Python analyses", "projects.html#supply-chain"),
 "Forecasting": ("Rolling-origin backtests against a naive baseline, with prediction intervals and scenarios.", "See the forecast backtests", "projects.html#finance"),
 "Lean and process design": ("I applied lean methodology and process design to coordinate events across five fulfillment centers, improving coordination efficiency by 20%.", "Experience", "#experience"),
 "Change control and budgets": ("Managed timelines, vendors and a $3.5M+ budget under change control, keeping delivery on time and compliant.", "Experience", "#experience"),
 "Risk escalation": ("I keep action and risk logs and escalate to senior management early, with a recommendation attached.", "Experience", "#experience"),
 "Stakeholder management": ("Facilitated meetings across HR, Marketing and Finance, documented outcomes in Confluence and drafted leadership communications.", "Experience", "#experience"),
 "Supply chain and logistics": ("Fulfillment-center operations by day. In the case studies: supplier OTIF scorecards, safety stock simulation and fleet cost per mile.", "Supplier performance case study", "projects.html#supply-chain"),
 "Product requirements": ("I wrote a full product requirements case for an AI triage feature: problem, goals and non-goals, success metrics, risks and a phased rollout.", "Read the product case", "pm.html"),
 "Prioritization (RICE)": ("An editable RICE model ranks seven candidate features. Change reach, impact, confidence or effort and the ranking updates.", "Try the RICE model", "pm.html#prioritization"),
 "Experiment design": ("Sample sizing, split checks and guardrail metrics, in the A/B test on onboarding and the rollout plan for the AI feature.", "See the A/B test", "projects.html#business-analysis"),
 "AI feature evaluation": ("Confidence thresholds, precision floors and error costs decide what an AI feature may do on its own. Move the slider in the product case.", "Try the threshold simulator", "pm.html#simulator"),
 "AWS": ("AWS Certified Solutions Architect, Professional (2024). Cloud operations background alongside the operations work.", "Certifications", "#experience"),
}
groups = [("Operations and programs", ["Lean and process design", "Change control and budgets", "Risk escalation", "Stakeholder management", "Supply chain and logistics"]),
          ("Data and analytics", ["SQL", "Tableau", "Excel", "Power BI", "Python", "Forecasting"]),
          ("Product and AI", ["Product requirements", "Prioritization (RICE)", "Experiment design", "AI feature evaluation", "AWS"])]
cols = "".join(f'<div class="col"><h3>{g}</h3><div class="chips">' + "".join(f'<button type="button" class="chip skill" data-k="{k}" aria-pressed="false">{k}</button>' for k in ks) + "</div></div>" for g, ks in groups)
services = [("Program delivery", "Plan timelines, vendors and budgets, run change control, and keep stakeholders aligned from kickoff to close."),
            ("Operational analytics", "SQL, Tableau and Excel dashboards that turn event data into decisions and action items."),
            ("Process design", "Lean methods to remove steps, clarify ownership and speed up coordination across sites."),
            ("Risk and escalation", "Early risk logs, clear status updates and recommendations ready for senior management."),
            ("Supply chain and logistics", "Supplier performance, inventory policy and fleet economics, from data to recommendation."),
            ("AI-enabled operations", "Scoping AI features for operations teams: where they help, where they must not act alone.")]
svc = "".join(f'<div class="card"><h3>{a}</h3><p>{b}</p></div>' for a, b in services)
cards = [
 ("Supplier performance and inventory risk", "Supply chain", f"{prob['n']} of {prob['of']} suppliers miss 60% OTIF. A variability-aware reorder policy lifts simulated service on top SKUs.", f"{sc_k['otif_pct']}%", "overall OTIF", "projects.html#supply-chain"),
 ("Fleet profitability: AI vs conventional trucks", "Logistics", f"AI-equipped tractors pay back a $75K premium in {fl_pb} months on long-haul, and lose money on urban lanes.", f"{fl_pb} months", "long-haul payback", "projects.html#fleet"),
 ("Budget vs actual and outlook", "Finance", "Revenue on plan, EBITDA short. A price, volume and cost bridge shows where the margin went.", f"-${eb_gap:.1f}M", "EBITDA vs budget, YTD", "projects.html#finance"),
 ("Subscription growth and onboarding", "Business analysis", "Retention is stable, so the leak is upstream. A tested onboarding checklist lifts activation.", f"+{BA['experiment']['lift_pts']} pts", "activation lift in A/B test", "projects.html#business-analysis"),
]
card_html = "".join(f'<a class="card" href="{h}"><span><span class="badge">{b}</span><span class="badge w">Synthetic data</span></span><h3>{t}</h3><p>{p}</p><div class="metric">{m}<small>{ml}</small></div></a>' for t, b, p, m, ml, h in cards)
mini = {f"{t:.2f}": dict(cov=r["coverage"], prec=r["precision"]) for t in [x / 100 for x in range(50, 100)] for r in [next(c for c in PM["curve"] if abs(c["t"] - t) < 1e-9)]}
hdata = json.dumps(dict(curve=mini, skills={k: dict(text=v[0], link_label=v[1], href=v[2]) for k, v in skills.items()}), separators=(",", ":"))

nodes = [("Source data", "Event and inventory records pulled from SAP and SQL.", "SAP · SQL"),
         ("Analysis", "Clean, join and test. Check the numbers before anyone sees them.", "SQL · Python · Excel"),
         ("Dashboards", "Metrics and action items in one view for the people deciding.", "Tableau · Excel"),
         ("Decisions", "Facilitate the meeting, record outcomes, escalate the risk.", "MS Teams · Confluence"),
         ("Delivery", "Hold timelines and budget under change control, track KPIs.", "Change control · KPIs")]
node_html = "".join(f'<div class="node"><b>{a}</b><small>{b}</small><em>{c}</em></div>' for a, b, c in nodes)

home = f"""{NAV()}
<main class="wrap">
<header class="hero">
  <div class="mono-badge" aria-hidden="true">NM</div>
  <div><p class="eyebrow">Operations Program Manager · Amazon</p>
  <h1>Nischal Malla</h1>
  <p class="lede">I run cross-functional programs across fulfillment operations and use SQL, Tableau and Python to turn operational data into decisions. Open to operations, analyst, AI and product roles.</p></div>
</header>
<div class="stats"><div class="stat"><b>$3.5M+</b><span>program budget managed under change control</span></div><div class="stat"><b>5</b><span>fulfillment centers coordinated</span></div><div class="stat"><b>5</b><span>case studies: 4 analytics, 1 product</span></div></div>
<div class="cta"><a class="btn primary" href="#work">View work</a><a class="btn" href="pm.html">Product case study</a><a class="btn" href="{C.LINKEDIN}" rel="noopener">LinkedIn</a><a class="btn" href="#contact">Contact</a></div>

<div class="flow"><h2>How I turn operations data into decisions</h2><div class="nodes">{node_html}</div>
<p class="cap">One workflow, the tools I use in it every week. Each case study below runs the same loop on synthetic data.</p></div>

<section class="sec" id="work"><div class="sh"><span class="n">01</span><h2>Selected work</h2></div>
<div class="feat">
  <div><span class="badge">Product case study</span><span class="badge w">Synthetic data</span>
  <h3>Exception Copilot: how much should an AI feature do on its own?</h3>
  <p>A product requirements case for an AI triage assistant in fulfillment exceptions. The data says auto-resolving is only safe for {pc(LA['coverage'], 0)} of tickets at a 97% precision floor, while suggestions help agents on most tickets. So the plan ships assist mode first.</p>
  <p><strong>Result:</strong> about {AS['hours_pw']:.0f} agent-hours a week saved in assist mode, plus {LA['hours_saved_pw']:.0f} from gated auto-resolve.</p>
  <div class="cta"><a class="btn primary" href="pm.html">Read the case</a><a class="btn" href="pm.html#simulator">Open the simulator</a></div>
  <div class="pills"><span class="pill">PRD</span><span class="pill">RICE</span><span class="pill">Threshold model</span><span class="pill">Experiment design</span><span class="pill">Python</span></div></div>
  <div class="demo" aria-label="Mini simulator"><span class="lab">Try it: confidence threshold</span>
    <div style="display:flex;justify-content:space-between;margin-top:6px"><label for="m-t">Auto-resolve above</label><strong id="m-tv"></strong></div>
    <input type="range" id="m-t" min="50" max="99" value="{int(round(LA['t'] * 100))}">
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:10px"><div><div class="big" id="m-cov"></div><span class="note">of tickets auto-resolved</span></div><div><div class="big" id="m-prec"></div><span class="note">of those correct</span></div></div>
    <p id="m-flag" style="margin:10px 0 0;font-weight:600"></p></div>
</div>
<div class="grid2" style="margin-top:16px;grid-template-columns:repeat(auto-fit,minmax(260px,1fr))">{card_html}
<a class="card" href="https://study-sync-incredible-flow.base44.app/" rel="noopener"><span><span class="badge">App</span><span class="badge w">In development</span></span><h3>StudySync</h3><p>A web app I'm building on Base44. Open the live preview.</p><div class="metric">Live<small>base44.app ↗</small></div></a></div>
<p class="note" style="margin-top:12px"><a href="projects.html">See all four analytics case studies with interactive charts →</a></p></section>

<section class="sec" id="what"><div class="sh"><span class="n">02</span><h2>What I work on</h2></div><div class="grid3 services">{svc}</div></section>

<section class="sec" id="experience"><div class="sh"><span class="n">03</span><h2>Experience</h2></div>
<div class="timeline">
<div class="job"><h3>Operations Program Manager, Amazon</h3><div class="when">May 2024 to present</div><ul>
<li>Coordinate cross-functional events at five regional fulfillment centers with SAP and MS Teams, using lean methods to cut coordination effort by 20%.</li>
<li>Manage timelines, vendors and a $3.5M+ budget under change control, on time and within corporate standards.</li>
<li>Build Excel and Tableau dashboards that track operational metrics and action items for tiered decision-making.</li>
<li>Analyze SQL event data into client-ready reports, escalate risks and recommend process changes for future programs.</li></ul></div>
<div class="job"><h3>Business Consultant, Keller Williams Realty</h3><div class="when">Dec 2021 to Jan 2024</div><ul>
<li>Directed event coordination and technology integration across seven offices for 200+ stakeholders.</li>
<li>Built Power BI and Excel dashboards to log actions, track ROI and escalate risks, reducing manual reporting by 20%.</li>
<li>Delivered projects ahead of schedule and under budget, lifting attendee satisfaction by 25%.</li></ul></div>
<div class="job"><h3>Education</h3><div class="when">&nbsp;</div><ul>
<li>MS, Information Technology, Illinois Institute of Technology (expected May 2027)</li>
<li>MBA, Project Management, Louisiana State University Shreveport (Oct 2025)</li>
<li>BS, Business Administration, California State University, Chico</li></ul></div>
<div class="job"><h3>Certifications and programs</h3><div class="when">&nbsp;</div><ul>
<li>AWS Certified Solutions Architect, Professional (2024)</li><li>CAPM, Project Management Institute (2024)</li><li>Certified Sustainability Analyst, Arizona State University (2024)</li><li>OSHA 30, State of California (2025)</li><li>PwC Management Consulting Program (May 2024)</li></ul></div>
</div></section>

<section class="sec" id="skills"><div class="sh"><span class="n">04</span><h2>Skills and tooling</h2></div>
<p class="lead">Tap a skill to see where I have used it.</p><div class="cols3">{cols}</div>
<div class="case" aria-live="polite"><h3 id="case-t"></h3><p id="case-p"></p><a id="case-l" href="#">Case study</a></div></section>

<section class="sec about" id="contact"><div class="sh"><span class="n">05</span><h2>About and contact</h2></div>
<p>I'm an operations program manager at Amazon. I coordinate programs across five fulfillment centers, manage a $3.5M+ budget under change control, and build the dashboards that decisions run on.</p>
<p>Before that I was a business consultant at Keller Williams Realty, running events and technology across seven offices. I'm finishing an MS in Information Technology at Illinois Tech (May 2027) after an MBA in project management.</p>
<p>I'm looking for operations, analyst, AI and product roles where program delivery and data work together.</p>
<div class="contact"><code id="email-text">{C.EMAIL}</code><button type="button" id="copy-email" class="btn small">Copy email</button><a class="btn small" href="{C.LINKEDIN}" rel="noopener">LinkedIn</a></div></section>
</main>{FOOT}
<script id="hdata" type="application/json">{hdata}</script>
<script>{open(f'{HERE}/page_home.js').read()}{C.THEME_JS}{C.COPY_JS}</script>"""
open(f"{OUT}/index.frag.html", "w").write(C.fragment("Nischal Malla", "Operations program manager open to operations, analyst, AI and product roles: case studies in supply chain, fleet economics, finance, and an AI product spec.", home))

# ------------------------------------------------------------------ PM CASE
grid = {}
import pandas as pd
df = pd.read_csv(f"{HERE}/pm/data/tickets.csv")
for t in [x / 100 for x in range(50, 100)]:
    d = df[df.confidence >= t]; row = {}
    for c, g in d.groupby("category"):
        row[c] = dict(n=int(len(g)), ok=int(g.ai_correct.sum()), saved_min=float(g[g.ai_correct == 1].manual_minutes.sum()))
    grid[f"{t:.2f}"] = row
pmdata = dict(assump=ASM, total=BL["tickets"], grid=grid, launch=dict(t=LA["t"]), cat=PM["by_category"],
              rice=PM["rice"])
rice_rows = "".join(f'<tr><td>{f["name"]}</td><td><input class="rc" id="rc-r{i}" type="number" min="0" value="{f["reach"]}" aria-label="Reach, tickets per week"></td>'
                    f'<td><input class="rc" id="rc-i{i}" type="number" min="0.25" step="0.25" value="{f["impact"]}" aria-label="Impact"></td>'
                    f'<td><input class="rc" id="rc-c{i}" type="number" min="10" max="100" step="5" value="{round(f["confidence"] * 100)}" aria-label="Confidence percent"></td>'
                    f'<td><input class="rc" id="rc-e{i}" type="number" min="0.5" step="0.5" value="{f["effort"]}" aria-label="Effort in person-months"></td></tr>' for i, f in enumerate(PM["rice"]))
cat_rows = "".join(f'<tr><td>{c["category"]}</td><td class="n">{c["share"] * 100:.0f}%</td><td class="n">{c["mean_min"]:.0f} min</td><td class="n">{c["accuracy"] * 100:.0f}%</td><td class="n">{(next(p for p in PM["per_cat_launch"] if p["category"] == c["category"])["coverage"]) * 100:.0f}%</td></tr>' for c in PM["by_category"])
ex = PM["experiment"]
best = PM["best"]
pm_body = f"""{NAV()}
<main class="wrap">
<div class="page-h"><a class="crumb" href="index.html">← Nischal Malla</a><p class="eyebrow" style="margin-top:18px">Product case study</p>
<h1>Exception Copilot: how much should an AI feature do on its own?</h1>
<p class="lede">A requirements case for an AI triage assistant in a fulfillment network. The question is not whether the model works, but which actions it is safe to take without a person.</p>
<p class="meta">Fictional network. Synthetic data: {BL['tickets']:,} exception tickets, 13 weeks, 5 sites. Cost and time assumptions are mine and shown on the page.</p></div>

<div class="tldr"><h2>Recommendation</h2>
<p><strong>Ship in two steps.</strong> First, an assist mode that shows the suggested resolution on every non-hazmat ticket. Then gated auto-resolve at confidence {LA['t']:.2f}, which holds precision at {pc(LA['precision'])} and takes {pc(LA['coverage'], 0)} of tickets.</p>
<ul><li>Assist mode saves about <strong>{AS['hours_pw']:.0f} agent-hours a week</strong> ({pc(AS['hours_pw'] / BL['hours_per_week'], 0)} of the {BL['hours_per_week']:.0f} hours spent on exceptions).</li>
<li>Gated auto-resolve adds about <strong>{LA['hours_saved_pw']:.0f} hours</strong> and {usd(LA['net_usd_pw'])} a week after rework and escalation costs.</li>
<li>The value-maximizing threshold ({best['t']:.2f}) auto-resolves {pc(best['coverage'], 0)} of tickets but at only {pc(best['precision'])} precision, which fails the quality floor. The right threshold is a product decision, not a modeling one.</li>
<li>Hazmat and compliance tickets never auto-resolve: the model is right on only {pc(next(c for c in PM['by_category'] if c['category'] == 'Hazmat or compliance')['accuracy'], 0)} of them.</li></ul></div>

<h2 class="s">Problem and users</h2>
<p class="lead">Fulfillment exceptions (quantity mismatches, label errors, damage, location conflicts, vendor paperwork, hazmat) are triaged by hand. The network handles about {BL['per_week']:,.0f} a week and agents spend about {BL['hours_per_week']:.0f} hours a week on them, {BL['mean_min']:.0f} minutes per ticket on average.</p>
<div class="grid2" style="grid-template-columns:repeat(auto-fit,minmax(260px,1fr))"><div class="card"><h3>Exception agents</h3><p>Need the likely resolution and the evidence in one view, and a fast way to reject a bad suggestion.</p></div>
<div class="card"><h3>Site operations managers</h3><p>Need backlog, time-to-resolution and the root causes by site and vendor, not individual tickets.</p></div></div>

<h2 class="s">Goals, non-goals and metrics</h2>
<div class="tw"><table><thead><tr><th>Metric</th><th>Role</th><th>Target</th></tr></thead><tbody>
<tr><td>Median time to resolution</td><td>North star</td><td>Down {pc(AS['hours_pw'] / BL['hours_per_week'], 0)} or more in assist mode</td></tr>
<tr><td>Precision of auto-resolved tickets</td><td>Guardrail</td><td>At least 97%, measured weekly by site</td></tr>
<tr><td>Hazmat and compliance auto-resolved</td><td>Guardrail</td><td>Zero</td></tr>
<tr><td>Suggestion acceptance rate</td><td>Input</td><td>At least 60% within 8 weeks</td></tr>
<tr><td>Reopened tickets after auto-resolve</td><td>Guardrail</td><td>Under 3%</td></tr></tbody></table></div>
<p class="note" style="margin-top:10px"><strong>Non-goals for v1:</strong> replacing agents, handling hazmat, changing vendor contracts, or automating claims payments.</p>

<h2 class="s" id="simulator">Simulator: where should the auto-resolve threshold sit?</h2>
<p class="lead">The model gives each ticket a confidence score. Raising the threshold auto-resolves fewer tickets but more of them are right. Wrong auto-resolves cost rework and escalations, so the best number depends on what an error costs. Change the inputs and watch the trade-off.</p>
<div class="panel">
<div class="ctl"><label for="s-t">Confidence threshold</label><input id="s-t" type="range" min="50" max="99" value="{int(round(LA['t'] * 100))}"><output id="o-t"></output></div>
<div class="ctl"><label for="s-rw">Rework per wrong auto-resolve</label><input id="s-rw" type="range" min="10" max="120" step="5" value="{int(ASM['rework_min'])}"><output id="o-rw"></output></div>
<div class="ctl"><label for="s-lb">Loaded labor cost per hour</label><input id="s-lb" type="range" min="20" max="60" step="1" value="{int(ASM['labor'])}"><output id="o-lb"></output></div>
<div class="ctl"><span>Hazmat guardrail</span><div class="seg" id="g-seg" role="group" aria-label="Hazmat guardrail"><button type="button" data-g="on" aria-pressed="true">Exclude hazmat</button><button type="button" data-g="off" aria-pressed="false">Include hazmat</button></div></div>
<div class="read" aria-live="polite"><div><b id="r-cov"></b><span>of tickets auto-resolved</span></div><div><b id="r-prec"></b><span>precision</span></div><div><b id="r-wrong"></b><span>wrong per week</span></div><div><b id="r-hours"></b><span>net hours saved per week</span></div></div>
<p id="r-msg" class="note" style="min-height:3em"></p>
<div class="cv tall"><canvas id="c-curve" role="img" aria-label="Line chart of precision and share auto-resolved against confidence threshold"></canvas></div>
<p class="note">Net value this week at this threshold: <strong id="r-usd"></strong> after rework and a ${ASM['escalation']:.0f} escalation cost per error.</p>
<div class="cv"><canvas id="c-net" role="img" aria-label="Line chart of net weekly value against confidence threshold"></canvas></div></div>

<h3 class="s">Accuracy differs by ticket type</h3>
<div class="tw"><table><thead><tr><th>Category</th><th class="n">Share of tickets</th><th class="n">Manual handling</th><th class="n">Model accuracy</th><th class="n">Auto-resolved at {LA['t']:.2f}</th></tr></thead><tbody>{cat_rows}</tbody></table></div>
<p class="note" style="margin-top:8px">Damage, vendor documentation and hazmat are harder for the model and also the most expensive to get wrong, which is why the rollout starts with label, quantity and location tickets.</p>

<h2 class="s" id="prioritization">Prioritization: what to build first</h2>
<p class="lead">Seven candidate features scored with RICE (reach in tickets per week, impact from 0.25 to 3, confidence, effort in person-months). Auto-resolve scores low because only {pc(LA['coverage'], 0)} of tickets qualify and it costs the most to build. Edit any value to see if the ranking holds.</p>
<div class="panel"><div class="tw"><table><thead><tr><th>Feature</th><th>Reach / week</th><th>Impact</th><th>Confidence %</th><th>Effort (months)</th></tr></thead><tbody>{rice_rows}</tbody></table></div>
<p class="note" style="margin-top:10px">Top priority now: <strong id="rice-top"></strong> <button type="button" id="rice-reset" class="btn small" style="margin-left:10px">Reset</button></p>
<div class="cv"><canvas id="c-rice" role="img" aria-label="Bar chart of RICE scores by feature"></canvas></div></div>

<h2 class="s">Rollout plan</h2>
<div class="phases">
<div class="phase"><span class="p">PHASE 0 · 3 weeks</span><h3>Shadow mode</h3><p>Model runs silently on all tickets at two sites. Nothing is shown to agents.</p><div class="gate">Gate: accuracy within 3 points of offline results.</div></div>
<div class="phase"><span class="p">PHASE 1 · 6 weeks</span><h3>Assist mode</h3><p>Suggested resolution and evidence shown on non-hazmat tickets. Agents accept or reject.</p><div class="gate">Gate: acceptance 60%+, no rise in reopened tickets.</div></div>
<div class="phase"><span class="p">PHASE 2 · 8 weeks</span><h3>Gated auto-resolve</h3><p>Label, quantity and location tickets above {LA['t']:.2f} resolve automatically with a 1-minute spot check.</p><div class="gate">Gate: precision 97%+ by site for 4 straight weeks.</div></div>
<div class="phase"><span class="p">PHASE 3</span><h3>Network rollout</h3><p>Expand sites and review thresholds by category every quarter.</p><div class="gate">Gate: reopen rate under 3%.</div></div></div>

<h2 class="s">Experiment plan</h2>
<p class="lead">Randomize by site-week, because agents at one site share a queue and would contaminate a ticket-level split. Primary metric: mean time to resolution. Guardrails: precision, reopened tickets, agent satisfaction. Ticket handling time has a standard deviation of {ex['sd']:.0f} minutes, so detecting a {ex['mde_min']:.0f}-minute reduction at 80% power needs about {ex['n_per_arm']:,} tickets per arm ({ex['n_per_arm'] / ex['weekly_tickets_per_site']:.1f} site-weeks); a 2-minute reduction needs {ex['n_per_arm_2']:,}. Check the split before reading results.</p>

<h2 class="s">Risks and open questions</h2>
<div class="tw"><table><thead><tr><th>Risk</th><th>Mitigation</th></tr></thead><tbody>
<tr><td>Agents over-trust suggestions (automation bias)</td><td>Show confidence and evidence; track the rate of accepted suggestions that later reopen.</td></tr>
<tr><td>Model accuracy drifts by site or vendor</td><td>Weekly precision by site; automatic fallback to assist mode below the floor.</td></tr>
<tr><td>Compliance exposure on hazmat</td><td>Hard exclusion and an audit trail on every automated action.</td></tr>
<tr><td>Value estimates are assumptions</td><td>Sliders above; replace with measured rework time in Phase 1.</td></tr></tbody></table></div>
<p class="note" style="margin-top:10px"><strong>Open questions:</strong> who owns a wrong auto-resolution, how appeals from vendors are handled, and whether site managers want different thresholds.</p>
<p class="note">Limits: synthetic tickets and a calibrated-by-construction model. The real calibration, costs and acceptance rates would come from a shadow-mode period. Nothing here uses employer data.</p>
</main>{FOOT}
<script id="pmdata" type="application/json">{json.dumps(pmdata, separators=(",", ":"))}</script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<script>{open(f'{HERE}/page_pm.js').read()}{C.THEME_JS}</script>"""
open(f"{OUT}/pm.frag.html", "w").write(C.fragment("Exception Copilot Product Case", "Product requirements case for an AI triage feature in fulfillment operations, with a live threshold simulator and RICE prioritization on synthetic data.", pm_body))
print("built", len(home) // 1024, len(pm_body) // 1024)

# ------------------------------------------------------------------ PROJECTS (existing analytics page, re-skinned navigation)
p = open(f"{HERE}/portfolio.html").read()
def rp(a, b):
    global p
    assert a in p, a
    p = p.replace(a, b, 1)
rp("<title>Nischal Malla Analytics Portfolio</title>", "<title>Nischal Malla Analytics Case Studies</title>")
rp('<span class="brand">Nischal Malla</span>', '<a class="brand" href="index.html" style="color:inherit;text-decoration:none">&larr; Nischal Malla</a>')
rp('<div class="links"><a href="#skills">', '<div class="links"><a href="pm.html">Product case</a><a href="#skills">')
rp('<p class="eyebrow">Data analyst portfolio</p>', '<p class="eyebrow">Analytics case studies</p>')
rp("<h1>Nischal Malla</h1>", "<h1>Four analytics case studies</h1>")
rp("Open to mid-level data analyst roles.", "Open to operations, analyst, AI and product roles.")
rp("nischalmalla28@gmail.com", C.EMAIL)
rp('<a href="https://www.linkedin.com/in/nischalmalla">linkedin.com/in/nischalmalla</a>', f'<a href="{C.LINKEDIN}">linkedin.com/in/nischal-malla</a>')
open(f"{OUT}/projects.frag.html", "w").write(p)
for n in ("index", "pm", "projects"):
    f = open(f"{OUT}/{n}.frag.html").read()
    open(f"{OUT}/{n}.html", "w").write(C.to_full(f))
print("pages written")
