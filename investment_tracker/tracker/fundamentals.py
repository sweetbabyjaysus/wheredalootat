"""Merge quarterly fundamentals from every source, with provenance per value.

Sources, in priority order:
  sec       SEC companyfacts (US filers and some 20-F filers)
  manual    data/fundamentals_manual.csv - figures taken by hand from company filings / IR files,
            each row carrying its document URL. Used to backfill quarters free APIs don't have.
  yfinance  yfinance quarterly statements (usually the latest 4-6 quarters)
  store     data/fundamentals_store.csv - every yfinance quarter seen on earlier runs, so
            history accumulates beyond yfinance's rolling window.

Per field, the source with the most quarters becomes the backbone (so one definition is used
where possible) and other sources only fill dates it lacks. Every value keeps its own source.
"""
from __future__ import annotations

import datetime as dt

import pandas as pd

from .config import ROOT
from .provenance import Ledger
from .sources import sec, yahoo

MANUAL = ROOT / "data" / "fundamentals_manual.csv"
STORE = ROOT / "data" / "fundamentals_store.csv"
PRIORITY = ["sec", "manual", "yfinance", "store"]
FIELDS = ["revenue", "gross_profit", "cost_of_revenue", "operating_income", "net_income", "ebitda", "d_and_a",
          "interest_expense", "cfo", "capex", "debt_total", "finance_lease_liability", "short_term_borrowings",
          "cash", "short_term_investments", "maturity_next_12m", "maturity_year_2"]


def _long_from_ledger(tmp: Ledger, kind: str) -> list[dict]:
    out = []
    for d in tmp.data:
        if d.field.startswith("q:"):
            out.append({"date": pd.Timestamp(d.as_of), "field": d.field[2:], "value": d.value,
                        "source": d.source, "unit": d.unit, "note": d.note, "kind": kind})
    return out


def _from_csv(path, ticker, kind):
    if not path.exists():
        return []
    df = pd.read_csv(path, dtype={"ticker": str})
    df = df[df.ticker == ticker]
    out = []
    for _, r in df.iterrows():
        src = r.get("source", kind)
        if isinstance(r.get("source_url"), str) and r["source_url"]:
            src = f"{src} <{r['source_url']}>"
        out.append({"date": pd.Timestamp(r.period_end), "field": r.field, "value": float(r.value),
                    "source": src, "unit": r.get("currency", ""), "note": str(r.get("note", "") or ""), "kind": kind})
    return out


def _snap_dates(recs: list[dict], tol_days: int = 10) -> list[dict]:
    """Different sources may date the same fiscal quarter a few days apart; use one date."""
    recs = sorted(recs, key=lambda r: PRIORITY.index(r["kind"]))
    anchors: list[pd.Timestamp] = []
    for r in recs:
        hit = next((a for a in anchors if abs((a - r["date"]).days) <= tol_days), None)
        if hit is None:
            anchors.append(r["date"])
        else:
            r["date"] = hit
    return recs


def gather(row, settings: dict, ledger: Ledger) -> pd.DataFrame:
    tk = row.ticker
    recs = []
    if row.fundamentals_source == "sec":
        tmp = Ledger()
        try:
            sec.quarterly(tk, settings["sec_user_agent"], tmp)
            recs += _long_from_ledger(tmp, "sec")
        except Exception as e:
            ledger.gap(tk, "sec_fundamentals", f"SEC fetch failed: {type(e).__name__}: {str(e)[:80]}")
    tmp = Ledger()
    try:
        yahoo.quarterly_statements(tk, tmp)
        yf_recs = _long_from_ledger(tmp, "yfinance")
    except Exception as e:
        yf_recs = []
        ledger.gap(tk, "yfinance_fundamentals", f"failed: {type(e).__name__}")
    recs += yf_recs + _from_csv(MANUAL, tk, "manual") + _from_csv(STORE, tk, "store")
    _append_store(tk, yf_recs)
    if not recs:
        ledger.gap(tk, "fundamentals", "no quarterly data from any source")
        return pd.DataFrame()
    recs = _snap_dates(recs)
    df = pd.DataFrame(recs)
    horizon = pd.Timestamp.today() - pd.Timedelta(days=365 * 5)
    df = df[df.date >= horizon]

    chosen = []
    for field, g in df.groupby("field"):
        counts = g.groupby("kind").date.nunique()
        backbone = max(counts.index, key=lambda k: (counts[k], -PRIORITY.index(k)))
        order = [backbone] + [k for k in PRIORITY if k != backbone]
        g = g.assign(rank=g.kind.map(order.index)).sort_values("rank")
        chosen.append(g.drop_duplicates("date", keep="first"))
    best = pd.concat(chosen)
    for _, r in best.iterrows():
        ledger.add(tk, f"q:{r.field}", float(r.value), r.source, r.date.date(), r.unit,
                   (r.note + "; " if r.note else "") + ("filled from secondary source" if r.kind != best[best.field == r.field].kind.mode()[0] else ""))
    wide = best.pivot(index="date", columns="field", values="value").sort_index()
    for f in ("revenue", "operating_income", "cfo", "capex", "debt_total", "cash"):
        if f not in wide or wide[f].dropna().empty:
            ledger.gap(tk, f, "not available from any fundamentals source")
    recent = wide.index[wide.index >= pd.Timestamp.today() - pd.Timedelta(days=365 * 2 + 120)]
    n_rev = int(wide.loc[recent, "revenue"].notna().sum()) if "revenue" in wide else 0
    if n_rev < settings["quarters"]:
        ledger.gap(tk, "fundamentals_quarters",
                   f"{n_rev} of {settings['quarters']} recent quarters of revenue available; "
                   "backfill from filings via data/fundamentals_manual.csv")
    return wide


def _append_store(ticker: str, yf_recs: list[dict]):
    if not yf_recs:
        return
    new = pd.DataFrame([{"ticker": ticker, "period_end": r["date"].date().isoformat(), "field": r["field"],
                         "value": r["value"], "currency": r["unit"],
                         "source": f"yfinance quarterly statements (stored {dt.date.today().isoformat()})",
                         "source_url": "", "note": ""} for r in yf_recs])
    old = pd.read_csv(STORE, dtype={"ticker": str}) if STORE.exists() else new.iloc[0:0]
    allr = pd.concat([old, new]).drop_duplicates(["ticker", "period_end", "field"], keep="first")
    allr.sort_values(["ticker", "period_end", "field"]).to_csv(STORE, index=False)
