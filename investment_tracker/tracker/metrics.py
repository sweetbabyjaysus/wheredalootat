"""Derived per-quarter metrics. All are computed from sourced inputs; nothing is filled in.

Quarter arithmetic is date-aware: a YoY comparison only uses a quarter ~1 year earlier, and a
TTM sum needs four quarters inside one year, so missing quarters produce blanks, not errors.
"""
from __future__ import annotations

import pandas as pd


def lag(s: pd.Series, quarters: int, tol_days: int = 25) -> pd.Series:
    s = s.dropna()
    out = {}
    for d in s.index:
        target = d - pd.Timedelta(days=round(91.3 * quarters))
        near = s[(s.index >= target - pd.Timedelta(days=tol_days)) & (s.index <= target + pd.Timedelta(days=tol_days))]
        out[d] = near.iloc[0] if len(near) else float("nan")
    return pd.Series(out, dtype=float)


def ttm(s: pd.Series) -> pd.Series:
    s = s.dropna()
    out = {}
    for d in s.index:
        win = s[(s.index > d - pd.Timedelta(days=350)) & (s.index <= d)]
        out[d] = win.sum() if len(win) == 4 else float("nan")
    return pd.Series(out, dtype=float)


def fundamentals_table(q: pd.DataFrame) -> pd.DataFrame:
    """q: quarterly raw fields indexed by period end. Returns derived columns."""
    if q.empty:
        return pd.DataFrame()
    q = q.sort_index().copy()
    idx = q.index
    g = lambda c: q[c] if c in q else pd.Series(index=idx, dtype=float)
    rev = g("revenue")
    gp = g("gross_profit").combine_first(rev - g("cost_of_revenue"))
    ebitda_q = g("operating_income") + g("d_and_a")   # one definition everywhere (vendor EBITDA lines vary)
    cash = g("cash")
    cash_all = cash + g("short_term_investments").fillna(0)
    debt = g("debt_total").add(g("short_term_borrowings"), fill_value=0).where(g("debt_total").notna())
    re_ = lambda s: s.reindex(idx)
    out = pd.DataFrame(index=idx)
    out["revenue"] = rev
    out["revenue_yoy"] = rev / re_(lag(rev, 4)) - 1
    out["gross_margin"] = gp / rev
    out["operating_margin"] = g("operating_income") / rev
    out["net_income"] = g("net_income")
    out["fcf"] = g("cfo") - g("capex")
    out["capex"] = g("capex")
    out["capex_pct_revenue"] = g("capex") / rev
    out["total_debt"] = debt
    out["net_debt"] = debt - cash_all
    out["revenue_ttm"] = re_(ttm(rev))
    out["ebitda_ttm"] = re_(ttm(ebitda_q))
    out["net_income_ttm"] = re_(ttm(g("net_income")))
    out["fcf_ttm"] = re_(ttm(out["fcf"]))
    out["interest_coverage_ttm"] = re_(ttm(g("operating_income"))) / re_(ttm(g("interest_expense").abs()))
    out["fcf_margin_ttm"] = out["fcf_ttm"] / out["revenue_ttm"]
    out["fcf_margin"] = out["fcf"] / rev
    out["net_debt_to_ebitda"] = (out["net_debt"] / out["ebitda_ttm"]).where(out["ebitda_ttm"] > 0)
    out["net_debt_to_ebitda_chg_4q"] = out["net_debt_to_ebitda"] - re_(lag(out["net_debt_to_ebitda"], 4))
    out["debt_chg_4q"] = debt / re_(lag(debt, 4)) - 1
    out["revenue_yoy_chg_2q"] = out["revenue_yoy"] - re_(lag(out["revenue_yoy"], 2))
    out["operating_margin_chg_4q"] = out["operating_margin"] - re_(lag(out["operating_margin"], 4))
    out["maturities_24m"] = g("maturity_next_12m") + g("maturity_year_2")
    return out
