# Nischal Malla: Data Analytics Portfolio

Three end-to-end analytics projects, each built from raw tables to a written recommendation.
The portfolio page is `index.html` (served by GitHub Pages). All datasets are synthetic, generated with
realistic structure, so everything here is reproducible.

| Project | Question | Methods |
|---|---|---|
| `supply_chain/` | Where do late and short deliveries come from, and what would it cost to stop them hurting service? | SQL scorecards (CTEs, windows), ABC analysis, Monte Carlo reorder-policy test, rolling-origin forecast backtest |
| `finance/` | Revenue is on budget but EBITDA is short. Why, and where is the year heading? | SQL conditional aggregation and LAG, price/volume/cost/opex EBITDA bridge, DSO, revenue forecast with bootstrap intervals, scenarios and sensitivity |
| `business_analysis/` | Retention looks weak and paid social keeps growing. Where should a subscription app invest next quarter? | KPI dictionary, hypotheses, recursive-CTE cohort retention, funnel by channel, mix-shift decomposition, A/B test with split check and confidence intervals, prioritized business case |

## Run it

```bash
pip install pandas numpy scikit-learn
for p in supply_chain finance business_analysis; do (cd $p && python 01_generate_data.py && python 02_analyze.py); done
python build_portfolio.py   # rebuilds index.html from the three results.json files
```

Each project folder contains:

- `01_generate_data.py` builds the dataset and a SQLite database (seeded, reproducible)
- `queries.sql` holds the SQL layer, one tagged query per metric
- `02_analyze.py` runs the SQL, the Python analysis and the tests, then writes `results.json`

`build_portfolio.py`, `ba_content.py` and `page.js` turn the results into the interactive page. Every number on the
page is formatted from a `results.json` file, so the page cannot drift from the analysis.

## Checks built in

- The EBITDA bridge components are asserted to sum exactly to the budget-vs-actual variance.
- The scenario base case is asserted to equal the forecast EBITDA.
- The retention change is decomposed into mix and rate effects, and the parts are asserted to sum to the total.
- Forecasts are scored against a naive baseline on rolling holdout windows, not on the training data.
- The A/B test reports a split check, confidence intervals and the smallest effect it could detect.

## Limits

Synthetic data shows the method, not real-world performance. Each project section on the page lists its own modelling assumptions.
