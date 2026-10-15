-- Financial analysis project: SQL layer (SQLite dialect).
-- Tidy table pnl(month, bu, scenario['Actual'|'Budget'], units, price, unit_cost,
--                revenue, cogs, payroll, marketing, other_opex) and ar(month, bu, ar_balance).
-- EBITDA = revenue - cogs - payroll - marketing - other_opex

-- name: ytd_variance
-- 2026 YTD (Jan-Sep) actual vs budget by business unit, via conditional aggregation.
SELECT bu,
       SUM(CASE WHEN scenario='Actual' THEN revenue END)                                   AS rev_act,
       SUM(CASE WHEN scenario='Budget' THEN revenue END)                                   AS rev_bud,
       SUM(CASE WHEN scenario='Actual' THEN revenue - cogs END)                            AS gp_act,
       SUM(CASE WHEN scenario='Budget' THEN revenue - cogs END)                            AS gp_bud,
       SUM(CASE WHEN scenario='Actual' THEN revenue - cogs - payroll - marketing - other_opex END) AS ebitda_act,
       SUM(CASE WHEN scenario='Budget' THEN revenue - cogs - payroll - marketing - other_opex END) AS ebitda_bud
FROM pnl
WHERE month BETWEEN '2026-01-01' AND '2026-09-01'
GROUP BY bu
ORDER BY bu;

-- name: ebitda_bridge
-- Price / volume / cost / opex decomposition of the EBITDA variance, computed at
-- month x BU grain so the effects sum exactly to the total variance:
--   volume = (units_a - units_b) * (price_b - cost_b)
--   price  = (price_a - price_b) * units_a
--   cost   = -(cost_a - cost_b) * units_a
WITH a AS (SELECT * FROM pnl WHERE scenario = 'Actual'),
     b AS (SELECT * FROM pnl WHERE scenario = 'Budget')
SELECT a.bu,
       SUM((a.units - b.units) * (b.price - b.unit_cost))                    AS volume_effect,
       SUM((a.price - b.price) * a.units)                                    AS price_effect,
       SUM(-(a.unit_cost - b.unit_cost) * a.units)                           AS cost_effect,
       SUM(-(a.marketing - b.marketing))                                     AS marketing_effect,
       SUM(-((a.payroll + a.other_opex) - (b.payroll + b.other_opex)))       AS payroll_other_effect,
       SUM((a.revenue - a.cogs - a.payroll - a.marketing - a.other_opex)
         - (b.revenue - b.cogs - b.payroll - b.marketing - b.other_opex))    AS total_ebitda_var
FROM a JOIN b ON a.month = b.month AND a.bu = b.bu
WHERE a.month BETWEEN '2026-01-01' AND '2026-09-01'
GROUP BY a.bu
ORDER BY a.bu;

-- name: quarterly_margin
-- Gross margin by quarter and BU, actual vs budget, with a YoY change in points (LAG over 4 quarters).
WITH q AS (
    SELECT bu,
           substr(month, 1, 4) || '-Q' || ((CAST(substr(month, 6, 2) AS INTEGER) + 2) / 3) AS qtr,
           100.0 * SUM(CASE WHEN scenario='Actual' THEN revenue - cogs END)
                 / SUM(CASE WHEN scenario='Actual' THEN revenue END)  AS gm_act,
           100.0 * SUM(CASE WHEN scenario='Budget' THEN revenue - cogs END)
                 / SUM(CASE WHEN scenario='Budget' THEN revenue END)  AS gm_bud
    FROM pnl
    WHERE month <= '2026-09-01'
    GROUP BY bu, qtr
)
SELECT bu, qtr,
       ROUND(gm_act, 1) AS gm_actual_pct,
       ROUND(gm_bud, 1) AS gm_budget_pct,
       ROUND(gm_act - LAG(gm_act, 4) OVER (PARTITION BY bu ORDER BY qtr), 1) AS yoy_pts
FROM q
ORDER BY bu, qtr;

-- name: monthly_company
-- Company-level monthly actual vs budget, with YoY revenue growth (LAG 12 months).
WITH m AS (
    SELECT month,
           SUM(CASE WHEN scenario='Actual' THEN revenue END) AS rev_act,
           SUM(CASE WHEN scenario='Budget' THEN revenue END) AS rev_bud,
           SUM(CASE WHEN scenario='Actual' THEN revenue - cogs - payroll - marketing - other_opex END) AS ebitda_act,
           SUM(CASE WHEN scenario='Budget' THEN revenue - cogs - payroll - marketing - other_opex END) AS ebitda_bud
    FROM pnl
    GROUP BY month
)
SELECT month, ROUND(rev_act) AS rev_act, ROUND(rev_bud) AS rev_bud,
       ROUND(ebitda_act) AS ebitda_act, ROUND(ebitda_bud) AS ebitda_bud,
       ROUND(100.0 * (rev_act / LAG(rev_act, 12) OVER (ORDER BY month) - 1), 1) AS rev_yoy_pct
FROM m
WHERE rev_act IS NOT NULL
ORDER BY month;

-- name: dso
-- Days sales outstanding by BU (AR balance / monthly revenue x 30) + 3-month moving average.
WITH d AS (
    SELECT a.bu, a.month, a.ar_balance / p.revenue * 30.0 AS dso
    FROM ar a
    JOIN pnl p ON p.month = a.month AND p.bu = a.bu AND p.scenario = 'Actual'
)
SELECT bu, month, dso AS dso_raw, ROUND(dso, 1) AS dso,
       ROUND(AVG(dso) OVER (PARTITION BY bu ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 1) AS dso_3mo
FROM d
ORDER BY bu, month;

-- name: bu_monthly_actuals
-- Monthly actual revenue and cost lines per BU: input to the forecasting model.
SELECT month, bu, revenue, cogs, payroll, marketing, other_opex
FROM pnl
WHERE scenario = 'Actual'
ORDER BY bu, month;
