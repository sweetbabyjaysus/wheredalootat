"""yfinance adapter: prices, valuation, analyst data, short interest, options, earnings dates."""
from __future__ import annotations

import datetime as dt

import pandas as pd
import yfinance as yf

from ..cache import cached
from ..provenance import Ledger

INFO_FIELDS = {  # info key -> (our field, unit)
    "longName": ("name", ""), "shortName": ("short_name", ""), "exchange": ("exchange_code", ""), "currency": ("currency", ""),
    "quoteType": ("quote_type", ""), "marketCap": ("market_cap", "local"),
    "enterpriseValue": ("enterprise_value", "local"), "forwardPE": ("forward_pe", "x"),
    "enterpriseToEbitda": ("ev_ebitda_yf", "x"), "enterpriseToRevenue": ("ev_sales_yf", "x"),
    "recommendationMean": ("analyst_rating_mean", "1=strong buy..5=sell"),
    "recommendationKey": ("analyst_rating_key", ""), "numberOfAnalystOpinions": ("analyst_count", ""),
    "targetMeanPrice": ("target_mean_price", "local"), "shortPercentOfFloat": ("short_pct_float", "ratio"),
    "fiftyTwoWeekHigh": ("high_52w_yf", "local"), "financialCurrency": ("financial_currency", ""),
}


def history(ticker: str, years: int, ledger: Ledger) -> pd.DataFrame:
    df = cached(f"hist:{ticker}:{years}", lambda: yf.Ticker(ticker).history(period=f"{years}y", auto_adjust=True))
    if df.empty:
        ledger.gap(ticker, "price_history", "yfinance returned no prices")
        return df
    df.index = df.index.tz_localize(None).normalize()
    first = df.index[0].date()
    if first > dt.date.today() - dt.timedelta(days=365 * 2 - 7):
        ledger.gap(ticker, "price_history", f"history starts {first}; shorter than 2 years")
    return df[["Close", "Volume"]]


def info(ticker: str, ledger: Ledger) -> dict:
    raw = cached(f"info:{ticker}", lambda: yf.Ticker(ticker).info) or {}
    today = dt.date.today()
    out = {}
    for k, (f, unit) in INFO_FIELDS.items():
        v = raw.get(k)
        if k == "shortPercentOfFloat" and v is None:
            ledger.gap(ticker, f, "yfinance has no short interest (typically non-US listings)")
            continue
        out[f] = ledger.add(ticker, f, v, f"yfinance:info.{k}", today, unit)
    return out


def price_metrics(ticker: str, px: pd.DataFrame, ledger: Ledger) -> dict:
    """Returns, 52w-high distance, 200dma. Computed from yfinance closes."""
    if px.empty:
        return {}
    c = px["Close"].dropna()
    last_date = c.index[-1].date()
    src = "computed from yfinance daily closes"

    def ret(days=None, since=None):
        start = pd.Timestamp(since) if since else c.index[-1] - pd.Timedelta(days=days)
        base = c[c.index <= start]
        return None if base.empty else float(c.iloc[-1] / base.iloc[-1] - 1)

    m = {
        "price": float(c.iloc[-1]),
        "ret_1m": ret(30), "ret_3m": ret(91), "ret_1y": ret(365),
        "ret_ytd": ret(since=f"{last_date.year - 1}-12-31"),
        "pct_from_52w_high": float(c.iloc[-1] / c[c.index > c.index[-1] - pd.Timedelta(days=365)].max() - 1),
        "pct_vs_200dma": float(c.iloc[-1] / c.iloc[-200:].mean() - 1) if len(c) >= 200 else None,
    }
    for k, v in m.items():
        ledger.add(ticker, k, v, src, last_date, "local" if k == "price" else "ratio", "computed")
    return m


def analyst(ticker: str, ledger: Ledger) -> dict:
    t, today, out = yf.Ticker(ticker), dt.date.today(), {}
    try:
        tr = cached(f"epstrend:{ticker}", lambda: t.eps_trend)  # rows: 0q, +1q, 0y, +1y ; cols: current, 7daysAgo, 30daysAgo, 60daysAgo, 90daysAgo
        row = tr.loc["+1y"]
        for d in (30, 90):
            base = row.get(f"{d}daysAgo")
            # divide by |base| so the sign means "estimates went up" even when EPS < 0
            v = (row["current"] - base) / abs(base) if base else None
            out[f"eps_revision_{d}d"] = ledger.add(
                ticker, f"eps_revision_{d}d", v, "yfinance:eps_trend[+1y]", today, "ratio",
                "next-fiscal-year EPS used as NTM proxy")
    except Exception as e:
        ledger.gap(ticker, "eps_revision", f"yfinance eps_trend unavailable ({type(e).__name__})")
    return out


class _Chain:
    def __init__(self, calls, puts):
        self.calls, self.puts = calls, puts


def _chain(t, e):
    oc = t.option_chain(e)
    return _Chain(oc.calls, oc.puts)


def put_call(ticker: str, ledger: Ledger, expiries: int = 3) -> dict:
    t = yf.Ticker(ticker)
    try:
        exps = cached(f"opts:{ticker}", lambda: t.options)[:expiries]
    except Exception:
        exps = ()
    if not exps:
        ledger.gap(ticker, "put_call_ratio", "no listed options on yfinance")
        return {}
    pv = cv = po = co = 0.0
    for e in exps:
        ch = cached(f"chain:{ticker}:{e}", lambda: _chain(t, e))
        pv += ch.puts["volume"].fillna(0).sum(); cv += ch.calls["volume"].fillna(0).sum()
        po += ch.puts["openInterest"].fillna(0).sum(); co += ch.calls["openInterest"].fillna(0).sum()
    src = f"yfinance option_chain, nearest {len(exps)} expiries"
    today = dt.date.today()
    return {"put_call_volume": ledger.add(ticker, "put_call_volume", pv / cv if cv else None, src, today, "x", "computed"),
            "put_call_oi": ledger.add(ticker, "put_call_oi", po / co if co else None, src, today, "x", "computed")}


def next_earnings(ticker: str, ledger: Ledger):
    try:
        ed = cached(f"edates:{ticker}", lambda: yf.Ticker(ticker).get_earnings_dates(limit=8))
        fut = [d for d in ed.index if d.tz_localize(None) >= pd.Timestamp.today().normalize()]
        if fut:
            d = min(fut).date().isoformat()
            return ledger.add(ticker, "next_earnings", d, "yfinance:get_earnings_dates", dt.date.today())
    except Exception:
        pass
    try:  # fallback: Ticker.calendar
        cal = cached(f"cal:{ticker}", lambda: yf.Ticker(ticker).calendar) or {}
        fut = [d for d in cal.get("Earnings Date", []) if pd.Timestamp(d) >= pd.Timestamp.today().normalize()]
        if fut:
            return ledger.add(ticker, "next_earnings", min(fut).isoformat(), "yfinance:calendar", dt.date.today(),
                              note="may be an estimate; yfinance does not flag confirmed vs projected")
    except Exception:
        pass
    ledger.gap(ticker, "next_earnings", "no future earnings date on yfinance")
    return None


def quarterly_statements(ticker: str, ledger: Ledger) -> pd.DataFrame:
    """Fallback fundamentals for non-SEC filers. yfinance usually has only 4-5 quarters."""
    t = yf.Ticker(ticker)
    inc, bs, cf = cached(f"qstmts:{ticker}",
                         lambda: (t.quarterly_income_stmt, t.quarterly_balance_sheet, t.quarterly_cashflow))
    pick = {
        "revenue": (inc, ["Total Revenue", "Operating Revenue"]),
        "gross_profit": (inc, ["Gross Profit"]),
        "operating_income": (inc, ["Operating Income", "Total Operating Income As Reported"]),
        "net_income": (inc, ["Net Income", "Net Income Common Stockholders"]),
        "interest_expense": (inc, ["Interest Expense"]),
        "d_and_a": (cf, ["Depreciation And Amortization", "Depreciation Amortization Depletion"]),
        "cfo": (cf, ["Operating Cash Flow"]),
        "capex": (cf, ["Capital Expenditure"]),
        "debt_total": (bs, ["Total Debt"]),
        "cash": (bs, ["Cash Cash Equivalents And Short Term Investments", "Cash And Cash Equivalents"]),
    }
    rows = {}
    for f, (df, keys) in pick.items():
        key = next((k for k in keys if df is not None and k in df.index), None)
        if key is None:
            ledger.gap(ticker, f, "not in yfinance quarterly statements")
            continue
        rows[f] = df.loc[key]
    out = pd.DataFrame(rows).sort_index()
    out.index = pd.to_datetime(out.index)
    out = out.dropna(how="all")
    if "capex" in out:
        out["capex"] = out["capex"].abs()
    for q, r in out.iterrows():
        for f, v in r.items():
            if pd.notna(v):
                ledger.add(ticker, f"q:{f}", float(v), "yfinance:quarterly statements", q.date(), "local")
    return out


def fx_per_usd(ccy: str, years: int, ledger: Ledger) -> pd.Series:
    """Units of `ccy` per 1 USD, daily (Yahoo `{ccy}=X`)."""
    if ccy == "USD":
        return None
    df = cached(f"fx:{ccy}:{years}", lambda: yf.Ticker(f"{ccy}=X").history(period=f"{years}y"))
    if df.empty:
        ledger.gap(ccy, "fx", f"Yahoo {ccy}=X returned nothing")
        return None
    s = df["Close"]
    s.index = s.index.tz_localize(None).normalize()
    return s[~s.index.duplicated(keep="last")]


def shares_history(ticker: str, years: int, ledger: Ledger) -> pd.Series:
    start = (dt.date.today() - dt.timedelta(days=365 * years)).isoformat()
    try:
        s = cached(f"shares:{ticker}:{years}", lambda: yf.Ticker(ticker).get_shares_full(start=start))
    except Exception:
        s = None
    if s is None or len(s) == 0:
        ledger.gap(ticker, "shares_history", "yfinance get_shares_full returned nothing")
        return None
    s.index = pd.to_datetime(s.index).tz_localize(None).normalize()
    return s[~s.index.duplicated(keep="last")].sort_index()


def close_series(symbol: str, years: int) -> pd.Series:
    df = cached(f"hist:{symbol}:{years}", lambda: yf.Ticker(symbol).history(period=f"{years}y", auto_adjust=True))
    s = df["Close"]
    s.index = s.index.tz_localize(None).normalize()
    return s[~s.index.duplicated(keep="last")]
