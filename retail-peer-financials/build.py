"""Load the peer financial statements into SQLite, run data checks, compute ratios, export for the dashboard."""
import csv, json, math, sqlite3, sys
from pathlib import Path

HERE = Path(__file__).parent
DB = HERE / "output" / "retail_peers.db"

def load(con, name):
    with open(HERE / "data" / f"{name}.csv", newline="") as f:
        rows = list(csv.DictReader(f))
    cols = rows[0].keys()
    con.execute(f"DROP TABLE IF EXISTS {name}")
    con.execute(f"CREATE TABLE {name} ({', '.join(cols)})")
    con.executemany(f"INSERT INTO {name} VALUES ({', '.join('?' * len(cols))})",
                    [[float(v) if k not in ("ticker", "company", "fiscal_year_end") else v for k, v in r.items()] for r in rows])

def main():
    DB.parent.mkdir(exist_ok=True)
    con = sqlite3.connect(DB)
    con.create_function("POWER", 2, math.pow)
    for t in ("income_statement", "balance_sheet", "cash_flow"):
        load(con, t)
    checks = con.execute((HERE / "sql" / "01_checks.sql").read_text()).fetchall()
    for name, fails in checks:
        print(f"check {name}: {fails} failures")
    if any(f for _, f in checks):
        sys.exit("data checks failed")
    con.executescript((HERE / "sql" / "02_ratios.sql").read_text())
    cur = con.execute("SELECT * FROM ratios ORDER BY ticker, fiscal_year")
    cols = [d[0] for d in cur.description]
    rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    with open(HERE / "output" / "ratios.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
    (HERE / "output" / "ratios.json").write_text(json.dumps(rows, indent=1))
    (HERE / "output" / "peer_data.min.json").write_text(json.dumps(rows, separators=(",", ":")))
    print(f"{len(rows)} company-years written")

if __name__ == "__main__":
    main()
