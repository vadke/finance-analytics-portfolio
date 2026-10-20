"""Rebuild each dashboard's index.html from its template and the latest analysis output."""
from pathlib import Path
H = Path(__file__).parent
for proj, data in (("retail-peer-financials", "output/peer_data.min.json"), ("fpa-budget-forecast", "output/dash.min.json")):
    page = (H / proj / "dashboard" / "template.html").read_text().replace("__DATA__", (H / proj / data).read_text())
    head, _, body = page.partition('<div class="wrap">')
    (H / proj / "dashboard" / "index.html").write_text(
        '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        + head + '</head>\n<body>\n<div class="wrap">' + body + "\n</body>\n</html>\n")
    print("built", proj)
