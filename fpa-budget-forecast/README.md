# Summit Outfitters FP&A

Budget vs. actual variance analysis and a rolling forecast for a specialty outdoor retailer with four regions (West, Southwest, Midwest, Northeast) and two channels (stores, e-commerce).

**The company and its data are simulated.** No public company releases budget-level detail, so `generate_data.py` creates 33 months of actuals (Jan 2024 to Sep 2026) and three annual budgets. Margins are set close to those of public big-box retailers. The data includes realistic events to explain: a shift to e-commerce, a Northeast store slowdown, a freight cost spike, a spring marketing overspend and delayed technology hires.

## Results (FY2026, actuals through September)

- Revenue $966.8M year to date, 3.2% ahead of budget. Operating income $70.2M, 11.9% ahead.
- E-commerce beat plan in every region (+23% to +28%). Northeast stores are the weakest segment: 12.3% below budget and down 4.3% year over year.
- Gross margin 37.6% vs. 38.0% budgeted, mostly from the mix shift toward lower-margin online orders.
- FY2026 latest estimate: $1.40B revenue (+4.0% vs. budget) and $122.5M operating income (+13.6%).
- Forecast backtest: trained on data through Dec 2025 and tested on Jan to Sep 2026, the model's mean monthly error was 1.5% (worst month 4.6%).

## How it works

| File | Purpose |
|---|---|
| `generate_data.py` | Builds the simulated monthly P&L (seeded, so results reproduce) |
| `sql/01_pl_views.sql` | Rolls the ledger into a P&L with gross profit and operating income, and computes monthly budget vs. actual variance with a favorable or unfavorable flag |
| `sql/02_reports.sql` | Year-to-date variance by P&L line, variance by region and channel (ranked), and year-over-year growth |
| `analysis.py` | Runs the SQL, fits the revenue forecast, backtests it, fits fixed and variable cost drivers, and builds the scenarios and latest estimate |
| `build_excel.py` | Writes `output/Summit_Outfitters_FPA_Model.xlsx` |

**Revenue forecast.** A log-linear trend with month-of-year effects, fitted separately for each of the eight region and channel segments on the latest 24 months, then summed.

**Cost forecast.** Each department's monthly cost is split into a fixed amount plus a variable rate on revenue, using a regression on the trailing 12 months. This keeps fixed costs flat through the holiday peak instead of scaling them with sales.

**Scenarios.** Upside is +3% revenue and +0.5 points of gross margin. Downside is -5% revenue and -1.0 point of gross margin.

## Excel model

`output/Summit_Outfitters_FPA_Model.xlsx` has 500+ live formulas and no pasted results:

- **Assumptions**: a scenario dropdown and every forecast driver. Blue cells are inputs; yellow cells are the key levers.
- **Data**: monthly budget and actual by P&L line, plus the base revenue forecast.
- **Budget vs Actual**: FY2026 by month (SUMIFS), variance in dollars and percent, YTD, and the full-year latest estimate.
- **Forecast**: Oct 2026 to Sep 2027 P&L that recalculates when you change the scenario.
