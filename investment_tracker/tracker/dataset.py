"""Fetch everything once per run into a Dataset. All values go through the Ledger."""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

import pandas as pd

from . import fundamentals
from .cache import cached
from .metrics import fundamentals_table
from .provenance import Ledger
from .sources import calendars, fred, mof, news, yahoo


@dataclass
class Dataset:
    universe: pd.DataFrame
    ledger: Ledger
    prices: dict = field(default_factory=dict)        # ticker -> local-currency close
    prices_usd: dict = field(default_factory=dict)
    fx: dict = field(default_factory=dict)            # ccy -> units per USD
    snapshot: dict = field(default_factory=dict)      # ticker -> dict of latest metrics
    fund: dict = field(default_factory=dict)          # ticker -> derived quarterly table
    val_hist: dict = field(default_factory=dict)      # ticker -> quarter-end multiples
    headlines: dict = field(default_factory=dict)
    macro: dict = field(default_factory=dict)         # series name -> pd.Series
    macro_src: dict = field(default_factory=dict)
    calendar: list = field(default_factory=list)


def _macro(name: str, spec: dict, start: str, years: int, ds: Dataset):
    errors = []
    for src in spec["sources"]:
        kind, ident = src.split(":", 1)
        try:
            if kind == "fred":
                s = cached(f"fred:{ident}:{start}", fred.series, ident, start)
            elif kind == "mof":
                s = cached(f"mof:{ident}:{start}", mof.tenor, ident, start)
            elif kind == "yahoo":
                s = yahoo.close_series(ident, years)
            else:
                raise ValueError(kind)
            if s is not None and len(s):
                ds.macro[name] = s.rename(name)
                ds.macro_src[name] = src + (" (fallback)" if src != spec["sources"][0] else "")
                ds.ledger.add(name, "latest", float(s.iloc[-1]), src, s.index[-1].date())
                if src != spec["sources"][0]:
                    ds.ledger.gap(name, "primary_source", f"{spec['sources'][0]} failed ({errors[-1]}); used {src}")
                return
        except Exception as e:
            errors.append(f"{src}: {type(e).__name__}")
    ds.ledger.gap(name, "series", "all sources failed: " + "; ".join(errors))


def _valuation_listing(row, info: dict, ledger: Ledger):
    """Listing whose trading currency equals the reporting currency (avoids ADR ratio issues)."""
    fin_ccy = info.get("financialCurrency")
    for tk in [row.ticker] + [t for t in row.alt_tickers.split(";") if t]:
        raw = cached(f"info:{tk}", lambda: __import__("yfinance").Ticker(tk).info) or {}
        if fin_ccy and raw.get("currency") == fin_ccy:
            return tk, fin_ccy
    ledger.gap(row.ticker, "valuation_history", f"no listing trades in reporting currency {fin_ccy}")
    return None, fin_ccy


def _valuation_history(tk_val, px: pd.Series, shares: pd.Series, f: pd.DataFrame) -> pd.DataFrame:
    """Quarter-end TTM multiples: EV = price x shares + net debt."""
    rows = []
    f = f.assign(net_debt=f["net_debt"].ffill(limit=1))  # balance sheet can lag the income statement by a quarter
    for d, r in f.iterrows():
        p = px[px.index <= d]
        sh = shares[shares.index <= d] if shares is not None else pd.Series(dtype=float)
        if p.empty or sh.empty or (d - p.index[-1]).days > 10:
            continue
        mcap = p.iloc[-1] * sh.iloc[-1]
        ev = mcap + r.net_debt if pd.notna(r.net_debt) else float("nan")
        rows.append({"date": d, "mcap": mcap, "ev": ev,
                     "ev_sales_ttm": ev / r.revenue_ttm if r.revenue_ttm and r.revenue_ttm > 0 else float("nan"),
                     "ev_ebitda_ttm": ev / r.ebitda_ttm if r.ebitda_ttm and r.ebitda_ttm > 0 else float("nan"),
                     "pe_ttm": mcap / r.net_income_ttm if r.net_income_ttm and r.net_income_ttm > 0 else float("nan")})
    return pd.DataFrame(rows).set_index("date") if rows else pd.DataFrame()


def build(universe: pd.DataFrame, hyp: dict, settings: dict, log=print) -> Dataset:
    L = Ledger()
    ds = Dataset(universe=universe, ledger=L)
    years = settings["fetch_history_years"]
    start = (dt.date.today() - dt.timedelta(days=365 * years)).isoformat()

    for ccy in sorted(set(universe.currency) | {settings["secondary_currency"], "JPY", "EUR", "KRW", "TWD"}):
        s = yahoo.fx_per_usd(ccy, years, L)
        if s is not None:
            ds.fx[ccy] = s

    for _, row in universe.iterrows():
        tk = row.ticker
        log(f"  {tk:10s} {row.company}")
        snap = {"company": row.company, "bucket": row.bucket, "group": row.group, "currency": row.currency}
        px = yahoo.history(tk, years, L)
        if not px.empty:
            c = px["Close"]
            ds.prices[tk] = c
            fx = ds.fx.get(row.currency)
            ds.prices_usd[tk] = c if row.currency == "USD" else (c / fx.reindex(c.index).ffill()).dropna() if fx is not None else None
        info = yahoo.info(tk, L)
        snap.update(info)
        snap.update(yahoo.price_metrics(tk, px, L))
        snap.update(yahoo.analyst(tk, L))
        if row.currency == "USD":
            snap.update(yahoo.put_call(tk, L))
        else:
            L.gap(tk, "put_call_ratio", "no free options data for non-US listing")
        snap["next_earnings"] = yahoo.next_earnings(tk, L)
        if snap.get("target_mean_price") and snap.get("price"):
            snap["target_upside"] = L.add(tk, "target_upside", snap["target_mean_price"] / snap["price"] - 1,
                                          "computed: yfinance targetMeanPrice / last close", dt.date.today(), "ratio", "computed")
        # market cap / EV in USD for comparability
        fx_now = ds.fx[row.currency].iloc[-1] if row.currency in ds.fx else 1.0
        for k in ("market_cap", "enterprise_value"):
            if snap.get(k):
                snap[k + "_usd"] = snap[k] / fx_now

        q = fundamentals.gather(row, settings, L)
        f = fundamentals_table(q)
        ds.fund[tk] = f
        if not f.empty:
            for k in ("revenue_yoy", "revenue_yoy_chg_2q", "gross_margin", "operating_margin", "operating_margin_chg_4q",
                      "fcf_margin_ttm", "capex_pct_revenue", "net_debt", "net_debt_to_ebitda",
                      "net_debt_to_ebitda_chg_4q", "interest_coverage_ttm", "debt_chg_4q", "maturities_24m"):
                s = f[k].dropna()
                if s.empty:
                    L.gap(tk, k, "not computable from available quarters")
                    continue
                if (f.index[-1] - s.index[-1]).days > 100:
                    L.gap(tk, k, f"latest computable value is from {s.index[-1].date()}, over a quarter older "
                                 f"than the latest quarter {f.index[-1].date()}; not used as current")
                    continue
                snap[k] = float(s.iloc[-1])
                snap[k + "_asof"] = s.index[-1].date().isoformat()
                note = "computed"
                if k.startswith("net_debt_to_ebitda") and snap[k] == 99.0:
                    note = "computed; capped at 99x because TTM EBITDA <= 0 with positive net debt"
                L.add(tk, k, snap[k], "computed from merged quarterly fundamentals", s.index[-1].date(), note=note)

            raw_info = cached(f"info:{tk}", lambda: None) or {}
            vtk, _ = _valuation_listing(row, raw_info, L)
            if vtk:
                vpx = ds.prices.get(vtk)
                if vpx is None:
                    vh = yahoo.history(vtk, years, L)
                    vpx = vh["Close"] if not vh.empty else None
                shares = yahoo.shares_history(vtk, years, L)
                if vpx is not None and shares is not None:
                    vh = _valuation_history(vtk, vpx, shares, f)
                    ds.val_hist[tk] = vh
                    _current_multiples(tk, vtk, vpx, shares, f, vh, snap, L)
        ds.headlines[tk] = _news(row, settings, L, snap)
        ds.snapshot[tk] = snap

    log("  macro series")
    for name, spec in hyp["series"].items():
        _macro(name, spec, start, years, ds)

    if "US_CPI" in ds.macro:
        cpi = ds.macro["US_CPI"].dropna()
        # by date, not by row: FRED's CPI has missing months (e.g. the Oct-2025 shutdown)
        prior = cpi.reindex(cpi.index - pd.DateOffset(months=12)).values
        yoy = (pd.Series(cpi.values / prior - 1, index=cpi.index).dropna()) * 100
        ds.macro["US_CPI_YOY"] = yoy.rename("US_CPI_YOY")
        ds.macro_src["US_CPI_YOY"] = "computed from fred:CPIAUCSL (12-month % change)"
        L.add("US_CPI_YOY", "latest", float(yoy.iloc[-1]), "computed from fred:CPIAUCSL", yoy.index[-1].date(), "%", "computed")

    log("  calendars")
    for fn, name in ((calendars.fomc, "FOMC"), (calendars.boj, "BoJ"), (calendars.bls_cpi, "US CPI")):
        try:
            ev = cached(f"cal:{name}", fn)
            ds.calendar += ev
            if not ev:
                L.gap(name, "calendar", "parsed zero dates from official page")
        except Exception as e:
            L.gap(name, "calendar", f"fetch/parse failed: {type(e).__name__}")
    return ds


def _current_multiples(tk, vtk, vpx, shares, f, vh, snap, L):
    """Current TTM multiples. Each uses the latest quarter where its own denominator exists."""
    f = f.assign(net_debt=f["net_debt"].ffill(limit=1))
    vpx, shares = vpx.dropna(), shares.dropna()   # Yahoo can return an empty bar for the current session
    mcap = vpx.iloc[-1] * shares.iloc[-1]
    src = f"computed: {vtk} price x yfinance shares + latest net debt, over TTM fundamentals"
    today = dt.date.today()
    three_y = vh[vh.index >= pd.Timestamp.today() - pd.Timedelta(days=365 * 3)] if not vh.empty else vh
    for k, den, use_ev in (("ev_sales_ttm", "revenue_ttm", True), ("ev_ebitda_ttm", "ebitda_ttm", True),
                           ("pe_ttm", "net_income_ttm", False)):
        rows = f.dropna(subset=[den] + (["net_debt"] if use_ev else []))
        if rows.empty or rows.iloc[-1][den] <= 0 or (f.index[-1] - rows.index[-1]).days > 100:
            L.gap(tk, k, "denominator <= 0, missing, or older than one quarter (loss-making or no data)")
            continue
        r = rows.iloc[-1]
        v = (mcap + r.net_debt if use_ev else mcap) / r[den]
        snap[k] = L.add(tk, k, float(v), src + f" (fundamentals as of {rows.index[-1].date()})", today, "x", "computed")
        hist = three_y[k].dropna() if not three_y.empty and k in three_y else pd.Series(dtype=float)
        if len(hist) >= 8:
            snap[k + "_3y_avg"] = L.add(tk, k + "_3y_avg", float(hist.mean()), src + f"; mean of {len(hist)} quarter-ends",
                                        hist.index[-1].date(), "x", "computed")
            short = k.replace("_ttm", "")
            snap[f"{short}_vs_3y_avg"] = L.add(tk, f"{short}_vs_3y_avg", float(v / hist.mean() - 1), src, today, "ratio", "computed")
        else:
            L.gap(tk, k + "_3y_avg", f"only {len(hist)} quarter-end values in 3 years (need 8)")
    L.gap(tk, "forward_pe_3y_avg", "no free history of forward P/E; trailing multiples used for the 3-year comparison")


def _news(row, settings, L, snap):
    try:
        heads = cached(f"news:{row.ticker}", news.headlines, row.company, row.ticker, settings["news_days"])
    except Exception as e:
        L.gap(row.ticker, "news", f"failed: {type(e).__name__}")
        return []
    for h in heads:
        h["score"], h["rationale"] = news.score_lexicon(h["title"])
    if heads:
        snap["news_sentiment"] = L.add(row.ticker, "news_sentiment", round(sum(h["score"] for h in heads) / len(heads), 3),
                                       f"lexicon score, mean of {len(heads)} headlines over {settings['news_days']}d",
                                       dt.date.today(), "[-1,1]", "computed")
        snap["news_count"] = len(heads)
    else:
        L.gap(row.ticker, "news_sentiment", "no headlines found")
    return heads
