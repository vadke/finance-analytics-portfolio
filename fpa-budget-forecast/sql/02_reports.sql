-- name: ytd_2026
-- Year-to-date (Jan-Sep 2026) budget vs. actual by P&L line
SELECT line_item, SUM(budget) AS budget, SUM(actual) AS actual, SUM(variance) AS variance,
       ROUND(100.0 * SUM(variance) / ABS(SUM(budget)), 2) AS variance_pct
FROM bva_monthly
WHERE fiscal_year = '2026' AND actual IS NOT NULL
GROUP BY line_item;

-- name: region_channel_ytd
-- Revenue variance by region and channel, YTD 2026, ranked worst first
WITH x AS (
  SELECT region, channel,
         SUM(CASE WHEN scenario = 'Budget' THEN amount_usd END) AS budget,
         SUM(CASE WHEN scenario = 'Actual' THEN amount_usd END) AS actual
  FROM pl_monthly
  WHERE line_type = 'Revenue' AND month BETWEEN '2026-01' AND '2026-09'
  GROUP BY region, channel)
SELECT region, channel, budget, actual, actual - budget AS variance,
       ROUND(100.0 * (actual - budget) / budget, 2) AS variance_pct,
       RANK() OVER (ORDER BY (actual - budget) * 1.0 / budget) AS rank_worst_first
FROM x;

-- name: region_channel_yoy
-- Same-period revenue growth by region and channel, Jan-Sep 2026 vs Jan-Sep 2025
WITH x AS (
  SELECT region, channel,
         SUM(CASE WHEN month BETWEEN '2026-01' AND '2026-09' THEN amount_usd END) AS cy,
         SUM(CASE WHEN month BETWEEN '2025-01' AND '2025-09' THEN amount_usd END) AS py
  FROM pl_monthly WHERE scenario = 'Actual' AND line_type = 'Revenue'
  GROUP BY region, channel)
SELECT region, channel, cy, py, ROUND(100.0 * (cy - py) / py, 2) AS yoy_pct FROM x;
