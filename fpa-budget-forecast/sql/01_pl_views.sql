-- Amounts are signed: revenue positive, costs negative.
-- So variance = actual - budget is favorable when positive, for every line.
DROP VIEW IF EXISTS pl_lines;
CREATE VIEW pl_lines AS
SELECT month, substr(month, 1, 4) AS fiscal_year, scenario, line_type, line_item, region, channel, amount_usd
FROM pl_monthly
UNION ALL
SELECT month, substr(month, 1, 4), scenario, 'Subtotal', 'Gross Profit', 'All', 'All', SUM(amount_usd)
FROM pl_monthly WHERE line_type IN ('Revenue', 'COGS') GROUP BY month, scenario
UNION ALL
SELECT month, substr(month, 1, 4), scenario, 'Subtotal', 'Operating Income', 'All', 'All', SUM(amount_usd)
FROM pl_monthly GROUP BY month, scenario;

DROP VIEW IF EXISTS bva_monthly;
CREATE VIEW bva_monthly AS
WITH b AS (SELECT month, fiscal_year, line_item, SUM(amount_usd) AS budget
           FROM pl_lines WHERE scenario = 'Budget' GROUP BY month, line_item),
     a AS (SELECT month, line_item, SUM(amount_usd) AS actual
           FROM pl_lines WHERE scenario = 'Actual' GROUP BY month, line_item)
SELECT b.month, b.fiscal_year, b.line_item, b.budget, a.actual,
       a.actual - b.budget AS variance,
       ROUND(100.0 * (a.actual - b.budget) / ABS(b.budget), 2) AS variance_pct,
       CASE WHEN a.actual IS NULL THEN NULL
            WHEN a.actual >= b.budget THEN 'Favorable' ELSE 'Unfavorable' END AS flag
FROM b LEFT JOIN a USING (month, line_item);
