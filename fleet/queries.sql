-- Fleet project: SQL layer (SQLite dialect).
-- vehicles(vehicle_id, type, lane, acquisition_date, acquisition_cost, residual_pct, life_months)
-- monthly_ops(vehicle_id, month, miles, revenue, fuel_cost, driver_cost, insurance, software_fee,
--             other_cost, depreciation, downtime_hours, age_months)
-- maintenance(event_id, vehicle_id, month, kind, cost, downtime_hours)   diesel(month, diesel_per_gal)
-- type is 'AI' (AI-equipped) or 'Conventional'. Operating profit = revenue - all costs including depreciation.

-- name: vehicle_months
-- One row per vehicle per month with maintenance cost joined on and operating profit computed.
-- Every other query reads from this CTE (repeated inline below).
WITH mx AS (
    SELECT vehicle_id, month, SUM(cost) AS maint_cost
    FROM maintenance GROUP BY vehicle_id, month
)
SELECT o.vehicle_id, v.type, v.lane, o.month, o.age_months, o.miles, o.revenue, o.fuel_cost, o.driver_cost,
       o.insurance, o.software_fee, o.other_cost, o.depreciation, COALESCE(mx.maint_cost, 0) AS maint_cost,
       o.downtime_hours,
       o.revenue - o.fuel_cost - o.driver_cost - o.insurance - o.software_fee - o.other_cost
                 - o.depreciation - COALESCE(mx.maint_cost, 0) AS profit
FROM monthly_ops o
JOIN vehicles v USING (vehicle_id)
LEFT JOIN mx ON mx.vehicle_id = o.vehicle_id AND mx.month = o.month;

-- name: cost_by_type_lane
-- Cost structure and profit by vehicle type and lane (totals; per-mile figures are computed in Python).
WITH mx AS (SELECT vehicle_id, month, SUM(cost) AS maint_cost FROM maintenance GROUP BY vehicle_id, month)
SELECT v.type, v.lane, COUNT(DISTINCT o.vehicle_id) AS vehicles, COUNT(*) AS vehicle_months,
       SUM(o.miles) AS miles, SUM(o.revenue) AS revenue, SUM(o.fuel_cost) AS fuel, SUM(o.driver_cost) AS driver,
       SUM(COALESCE(mx.maint_cost, 0)) AS maintenance, SUM(o.insurance) AS insurance, SUM(o.software_fee) AS software,
       SUM(o.other_cost) AS other, SUM(o.depreciation) AS depreciation, SUM(o.downtime_hours) AS downtime_hours
FROM monthly_ops o
JOIN vehicles v USING (vehicle_id)
LEFT JOIN mx ON mx.vehicle_id = o.vehicle_id AND mx.month = o.month
GROUP BY v.type, v.lane;

-- name: maintenance_by_kind
-- Events, spend and downtime by kind of maintenance and vehicle type.
SELECT v.type, m.kind, COUNT(*) AS events, SUM(m.cost) AS cost, SUM(m.downtime_hours) AS downtime_hours
FROM maintenance m JOIN vehicles v USING (vehicle_id)
GROUP BY v.type, m.kind;

-- name: miles_by_type
SELECT v.type, SUM(o.miles) AS miles, COUNT(*) AS vehicle_months
FROM monthly_ops o JOIN vehicles v USING (vehicle_id) GROUP BY v.type;

-- name: maintenance_by_age
-- Maintenance cost per mile by vehicle age bucket (age at the time of the cost).
WITH mx AS (SELECT vehicle_id, month, SUM(cost) AS maint_cost FROM maintenance GROUP BY vehicle_id, month)
SELECT v.type,
       CASE WHEN o.age_months < 12 THEN 0 WHEN o.age_months < 24 THEN 1 WHEN o.age_months < 36 THEN 2
            WHEN o.age_months < 48 THEN 3 ELSE 4 END AS bucket,
       COUNT(*) AS vehicle_months, SUM(o.miles) AS miles, SUM(COALESCE(mx.maint_cost, 0)) AS maintenance
FROM monthly_ops o JOIN vehicles v USING (vehicle_id)
LEFT JOIN mx ON mx.vehicle_id = o.vehicle_id AND mx.month = o.month
GROUP BY v.type, bucket;

-- name: vehicle_ttm
-- Trailing 12 months (Oct 2025 - Sep 2026) per vehicle: the fleet scatter and the watchlist.
WITH mx AS (SELECT vehicle_id, month, SUM(cost) AS maint_cost FROM maintenance GROUP BY vehicle_id, month)
SELECT v.vehicle_id, v.type, v.lane, v.acquisition_cost, MAX(o.age_months) AS age_months, COUNT(*) AS months,
       SUM(o.miles) AS miles, SUM(o.revenue) AS revenue,
       SUM(o.revenue - o.fuel_cost - o.driver_cost - o.insurance - o.software_fee - o.other_cost
                     - o.depreciation - COALESCE(mx.maint_cost, 0)) AS profit,
       SUM(COALESCE(mx.maint_cost, 0)) AS maintenance
FROM monthly_ops o JOIN vehicles v USING (vehicle_id)
LEFT JOIN mx ON mx.vehicle_id = o.vehicle_id AND mx.month = o.month
WHERE o.month >= '2025-10-01'
GROUP BY v.vehicle_id
HAVING COUNT(*) = 12;

-- name: monthly_profit
-- Profit per vehicle-month by calendar month and type.
WITH mx AS (SELECT vehicle_id, month, SUM(cost) AS maint_cost FROM maintenance GROUP BY vehicle_id, month)
SELECT o.month, v.type, COUNT(*) AS n,
       AVG(o.revenue - o.fuel_cost - o.driver_cost - o.insurance - o.software_fee - o.other_cost
                     - o.depreciation - COALESCE(mx.maint_cost, 0)) AS profit_per_vehicle
FROM monthly_ops o JOIN vehicles v USING (vehicle_id)
LEFT JOIN mx ON mx.vehicle_id = o.vehicle_id AND mx.month = o.month
GROUP BY o.month, v.type ORDER BY o.month, v.type;

-- name: diesel_price
SELECT month, diesel_per_gal FROM diesel ORDER BY month;
