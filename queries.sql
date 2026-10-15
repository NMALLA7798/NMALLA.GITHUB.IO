-- Business analysis project: SQL layer (SQLite dialect).
-- customers(customer_id, signup_date, channel, plan, activated_7d, tickets_30d, converted,
--           paid_start_date, cancel_date, exp_variant, monthly_price)  channel_costs(channel, cost_per_signup)
-- Data runs to 2025-12-31. cancel_date IS NULL means still subscribed (or never paid).
-- "Retained at 3 months" = no cancellation within 3 months of the first payment.

-- name: overall_kpis
-- Current-state KPIs on recent signups (Jan-Aug 2025; all have 3+ months of follow-up).
SELECT COUNT(*)                                                    AS signups,
       ROUND(100.0 * AVG(activated_7d), 1)                         AS activation_pct,
       ROUND(100.0 * AVG(converted), 1)                            AS conversion_pct,
       ROUND(100.0 * SUM(CASE WHEN converted = 1 AND (cancel_date IS NULL
                  OR cancel_date > date(paid_start_date, '+3 months')) THEN 1 ELSE 0 END)
             / SUM(converted), 1)                                  AS retained_90d_pct,
       ROUND(AVG(CASE WHEN converted = 1 THEN monthly_price END), 2) AS arpu
FROM customers
WHERE signup_date BETWEEN '2025-01-01' AND '2025-08-31';

-- name: funnel_by_channel
-- Signup -> activated -> paying -> still paying after 90 days, by acquisition channel.
SELECT channel,
       COUNT(*)           AS signups,
       SUM(activated_7d)  AS activated,
       SUM(converted)     AS paid,
       SUM(CASE WHEN converted = 1 AND (cancel_date IS NULL
                OR cancel_date > date(paid_start_date, '+3 months')) THEN 1 ELSE 0 END) AS retained_90d
FROM customers
WHERE signup_date BETWEEN '2025-01-01' AND '2025-08-31'
GROUP BY channel;

-- name: cohort_retention
-- Retention by paid-start cohort and months since first payment. A recursive CTE builds the month
-- offsets; a cell is kept only when the whole cohort has been observed that long.
WITH RECURSIVE months(m) AS (
    SELECT 0 UNION ALL SELECT m + 1 FROM months WHERE m < 12
),
paying AS (
    SELECT customer_id, strftime('%Y-%m', paid_start_date) AS cohort, paid_start_date, cancel_date
    FROM customers WHERE converted = 1
)
SELECT p.cohort, m.m AS months_since,
       COUNT(*) AS cohort_size,
       SUM(CASE WHEN p.cancel_date IS NULL
                  OR p.cancel_date > date(p.paid_start_date, '+' || m.m || ' months') THEN 1 ELSE 0 END) AS active
FROM paying p
JOIN months m
WHERE date(p.cohort || '-01', '+1 month', '-1 day', '+' || m.m || ' months') <= '2025-12-31'
GROUP BY p.cohort, m.m
ORDER BY p.cohort, m.m;

-- name: churn_by_segment
-- 6-month churn among paying customers (first payment on or before 2025-06-30), cut four ways.
WITH p AS (
    SELECT *, CASE WHEN cancel_date IS NOT NULL
                    AND cancel_date <= date(paid_start_date, '+6 months') THEN 1 ELSE 0 END AS churn6
    FROM customers
    WHERE converted = 1 AND paid_start_date <= '2025-06-30'
)
SELECT 'Channel' AS dimension, channel AS segment, COUNT(*) AS customers, ROUND(100.0 * AVG(churn6), 1) AS churn6_pct
FROM p GROUP BY channel
UNION ALL
SELECT 'Plan', plan, COUNT(*), ROUND(100.0 * AVG(churn6), 1) FROM p GROUP BY plan
UNION ALL
SELECT '7-day activation', CASE WHEN activated_7d = 1 THEN 'Activated' ELSE 'Not activated' END,
       COUNT(*), ROUND(100.0 * AVG(churn6), 1) FROM p GROUP BY 2
UNION ALL
SELECT 'Support tickets in first 30 days',
       CASE WHEN tickets_30d = 0 THEN '0 tickets' WHEN tickets_30d = 1 THEN '1 ticket' ELSE '2 or more' END,
       COUNT(*), ROUND(100.0 * AVG(churn6), 1) FROM p GROUP BY 2;

-- name: unit_economics
-- Revenue in the first 6 months vs acquisition spend, by channel (signups Jul 2024 - Jun 2025).
WITH RECURSIVE months(m) AS (
    SELECT 0 UNION ALL SELECT m + 1 FROM months WHERE m < 5
),
rev AS (
    SELECT c.customer_id,
           SUM(CASE WHEN c.cancel_date IS NULL
                      OR c.cancel_date > date(c.paid_start_date, '+' || m.m || ' months')
                    THEN c.monthly_price ELSE 0 END) AS rev6
    FROM customers c JOIN months m
    WHERE c.converted = 1
    GROUP BY c.customer_id
)
SELECT s.channel,
       COUNT(*)                                   AS signups,
       SUM(s.converted)                           AS paid,
       ROUND(COALESCE(SUM(r.rev6), 0))            AS revenue6,
       ROUND(COUNT(*) * cc.cost_per_signup)       AS spend,
       ROUND(COALESCE(SUM(r.rev6), 0) / COUNT(*), 2)                       AS revenue6_per_signup,
       ROUND(COALESCE(SUM(r.rev6), 0) / (COUNT(*) * cc.cost_per_signup), 2) AS return_per_dollar
FROM customers s
LEFT JOIN rev r USING (customer_id)
JOIN channel_costs cc USING (channel)
WHERE s.signup_date BETWEEN '2024-07-01' AND '2025-06-30'
GROUP BY s.channel
ORDER BY return_per_dollar;

-- name: value_by_activation
-- Conversion and 6-month revenue per paying customer, activated vs not (same signup window).
WITH RECURSIVE months(m) AS (
    SELECT 0 UNION ALL SELECT m + 1 FROM months WHERE m < 5
),
rev AS (
    SELECT c.customer_id,
           SUM(CASE WHEN c.cancel_date IS NULL
                      OR c.cancel_date > date(c.paid_start_date, '+' || m.m || ' months')
                    THEN c.monthly_price ELSE 0 END) AS rev6
    FROM customers c JOIN months m
    WHERE c.converted = 1
    GROUP BY c.customer_id
)
SELECT s.activated_7d, COUNT(*) AS signups, SUM(s.converted) AS paid, COALESCE(SUM(r.rev6), 0) AS revenue6
FROM customers s LEFT JOIN rev r USING (customer_id)
WHERE s.signup_date BETWEEN '2024-07-01' AND '2025-06-30'
GROUP BY s.activated_7d;

-- name: conversion_by_channel_period
-- Signup-to-paid conversion by channel for two signup windows: A = H1 2024, B = H1 2025.
SELECT CASE WHEN signup_date BETWEEN '2024-01-01' AND '2024-06-30' THEN 'A' ELSE 'B' END AS period,
       channel,
       COUNT(*)       AS signups,
       SUM(converted) AS paid
FROM customers
WHERE signup_date BETWEEN '2024-01-01' AND '2024-06-30' OR signup_date BETWEEN '2025-01-01' AND '2025-06-30'
GROUP BY period, channel;

-- name: monthly_trend
SELECT substr(signup_date, 1, 7) AS month,
       COUNT(*) AS signups,
       ROUND(100.0 * AVG(channel = 'Paid social'), 1) AS paid_social_share_pct,
       ROUND(100.0 * AVG(activated_7d), 1)            AS activation_pct
FROM customers
GROUP BY 1
ORDER BY 1;

-- name: experiment
-- Onboarding checklist A/B test (signups 2025-07-01 to 2025-09-30, randomised 50/50).
SELECT exp_variant AS variant, COUNT(*) AS n, SUM(activated_7d) AS activated, SUM(converted) AS paid,
       ROUND(AVG(tickets_30d), 3) AS avg_tickets
FROM customers
WHERE exp_variant IS NOT NULL
GROUP BY exp_variant;

-- name: experiment_balance
-- Randomisation check: channel mix should match across variants.
SELECT exp_variant AS variant, channel, COUNT(*) AS n
FROM customers
WHERE exp_variant IS NOT NULL
GROUP BY exp_variant, channel;

-- name: base_volumes
-- 2025 run-rate volumes used to size the business case.
SELECT channel, COUNT(*) AS signups_2025,
       SUM(CASE WHEN converted = 1 AND tickets_30d >= 2 THEN 1 ELSE 0 END) AS paying_hi_tickets,
       ROUND(AVG(CASE WHEN converted = 1 THEN monthly_price END), 2) AS arpu
FROM customers
WHERE signup_date BETWEEN '2025-01-01' AND '2025-12-31'
GROUP BY channel;

-- name: churned_2025
SELECT COUNT(*) AS churned_2025
FROM customers
WHERE cancel_date BETWEEN '2025-01-01' AND '2025-12-31';
