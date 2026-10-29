"""Group comparison, trends, sentiment matrix, yield sensitivity and event studies."""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

BUCKET_ORDER = ["Bottleneck", "Compute leader", "Hyperscaler", "Leveraged buildout"]

COMPARE_METRICS = [
    "ret_1m", "ret_3m", "ret_ytd", "ret_1y", "pct_from_52w_high", "pct_vs_200dma",
    "forward_pe", "ev_ebitda_yf", "ev_sales_yf", "ev_ebitda_ttm", "ev_ebitda_vs_3y_avg", "ev_sales_vs_3y_avg",
    "pe_vs_3y_avg", "revenue_yoy", "revenue_yoy_chg_2q", "gross_margin", "operating_margin", "operating_margin_chg_4q",
    "fcf_margin_ttm", "capex_pct_revenue", "net_debt_to_ebitda", "net_debt_to_ebitda_chg_4q",
    "interest_coverage_ttm", "debt_chg_4q", "analyst_rating_mean", "target_upside", "eps_revision_30d",
    "eps_revision_90d", "short_pct_float", "put_call_volume", "news_sentiment",
    "corr90_us10y", "corr90_jgb30", "corr90_usdjpy",
]


def company_table(ds) -> pd.DataFrame:
    df = pd.DataFrame.from_dict(ds.snapshot, orient="index")
    df.index.name = "ticker"
    return df


def group_comparison(ct: pd.DataFrame) -> pd.DataFrame:
    cols = [c for c in COMPARE_METRICS if c in ct]
    g = ct.groupby("bucket")[cols].median(numeric_only=True).T
    n = ct.groupby("bucket")[cols].count().T.add_prefix("n_")
    g = g[[b for b in BUCKET_ORDER if b in g]]
    return g.join(n[[f"n_{b}" for b in g.columns]])


def trends(ds) -> pd.DataFrame:
    rows = []
    for tk, f in ds.fund.items():
        if f.empty:
            continue
        px = ds.prices.get(tk)
        f = f[f.index >= pd.Timestamp.today() - pd.Timedelta(days=365 * 2 + 100)]
        prev = None
        for d, r in f.iterrows():
            pchg = np.nan
            if px is not None and prev is not None:
                a, b = px[px.index <= prev], px[px.index <= d]
                if len(a) and len(b) and (d - b.index[-1]).days <= 10:
                    pchg = b.iloc[-1] / a.iloc[-1] - 1
            prev = d
            rows.append({"ticker": tk, "company": ds.snapshot[tk]["company"], "bucket": ds.snapshot[tk]["bucket"],
                         "quarter_end": d.date(), "revenue_yoy": r.revenue_yoy, "gross_margin": r.gross_margin,
                         "operating_margin": r.operating_margin, "net_debt_to_ebitda": r.net_debt_to_ebitda,
                         "capex_pct_revenue": r.capex_pct_revenue, "price_chg_in_quarter": pchg})
    return pd.DataFrame(rows)


def _z(s: pd.Series) -> pd.Series:
    s = pd.to_numeric(s, errors="coerce")
    sd = s.std()
    return (s - s.mean()) / sd if sd and not math.isnan(sd) else s * np.nan


def scores(ct: pd.DataFrame, settings: dict) -> pd.DataFrame:
    """Sentiment and fundamentals-momentum z-score blends (higher = better)."""
    comp = pd.DataFrame(index=ct.index)
    comp["z_rating"] = -_z(ct.get("analyst_rating_mean"))          # 1 = strong buy, so invert
    comp["z_revision"] = _z(ct.get("eps_revision_90d"))
    comp["z_short"] = -_z(ct.get("short_pct_float"))
    comp["z_news"] = _z(ct.get("news_sentiment"))
    comp["z_rev_growth"] = _z(ct.get("revenue_yoy"))
    comp["z_margin_trend"] = _z(ct.get("operating_margin_chg_4q"))
    comp["z_fcf"] = _z(ct.get("fcf_margin_ttm"))
    w_s, w_f = settings["sentiment_score_weights"], settings["fundamentals_score_weights"]
    s_map = {"z_rating": abs(w_s["analyst_rating"]), "z_revision": abs(w_s["eps_revision_90d"]),
             "z_short": abs(w_s["short_interest"]), "z_news": abs(w_s["news"])}
    f_map = {"z_rev_growth": w_f["revenue_yoy"], "z_margin_trend": w_f["operating_margin_chg_4q"],
             "z_fcf": w_f["fcf_margin"]}

    def blend(m, min_n):
        z = comp[list(m)]
        w = pd.DataFrame({k: z[k].notna() * v for k, v in m.items()})
        val = (z.fillna(0) * pd.Series(m)).sum(axis=1) / w.sum(axis=1)
        return val.where(z.notna().sum(axis=1) >= min_n), z.notna().sum(axis=1)

    comp["sentiment_score"], comp["sentiment_inputs"] = blend(s_map, 2)
    comp["fundamentals_score"], comp["fundamentals_inputs"] = blend(f_map, 2)
    gap = comp["fundamentals_score"] - comp["sentiment_score"]
    comp["gap"] = gap
    thr = settings["divergence_z_gap"]
    comp["flag"] = np.select([gap > thr, gap < -thr],
                             ["Inference: possible opportunity (fundamentals > sentiment)",
                              "Inference: possible trap (sentiment > fundamentals)"], "")
    comp.insert(0, "company", ct["company"])
    comp.insert(1, "bucket", ct["bucket"])
    return comp


def sentiment_trend(sc: pd.DataFrame, prev: dict | None) -> pd.DataFrame:
    out = sc[["company", "bucket", "sentiment_score", "fundamentals_score"]].copy()
    if not prev:
        out["prev_sentiment"] = np.nan
        out["change"] = np.nan
        out["prev_snapshot"] = ""
        return out
    ps = {tk: v.get("sentiment_score") for tk, v in prev.get("companies", {}).items()}
    out["prev_sentiment"] = out.index.map(ps)
    out["change"] = out["sentiment_score"] - out["prev_sentiment"]
    out["prev_snapshot"] = prev.get("date", "")
    return out.sort_values("change", key=lambda s: s.abs(), ascending=False)


# ---------- returns, groups, yields ----------

def daily_returns(prices: dict) -> pd.DataFrame:
    """Each stock's return on its own trading calendar, then aligned. (Computing on a combined
    calendar would blank a US stock's return the day after a Tokyo-only session.)"""
    return pd.DataFrame({k: v.dropna().pct_change() for k, v in prices.items() if v is not None})


def window(df, years=2):
    return df[df.index >= df.index.max() - pd.Timedelta(days=365 * years)]


def group_index(ds, ccy: str = "USD", years: int = 2) -> pd.DataFrame:
    """Equal-weight buy-and-hold index (equal money in each member at the start).

    Rebalanced to equal weights only when membership changes (a member lists later, e.g. CRWV,
    SNDK), so late joiners enter at the group's level at that date. Daily rebalancing was not
    used: with very volatile members it adds a large volatility-harvesting effect."""
    px = window(pd.DataFrame({k: v for k, v in ds.prices_usd.items() if v is not None}).ffill(limit=5), years)
    out = {}
    for b in BUCKET_ORDER:
        members = [t for t in ds.universe[ds.universe.bucket == b].ticker if t in px]
        if not members:
            continue
        p = px[members]
        live = p.notna()
        change_days = [p.index[0]] + [d for d, prev, cur in zip(p.index[1:], live.values[:-1], live.values[1:])
                                      if (cur & ~prev).any()]
        level, pieces = 100.0, []
        for k, d0 in enumerate(change_days):
            d1 = change_days[k + 1] if k + 1 < len(change_days) else None
            seg = p[(p.index >= d0) & ((p.index <= d1) if d1 is not None else True)]
            cols = seg.columns[seg.iloc[0].notna()]
            rel = seg[cols].div(seg[cols].iloc[0]).ffill()
            lvl = rel.mean(axis=1) * level
            pieces.append(lvl if d1 is None else lvl.iloc[:-1])
            level = lvl.iloc[-1]
        out[b] = pd.concat(pieces)
    idx = pd.DataFrame(out)
    if ccy != "USD" and ccy in ds.fx:
        fx = ds.fx[ccy].reindex(idx.index).ffill()
        idx = idx.mul(fx / fx.iloc[0], axis=0)
    return idx


def group_return_table(ds) -> pd.DataFrame:
    rows = []
    for ccy in ("USD", "THB"):
        idx = group_index(ds, ccy, years=2)
        for b in idx:
            s = idx[b].dropna()
            last = s.index[-1]
            def r(days=None, since=None):
                start = pd.Timestamp(since) if since else last - pd.Timedelta(days=days)
                base = s[s.index <= start]
                return s.iloc[-1] / base.iloc[-1] - 1 if len(base) else np.nan
            rows.append({"group": b, "currency": ccy, "ret_1m": r(30), "ret_3m": r(91),
                         "ret_ytd": r(since=f"{last.year - 1}-12-31"), "ret_1y": r(365), "ret_2y": s.iloc[-1] / s.iloc[0] - 1})
    return pd.DataFrame(rows)


def macro_frame(ds) -> pd.DataFrame:
    return pd.DataFrame(ds.macro).sort_index()


def macro_changes(ds) -> pd.DataFrame:
    rows = []
    for k, s in ds.macro.items():
        s = s.dropna()
        last = s.index[-1]
        def ch(days):
            base = s[s.index <= last - pd.Timedelta(days=days)]
            return s.iloc[-1] - base.iloc[-1] if len(base) else np.nan
        rows.append({"series": k, "source": ds.macro_src.get(k), "as_of": last.date(), "latest": s.iloc[-1],
                     "chg_1m": ch(30), "chg_3m": ch(91), "chg_1y": ch(365),
                     "2y_high": window(s.to_frame()).iloc[:, 0].max(), "2y_low": window(s.to_frame()).iloc[:, 0].min()})
    return pd.DataFrame(rows)


def _factor_changes(ds):
    m = macro_frame(ds)
    f = pd.DataFrame(index=m.index)
    if "US_10Y" in m: f["us10y"] = m["US_10Y"].dropna().diff()
    if "JGB_30Y" in m: f["jgb30"] = m["JGB_30Y"].dropna().diff()
    if "USDJPY" in m: f["usdjpy"] = m["USDJPY"].dropna().pct_change(fill_method=None)
    return f


def correlations(ds, win: int = 90) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Latest rolling-90-trading-day correlation of LOCAL-currency daily returns with factor changes.

    Local returns are used so the yen factor is not mechanically inside Japanese stocks' USD returns.
    Caveat: Asian/European closes precede US data on the same date (asynchronous trading)."""
    r = daily_returns(ds.prices)
    f = _factor_changes(ds)
    per_co, series = {}, {}
    for tk in r:
        row = {}
        for k in f:
            j = pd.concat([r[tk], f[k]], axis=1, keys=["r", "f"]).dropna()
            roll = j["r"].rolling(win, min_periods=int(win * 0.8)).corr(j["f"])
            row[f"corr90_{k}"] = roll.dropna().iloc[-1] if roll.notna().any() else np.nan
        per_co[tk] = row
    groups = {}
    for b in BUCKET_ORDER:
        members = [t for t in ds.universe[ds.universe.bucket == b].ticker if t in r]
        gr = r[members].mean(axis=1, skipna=True)
        for k in f:
            j = pd.concat([gr, f[k]], axis=1, keys=["r", "f"]).dropna()
            series[(b, k)] = j["r"].rolling(win, min_periods=int(win * 0.8)).corr(j["f"])
    return pd.DataFrame(per_co).T, pd.DataFrame(series)


def event_days(ds, series: str, direction: str, n: int = 10, years: int = 2) -> pd.Series:
    s = ds.macro.get(series)
    if s is None:
        return pd.Series(dtype=float)
    s = window(s.dropna().to_frame(), years).iloc[:, 0]
    ch = s.diff() if series.startswith(("JGB", "US_")) else s.pct_change(fill_method=None)
    ch = ch.dropna()
    return ch.nlargest(n) if direction == "up" else ch.nsmallest(n)


def event_returns(ds, days: pd.Series) -> pd.DataFrame:
    """Same-day local-currency returns of each group and SoftBank on event days."""
    r = daily_returns(ds.prices)
    rows = []
    for d, mv in days.items():
        row = {"date": d.date(), "move": mv}
        for b in BUCKET_ORDER:
            members = [t for t in ds.universe[ds.universe.bucket == b].ticker if t in r]
            row[b] = r.loc[d, members].mean() if d in r.index else np.nan
        row["SoftBank (9984.T)"] = r.loc[d, "9984.T"] if d in r.index and "9984.T" in r else np.nan
        rows.append(row)
    return pd.DataFrame(rows)
