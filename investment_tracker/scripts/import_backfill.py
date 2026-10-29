"""Validate a transcribed backfill CSV against yfinance quarters, then append it to
data/fundamentals_manual.csv.

    python scripts/import_backfill.py path/to/TICKER.csv [--apply]

Overlap check: for each (period_end, field) present in both the backfill and
data/fundamentals_store.csv (yfinance), report the % difference. Revenue, operating income,
net income and cash must agree within 2% or nothing is imported. Any other field that differs by
more than 5% on the overlap uses a different definition (e.g. debt incl./excl. leases, capex
lines); it is NOT imported, so a series never splices two definitions. Without --apply nothing
is written.
"""
import _path  # noqa: F401
import sys

import pandas as pd

from tracker.fundamentals import MANUAL, STORE

STRICT = {"revenue", "operating_income", "net_income", "cash"}
COLS = ["ticker", "period_end", "field", "value", "currency", "source", "source_url", "note"]


def main(path, apply=False):
    new = pd.read_csv(path, dtype={"ticker": str})
    missing = set(COLS) - set(new.columns)
    if missing:
        raise SystemExit(f"missing columns {missing}")
    new = new[COLS]
    if new.source_url.isna().any() or (new.source_url.astype(str).str.len() < 10).any():
        raise SystemExit("every row needs a source_url")
    store = pd.read_csv(STORE, dtype={"ticker": str})
    m = new.merge(store, on=["ticker", "period_end", "field"], suffixes=("", "_yf"))
    m["pct_diff"] = (m.value - m.value_yf) / m.value_yf.abs()
    bad = m[m.field.isin(STRICT) & (m.pct_diff.abs() > 0.02)]
    pd.set_option("display.width", 200)
    print(f"{len(new)} rows; {len(m)} overlap with yfinance")
    if len(m):
        print(m[["period_end", "field", "value", "value_yf", "pct_diff"]].to_string(index=False,
              float_format=lambda x: f"{x:,.4g}"))
    if len(bad):
        print(f"\nBLOCKING: {len(bad)} strict fields differ by >2%")
        return 1
    if not len(m):
        print("\nWARNING: no overlap quarters to validate against")
    drop = sorted(set(m[~m.field.isin(STRICT) & (m.pct_diff.abs() > 0.05)].field))
    if drop:
        print(f"\nNot imported (definition differs from yfinance by >5%): {drop}")
        new = new[~new.field.isin(drop)]
    if apply:
        old = pd.read_csv(MANUAL, dtype={"ticker": str}) if MANUAL.exists() else pd.DataFrame(columns=COLS)
        allr = pd.concat([old, new]).drop_duplicates(["ticker", "period_end", "field"], keep="last")
        allr.sort_values(["ticker", "period_end", "field"]).to_csv(MANUAL, index=False)
        print(f"appended -> {MANUAL}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], "--apply" in sys.argv))
