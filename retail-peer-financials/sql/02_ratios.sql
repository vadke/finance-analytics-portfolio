-- Peer ratio model. Fiscal years are aligned to the calendar year in which
-- most of the fiscal period falls (Jan/Feb year-ends roll back one year).
DROP VIEW IF EXISTS ratios;
CREATE VIEW ratios AS
WITH base AS (
    SELECT i.ticker, i.company, i.fiscal_year_end,
           CASE WHEN CAST(strftime('%m', i.fiscal_year_end) AS INT) <= 2
                THEN CAST(strftime('%Y', i.fiscal_year_end) AS INT) - 1
                ELSE CAST(strftime('%Y', i.fiscal_year_end) AS INT) END AS fiscal_year,
           i.revenue, i.gross_profit, i.revenue - i.gross_profit AS cogs,
           i.operating_income, i.net_income, i.eps,
           b.inventory, b.total_current_assets, b.total_assets,
           b.total_current_liabilities, b.total_debt, b.shareholders_equity,
           c.operating_cash_flow, -c.capital_expenditures AS capex, c.free_cash_flow
    FROM income_statement i
    JOIN balance_sheet b USING (ticker, fiscal_year_end)
    JOIN cash_flow c USING (ticker, fiscal_year_end)
),
lagged AS (
    SELECT *,
           LAG(revenue)      OVER w AS prev_revenue,
           LAG(inventory)    OVER w AS prev_inventory,
           LAG(total_assets) OVER w AS prev_assets,
           FIRST_VALUE(revenue) OVER (PARTITION BY ticker ORDER BY fiscal_year
                ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS first_revenue,
           MIN(fiscal_year) OVER (PARTITION BY ticker) AS first_year
    FROM base
    WINDOW w AS (PARTITION BY ticker ORDER BY fiscal_year)
)
SELECT ticker, company, fiscal_year, fiscal_year_end,
       revenue, gross_profit, operating_income, net_income, eps,
       operating_cash_flow, capex, free_cash_flow,
       ROUND(100.0 * gross_profit / revenue, 2)          AS gross_margin_pct,
       ROUND(100.0 * operating_income / revenue, 2)      AS operating_margin_pct,
       ROUND(100.0 * net_income / revenue, 2)            AS net_margin_pct,
       ROUND(100.0 * (revenue - prev_revenue) / prev_revenue, 2) AS revenue_growth_pct,
       CASE WHEN fiscal_year > first_year THEN
            ROUND(100.0 * (POWER(1.0 * revenue / first_revenue, 1.0 / (fiscal_year - first_year)) - 1), 2)
       END                                               AS revenue_cagr_pct,
       ROUND(1.0 * total_current_assets / total_current_liabilities, 2) AS current_ratio,
       ROUND(cogs / ((inventory + prev_inventory) / 2.0), 2)            AS inventory_turnover,
       ROUND(365.0 / (cogs / ((inventory + prev_inventory) / 2.0)), 1)  AS days_inventory,
       CASE WHEN shareholders_equity > 0
            THEN ROUND(1.0 * total_debt / shareholders_equity, 2) END   AS debt_to_equity,
       ROUND(100.0 * net_income / ((total_assets + prev_assets) / 2.0), 2) AS roa_pct,
       ROUND(100.0 * free_cash_flow / revenue, 2)        AS fcf_margin_pct,
       ROUND(100.0 * capex / revenue, 2)                 AS capex_pct_revenue,
       ROUND(1.0 * operating_cash_flow / net_income, 2)  AS cash_conversion
FROM lagged;
