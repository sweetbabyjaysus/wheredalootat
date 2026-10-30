"""Supplier-customer links from config/relationships.csv, measured against prices.

For each pair: how closely the two trade (90-day and 1-year correlation and beta of supplier
returns on customer returns) and how the supplier moved around the customer's earnings.
Earnings dates come from the customer's SEC 8-K Item 2.02 filings (US filers only). The
reaction window runs from the close before the filing date to the close the day after it, so it
covers results released before the open or after the close.
"""
from __future__ import annotations

import pandas as pd

from .cache import cached
from .config import CONFIG
from .sources import sec

SUBMISSIONS = "https://data.sec.gov/submissions/CIK{cik:010d}.json"


def load() -> pd.DataFrame:
    p = CONFIG / "relationships.csv"
    return pd.read_csv(p, dtype=str).fillna("") if p.exists() else pd.DataFrame()


def earnings_8k_dates(ticker: str, user_agent: str) -> list[pd.Timestamp]:
    c = sec.cik(ticker, user_agent)
    if c is None:
        return []
    def get():
        return sec._session(user_agent).get(SUBMISSIONS.format(cik=c), timeout=30).json()
    rec = cached(f"secsub:{c}", get)["filings"]["recent"]
    return sorted({pd.Timestamp(d) for f, d, items in zip(rec["form"], rec["filingDate"], rec["items"])
                   if f == "8-K" and "2.02" in items})


def _window_return(px: pd.Series, d: pd.Timestamp):
    before = px[px.index < d]
    after = px[px.index > d]
    if before.empty or after.empty:
        return None
    return float(after.iloc[0] / before.iloc[-1] - 1)


def analyse(ds, settings, ledger):
    rel = load()
    if rel.empty:
        return pd.DataFrame(), pd.DataFrame()
    summary, events = [], []
    for (sup, cus), g in rel.groupby(["supplier", "customer"], sort=False):
        ps, pc = ds.prices.get(sup), ds.prices.get(cus)
        if ps is None or pc is None:
            ledger.gap(f"{sup}/{cus}", "relationship", "both tickers must be in universe.csv with prices")
            continue
        r = pd.concat([ps.pct_change(), pc.pct_change()], axis=1, keys=["s", "c"]).dropna()
        row = {"supplier": sup, "customer": cus, "links": " | ".join(g.relationship),
               "sources": " ; ".join(g.source_url)}
        for label, days in (("90d", 90), ("1y", 252)):
            w = r.iloc[-days:]
            row[f"corr_{label}"] = w.s.corr(w.c)
            row[f"beta_{label}"] = w.s.cov(w.c) / w.c.var()
        try:
            dates = [d for d in earnings_8k_dates(cus, settings["sec_user_agent"]) if d >= r.index[0]][-8:]
        except Exception as e:
            dates = []
            ledger.gap(cus, "earnings_8k_dates", f"SEC submissions failed: {type(e).__name__}")
        for d in dates:
            rs, rc = _window_return(ps, d), _window_return(pc, d)
            if rs is None or rc is None:
                continue
            events.append({"supplier": sup, "customer": cus, "customer_8k_2.02_date": d.date(),
                           "customer_move": rc, "supplier_move": rs, "same_direction": (rs > 0) == (rc > 0)})
        ev = [e for e in events if e["supplier"] == sup and e["customer"] == cus]
        if ev:
            row["earnings_events"] = len(ev)
            row["same_direction_share"] = sum(e["same_direction"] for e in ev) / len(ev)
            row["last_event"] = str(ev[-1]["customer_8k_2.02_date"])
            row["last_customer_move"] = ev[-1]["customer_move"]
            row["last_supplier_move"] = ev[-1]["supplier_move"]
        for k in ("corr_90d", "corr_1y", "beta_1y"):
            ledger.add(f"{sup}/{cus}", k, row[k], "computed from yfinance daily closes", r.index[-1].date(), note="computed")
        summary.append(row)
    return pd.DataFrame(summary), pd.DataFrame(events)
