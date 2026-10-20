# Finance Analytics Portfolio

Two finance projects, each with SQL, Python, and a live dashboard.

| Project | What it covers | Tools |
|---|---|---|
| [Big-Box Retail Benchmark](retail-peer-financials/) | Five years of 10-K financials for Walmart, Costco, Target, Home Depot and Lowe's: growth, margins, inventory turnover, free cash flow, leverage | SQL (CTEs, window functions), Python, SQLite, Chart.js |
| [Summit Outfitters FP&A](fpa-budget-forecast/) | Budget vs. actual variance analysis and a 12-month rolling forecast with Base, Upside and Downside scenarios (simulated company) | SQL, Python (NumPy), Excel model with live formulas, Chart.js |

Live dashboards: open `retail-peer-financials/dashboard/index.html` and `fpa-budget-forecast/dashboard/index.html` in a browser, or view them on GitHub Pages.

## Run it

```bash
pip install -r requirements.txt
python retail-peer-financials/build.py         # load statements, run data checks, compute ratios
python fpa-budget-forecast/generate_data.py    # simulated budget and actuals (seeded)
python fpa-budget-forecast/analysis.py         # variance SQL, forecast, backtest
python fpa-budget-forecast/build_excel.py      # Excel model
python build_pages.py                          # refresh both dashboards
```
