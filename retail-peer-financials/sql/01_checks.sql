-- Data-quality checks: every row should return 0 failures.
SELECT 'fcf_ties_to_ocf_plus_capex' AS check_name,
       COUNT(*) AS failures
FROM cash_flow
WHERE ABS(operating_cash_flow + capital_expenditures - free_cash_flow) > 1
UNION ALL
SELECT 'gross_profit_below_revenue', COUNT(*)
FROM income_statement WHERE gross_profit >= revenue OR gross_profit <= 0
UNION ALL
SELECT 'operating_income_below_gross_profit', COUNT(*)
FROM income_statement WHERE operating_income >= gross_profit
UNION ALL
SELECT 'current_assets_within_total_assets', COUNT(*)
FROM balance_sheet WHERE total_current_assets > total_assets
UNION ALL
SELECT 'statements_join_one_to_one', COUNT(*)
FROM income_statement i
LEFT JOIN balance_sheet b USING (ticker, fiscal_year_end)
LEFT JOIN cash_flow c USING (ticker, fiscal_year_end)
WHERE b.ticker IS NULL OR c.ticker IS NULL;
