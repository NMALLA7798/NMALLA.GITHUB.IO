-- Supply chain project: SQL layer (SQLite dialect; runs unchanged on Postgres with minor date-function swaps)
-- Each query is tagged "-- name: <id>" so 02_analyze.py can load and run it.

-- name: kpis
-- Headline procurement KPIs for the whole period.
SELECT
    COUNT(*)                                                         AS purchase_orders,
    ROUND(SUM(total_cost))                                           AS total_spend,
    ROUND(100.0 * AVG(received_date <= promised_date), 1)            AS on_time_pct,
    ROUND(100.0 * AVG(qty_received >= 0.98 * qty_ordered), 1)        AS in_full_pct,
    ROUND(100.0 * AVG(received_date <= promised_date
                      AND qty_received >= 0.98 * qty_ordered), 1)    AS otif_pct,
    ROUND(AVG(julianday(received_date) - julianday(promised_date)), 2) AS avg_delay_days,
    ROUND(SUM(CASE WHEN expedited = 1
                   THEN total_cost - unit_cost * qty_received END)) AS expedite_premium_paid
FROM purchase_orders;

-- name: supplier_scorecard
-- Supplier ranking: OTIF, delay, spend share. CTEs + window functions.
WITH po AS (
    SELECT p.*, s.supplier_name, s.country,
           julianday(received_date) - julianday(promised_date)  AS delay_days,
           julianday(received_date) - julianday(order_date)     AS actual_lead_days,
           CASE WHEN received_date <= promised_date THEN 1 ELSE 0 END      AS on_time,
           CASE WHEN qty_received >= 0.98 * qty_ordered THEN 1 ELSE 0 END  AS in_full
    FROM purchase_orders p
    JOIN suppliers s USING (supplier_id)
),
agg AS (
    SELECT supplier_id, supplier_name, country,
           COUNT(*)                                  AS pos,
           ROUND(SUM(total_cost))                    AS spend,
           ROUND(100.0 * AVG(on_time), 1)            AS on_time_pct,
           ROUND(100.0 * AVG(in_full), 1)            AS in_full_pct,
           ROUND(100.0 * AVG(on_time * in_full), 1)  AS otif_pct,
           ROUND(AVG(delay_days), 2)                 AS avg_delay_days,
           ROUND(AVG(actual_lead_days), 1)           AS avg_lead_days,
           SUM(expedited)                            AS expedited_pos
    FROM po
    GROUP BY supplier_id, supplier_name, country
)
SELECT *,
       RANK() OVER (ORDER BY otif_pct DESC)                      AS otif_rank,
       ROUND(100.0 * spend / SUM(spend) OVER (), 1)              AS spend_share_pct
FROM agg
ORDER BY otif_pct ASC;

-- name: monthly_otif
-- Monthly OTIF with a 3-month moving average (window frame).
WITH m AS (
    SELECT substr(received_date, 1, 7) AS month,
           COUNT(*) AS pos,
           ROUND(100.0 * AVG(received_date <= promised_date
                             AND qty_received >= 0.98 * qty_ordered), 1) AS otif_pct
    FROM purchase_orders
    GROUP BY 1
    HAVING COUNT(*) >= 50   -- drop ramp-up months with too few POs to be meaningful
)
SELECT month, pos, otif_pct,
       ROUND(AVG(otif_pct) OVER (ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 1) AS otif_3mo_avg
FROM m
ORDER BY month;

-- name: country_summary
SELECT s.country,
       COUNT(*)                                                       AS pos,
       ROUND(SUM(p.total_cost))                                       AS spend,
       ROUND(100.0 * AVG(p.received_date <= p.promised_date
                         AND p.qty_received >= 0.98 * p.qty_ordered), 1) AS otif_pct,
       ROUND(AVG(julianday(p.received_date) - julianday(p.promised_date)), 2) AS avg_delay_days
FROM purchase_orders p JOIN suppliers s USING (supplier_id)
GROUP BY s.country
ORDER BY otif_pct;

-- name: abc_classification
-- ABC / Pareto on 2025 demand value. Class A = SKUs making up the first 80% of value.
WITH s AS (
    SELECT d.sku, p.category, p.supplier_id,
           SUM(d.units * p.unit_cost) AS value
    FROM weekly_demand d JOIN products p USING (sku)
    WHERE d.week_start >= '2025-01-01'
    GROUP BY d.sku, p.category, p.supplier_id
),
r AS (
    SELECT *,
           SUM(value) OVER (ORDER BY value DESC) / SUM(value) OVER ()  AS cum_share,
           value / SUM(value) OVER ()                                   AS own_share,
           ROW_NUMBER() OVER (ORDER BY value DESC)                      AS rnk
    FROM s
)
SELECT sku, category, supplier_id, ROUND(value) AS value, rnk,
       ROUND(100.0 * cum_share, 1) AS cum_pct,
       CASE WHEN cum_share - own_share < 0.80 THEN 'A'
            WHEN cum_share - own_share < 0.95 THEN 'B'
            ELSE 'C' END AS abc_class
FROM r
ORDER BY rnk;

-- name: lead_time_by_supplier
-- Raw lead times per PO; the Python layer computes variability (SQLite has no STDDEV).
SELECT supplier_id,
       julianday(received_date) - julianday(order_date) AS actual_lead_days
FROM purchase_orders;
