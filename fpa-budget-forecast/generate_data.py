"""Generate a SIMULATED monthly P&L (budget and actuals) for a fictional specialty retailer,
"Summit Outfitters". Margins are calibrated to public big-box retail peers. Seeded, so results reproduce."""
import csv
from pathlib import Path
import numpy as np

rng = np.random.default_rng(42)
OUT = Path(__file__).parent / "data"
MONTHS = [f"{y}-{m:02d}" for y in (2024, 2025, 2026) for m in range(1, 13)]
ACTUAL_THROUGH = "2026-09"
SEASON = np.array([0.065, 0.060, 0.072, 0.078, 0.085, 0.090, 0.088, 0.082, 0.075, 0.080, 0.105, 0.120])
SEASON = SEASON / SEASON.sum()
REGIONS = {"West": 0.34, "Southwest": 0.24, "Midwest": 0.22, "Northeast": 0.20}
CHANNELS = {"Stores": 0.72, "E-commerce": 0.28}
BASE_REVENUE_2024 = 1_200_000_000
BUDGET_GROWTH = 0.06
BUDGET_GM = 0.38
OPEX = {  # department: (% of revenue budgeted, fixed share of the cost)
    "Store Operations": (0.140, 0.60),
    "Marketing": (0.045, 0.20),
    "Supply Chain & Logistics": (0.050, 0.30),
    "Technology": (0.025, 0.85),
    "General & Administrative": (0.040, 0.90),
}

def idx(month): return MONTHS.index(month)

def actual_growth(region, channel, t):
    """Annualised growth path for actuals; t = months since Jan 2024."""
    g = 0.15 if channel == "E-commerce" else 0.03
    if region == "Northeast" and channel == "Stores" and t >= 17:  # softness from Jun 2025
        g = -0.06
    if region == "Southwest":
        g += 0.02
    return g

rows = []
budget_rev_month = {}
for i, month in enumerate(MONTHS):
    year, m = int(month[:4]), int(month[5:])
    yrs = year - 2024
    is_actual = month <= ACTUAL_THROUGH
    for region, rs in REGIONS.items():
        for channel, cs in CHANNELS.items():
            b_rev = BASE_REVENUE_2024 * (1 + BUDGET_GROWTH) ** yrs * SEASON[m - 1] * rs * cs
            rows.append([month, "Budget", "Revenue", "Revenue", region, channel, round(b_rev)])
            rows.append([month, "Budget", "COGS", "Cost of Goods Sold", region, channel, round(-b_rev * (1 - BUDGET_GM))])
            budget_rev_month[month] = budget_rev_month.get(month, 0) + b_rev
            if is_actual:
                level = 1.0
                for t in range(i):  # compound monthly growth along the path
                    level *= (1 + actual_growth(region, channel, t)) ** (1 / 12)
                a_rev = BASE_REVENUE_2024 * SEASON[m - 1] * rs * cs * level * rng.normal(1, 0.025)
                gm = BUDGET_GM + rng.normal(0, 0.004)
                if month in ("2025-07", "2025-08", "2025-09"):  # freight-cost spike
                    gm -= 0.015
                if channel == "E-commerce":
                    gm -= 0.01  # shipping and returns
                rows.append([month, "Actual", "Revenue", "Revenue", region, channel, round(a_rev)])
                rows.append([month, "Actual", "COGS", "Cost of Goods Sold", region, channel, round(-a_rev * (1 - gm))])

actual_rev_month = {}
for r in rows:
    if r[1] == "Actual" and r[2] == "Revenue":
        actual_rev_month[r[0]] = actual_rev_month.get(r[0], 0) + r[6]

for month in MONTHS:
    b_rev = budget_rev_month[month]
    annual_b = sum(v for k, v in budget_rev_month.items() if k[:4] == month[:4]) / 12
    for dept, (pct, fixed) in OPEX.items():
        b = pct * (fixed * annual_b + (1 - fixed) * b_rev)
        rows.append([month, "Budget", "Opex", dept, "Corporate", "All", round(-b)])
        if month <= ACTUAL_THROUGH:
            a_rev = actual_rev_month[month]
            a = pct * (fixed * annual_b + (1 - fixed) * a_rev) * rng.normal(1, 0.02)
            if dept == "Marketing" and month in ("2025-04", "2025-05", "2025-06"):
                a *= 1.28  # unplanned spring campaign
            if dept == "Supply Chain & Logistics" and month in ("2025-07", "2025-08", "2025-09"):
                a *= 1.15  # freight spike
            if dept == "Technology" and month >= "2026-01":
                a *= 0.88  # hiring delays
            rows.append([month, "Actual", "Opex", dept, "Corporate", "All", round(-a)])

OUT.mkdir(exist_ok=True)
with open(OUT / "pl_monthly.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["month", "scenario", "line_type", "line_item", "region", "channel", "amount_usd"])
    w.writerows(rows)
print(len(rows), "rows written")
