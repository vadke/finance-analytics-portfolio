# Big-Box Retail Benchmark

Compares Walmart, Costco, Target, Home Depot and Lowe's over their last five fiscal years using figures from their 10-K filings.

## Findings

- **Costco grew fastest**: revenue up 7.5% a year, from $227B to $303B, with the highest inventory turnover in the group (14.1x).
- **Target's operating margin nearly halved**: from 8.6% to 4.7% while revenue stayed flat (-0.3% a year).
- **Lowe's generates the most cash per dollar of sales**: 8.9% free cash flow margin, even though revenue fell 2.7% a year.
- **Walmart is spending heavily**: capex rose from 2.3% to 3.7% of revenue, which leaves the lowest free cash flow margin (2.1%) on $713B of revenue.

## How it works

1. `data/` holds the income statement, balance sheet and cash flow figures ($ millions).
2. `build.py` loads them into SQLite and runs `sql/01_checks.sql`: free cash flow must equal operating cash flow less capex, gross profit must sit below revenue, operating income below gross profit, and the three statements must join one-to-one. The build stops if any check fails.
3. `sql/02_ratios.sql` builds one view with growth, CAGR, margins, current ratio, inventory turnover, days inventory, debt to equity, ROA, FCF margin, capex intensity and cash conversion. It uses `LAG` and `FIRST_VALUE` window functions for the year-over-year measures.
4. `dashboard/index.html` is a self-contained page that reads the ratio output.

## Notes

- Fiscal years are labeled by the calendar year in which most of the period falls. Costco's year ends in late August, about seven months after the others.
- Debt to equity is not meaningful for Lowe's, whose shareholders' equity is negative after years of share buybacks.
- Source: company 10-K filings, as compiled by StockAnalysis.com.
