"""Budget vs. actual variance (SQL) and a driver-based rolling forecast (Python) for the simulated retailer."""
import csv, json, re, sqlite3
from pathlib import Path
import numpy as np

HERE = Path(__file__).parent
OUT = HERE / "output"
LAST_ACTUAL = "2026-09"

def month_range(start, n):
    y, m = int(start[:4]), int(start[5:])
    out = []
    for _ in range(n):
        out.append(f"{y}-{m:02d}"); m += 1
        if m == 13: y, m = y + 1, 1
    return out

def fit_forecast(series, months, horizon):
    """OLS on log revenue: trend + month-of-year effects. Returns forecast for the next `horizon` months."""
    t = np.arange(len(series))
    moy = np.array([int(m[5:]) for m in months])
    X = np.column_stack([np.ones_like(t), t] + [(moy == k).astype(float) for k in range(2, 13)])
    beta, *_ = np.linalg.lstsq(X, np.log(series), rcond=None)
    fut = month_range(month_range(months[-1], 2)[1], horizon)
    tf = np.arange(len(series), len(series) + horizon)
    mf = np.array([int(m[5:]) for m in fut])
    Xf = np.column_stack([np.ones_like(tf), tf] + [(mf == k).astype(float) for k in range(2, 13)])
    return fut, np.exp(Xf @ beta)

def main():
    OUT.mkdir(exist_ok=True)
    con = sqlite3.connect(OUT / "fpa.db")
    with open(HERE / "data" / "pl_monthly.csv", newline="") as f:
        rows = list(csv.DictReader(f))
    con.execute("DROP TABLE IF EXISTS pl_monthly")
    con.execute("CREATE TABLE pl_monthly (month, scenario, line_type, line_item, region, channel, amount_usd REAL)")
    con.executemany("INSERT INTO pl_monthly VALUES (?,?,?,?,?,?,?)", [list(r.values()) for r in rows])
    con.executescript((HERE / "sql" / "01_pl_views.sql").read_text())

    reports = {}
    for block in re.split(r"(?m)^-- name: ", (HERE / "sql" / "02_reports.sql").read_text())[1:]:
        name, sql = block.split("\n", 1)
        cur = con.execute(sql)
        cols = [d[0] for d in cur.description]
        reports[name.strip()] = [dict(zip(cols, r)) for r in cur.fetchall()]

    cur = con.execute("SELECT * FROM bva_monthly ORDER BY month, line_item")
    cols = [d[0] for d in cur.description]
    bva = [dict(zip(cols, r)) for r in cur.fetchall()]

    # ---- Forecast: one model per region x channel, summed to total ----
    act = {}
    for r in con.execute("""SELECT month, region, channel, SUM(amount_usd) FROM pl_monthly
                            WHERE scenario='Actual' AND line_type='Revenue' GROUP BY 1,2,3 ORDER BY 1"""):
        act.setdefault((r[1], r[2]), {})[r[0]] = r[3]
    months = sorted({m for d in act.values() for m in d})

    # Backtest: train through Dec 2025, predict Jan-Sep 2026, compare to actuals
    train = [m for m in months if m <= "2025-12"]; test = [m for m in months if m >= "2026-01"]
    bt = np.zeros(len(test))
    for key, d in act.items():
        _, f = fit_forecast(np.array([d[m] for m in train]), train, len(test)); bt += f
    actual_test = np.array([sum(d[m] for d in act.values()) for m in test])
    ape = np.abs(bt - actual_test) / actual_test
    backtest = {"months": test, "forecast": bt.round().tolist(), "actual": actual_test.round().tolist(),
                "mape_pct": round(100 * ape.mean(), 2), "max_ape_pct": round(100 * ape.max(), 2),
                "total_error_pct": round(100 * (bt.sum() - actual_test.sum()) / actual_test.sum(), 2)}

    # Rolling forecast: train on last 24 months, forecast Oct 2026 - Sep 2027
    window = months[-24:]; horizon = 12
    fc_by_seg = {}
    for key, d in act.items():
        fut, f = fit_forecast(np.array([d[m] for m in window]), window, horizon)
        fc_by_seg[f"{key[0]}|{key[1]}"] = f.round().tolist()
    fc_total = np.sum([np.array(v) for v in fc_by_seg.values()], axis=0)

    # Cost drivers from trailing 12 months of actuals
    t12 = months[-12:]
    ph = ",".join("?" * 12)
    rev_t12 = np.array([r[0] for r in con.execute(
        f"SELECT SUM(amount_usd) FROM pl_monthly WHERE scenario='Actual' AND line_type='Revenue' AND month IN ({ph}) GROUP BY month ORDER BY month", t12)])
    cogs_t12 = con.execute(f"SELECT SUM(amount_usd) FROM pl_monthly WHERE scenario='Actual' AND line_type='COGS' AND month IN ({ph})", t12).fetchone()[0]
    gm = 1 + cogs_t12 / rev_t12.sum()
    # Each department's monthly cost = fixed + variable * revenue (OLS on the trailing 12 months)
    opex_model = {}
    for (dept,) in con.execute("SELECT DISTINCT line_item FROM pl_monthly WHERE line_type='Opex'").fetchall():
        cost = -np.array([r[0] for r in con.execute(
            f"SELECT SUM(amount_usd) FROM pl_monthly WHERE scenario='Actual' AND line_item=? AND month IN ({ph}) GROUP BY month ORDER BY month", [dept] + t12)])
        b, a = np.polyfit(rev_t12, cost, 1)
        opex_model[dept] = {"fixed_monthly": round(a, 2), "variable_rate": round(b, 8)}
    SCEN = {"Base": (1.00, 0.0), "Upside": (1.03, 0.005), "Downside": (0.95, -0.010)}
    scenarios = {}
    for s, (rev_mult, gm_adj) in SCEN.items():
        rev = fc_total * rev_mult
        gp = rev * (gm + gm_adj)
        opex = sum(m["fixed_monthly"] + m["variable_rate"] * rev for m in opex_model.values())
        oi = gp - opex
        scenarios[s] = {"revenue": rev.round().tolist(), "gross_profit": gp.round().tolist(),
                        "opex": opex.round().tolist(), "operating_income": oi.round().tolist()}
    opex_ratio = None

    # FY2026 latest estimate = Jan-Sep actuals + Oct-Dec base forecast, vs FY2026 budget
    def fy_sum(line, scen):
        return con.execute("SELECT SUM(amount_usd) FROM pl_lines WHERE fiscal_year='2026' AND scenario=? AND line_item=?", (scen, line)).fetchone()[0]
    q4 = slice(0, 3)
    le = {"Revenue": fy_sum("Revenue", "Actual") + sum(scenarios["Base"]["revenue"][q4]),
          "Gross Profit": fy_sum("Gross Profit", "Actual") + sum(scenarios["Base"]["gross_profit"][q4]),
          "Operating Income": fy_sum("Operating Income", "Actual") + sum(scenarios["Base"]["operating_income"][q4])}
    fy_budget = {k: fy_sum(k, "Budget") for k in le}

    out = {"company": "Summit Outfitters (simulated data)", "last_actual": LAST_ACTUAL,
           "bva_monthly": bva, "reports": reports, "backtest": backtest,
           "forecast": {"months": fut, "by_segment": fc_by_seg, "scenarios": scenarios,
                        "assumptions": {"gross_margin_t12": round(gm, 8), "opex_model": opex_model,
                                        "scenarios": {k: {"revenue_multiplier": v[0], "gross_margin_adj": v[1]} for k, v in SCEN.items()}}},
           "fy2026": {"latest_estimate": le, "budget": fy_budget}}
    (OUT / "dashboard_data.json").write_text(json.dumps(out))
    keep = {"Revenue", "Cost of Goods Sold", "Gross Profit", "Store Operations", "Marketing",
            "Supply Chain & Logistics", "Technology", "General & Administrative", "Operating Income"}
    compact = dict(out, bva_monthly=[{k: r[k] for k in ("month", "line_item", "budget", "actual")} for r in bva if r["line_item"] in keep])
    (OUT / "dash.min.json").write_text(json.dumps(compact, separators=(",", ":")))
    with open(OUT / "budget_vs_actual_monthly.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(bva)
    print(json.dumps({"backtest": {k: v for k, v in backtest.items() if k.endswith("pct")},
                      "ytd": reports["ytd_2026"], "region": reports["region_channel_ytd"],
                      "yoy": reports["region_channel_yoy"], "fy2026": out["fy2026"],
                      "gm": gm, "opex_model": opex_model, "base_q4": [scenarios["Base"][k][:3] for k in ("revenue","operating_income")]}, indent=1, default=float))

if __name__ == "__main__":
    main()
