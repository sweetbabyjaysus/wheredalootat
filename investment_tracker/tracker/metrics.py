"""Derived per-quarter metrics. All are computed from sourced inputs; nothing is filled in."""
from __future__ import annotations

import pandas as pd


def fundamentals_table(q: pd.DataFrame) -> pd.DataFrame:
    """q: quarterly raw fields indexed by period end. Returns raw + derived columns."""
    q = q.sort_index().copy()
    g = lambda c: q[c] if c in q else pd.Series(index=q.index, dtype=float)
    rev = g("revenue")
    gp = g("gross_profit")
    if gp.isna().all() and "cost_of_revenue" in q:
        gp = rev - q["cost_of_revenue"]
    ttm = lambda s: s.rolling(4, min_periods=4).sum()
    ebitda_q = g("ebitda") if "ebitda" in q else g("operating_income") + g("d_and_a")
    cash = g("cash").fillna(0) + g("short_term_investments").fillna(0)
    debt = g("debt_total").fillna(0) + g("short_term_borrowings").fillna(0)
    debt = debt.where(g("debt_total").notna() | g("short_term_borrowings").notna())
    out = pd.DataFrame({
        "revenue": rev,
        "revenue_yoy": rev / rev.shift(4) - 1,
        "gross_margin": gp / rev,
        "operating_margin": g("operating_income") / rev,
        "fcf": g("cfo") - g("capex"),
        "capex": g("capex"),
        "capex_pct_revenue": g("capex") / rev,
        "total_debt": debt,
        "net_debt": debt - cash.where(g("cash").notna()),
        "ebitda_ttm": ttm(ebitda_q),
        "interest_coverage_ttm": ttm(g("operating_income")) / ttm(g("interest_expense").abs()),
    })
    out["fcf_margin"] = out["fcf"] / rev
    out["net_debt_to_ebitda"] = (out["net_debt"] / out["ebitda_ttm"]).where(out["ebitda_ttm"] > 0)
    out["net_debt_to_ebitda_chg_4q"] = out["net_debt_to_ebitda"] - out["net_debt_to_ebitda"].shift(4)
    out["debt_chg_4q"] = out["total_debt"] / out["total_debt"].shift(4) - 1
    out["revenue_yoy_chg_2q"] = out["revenue_yoy"] - out["revenue_yoy"].shift(2)
    out["operating_margin_chg_4q"] = out["operating_margin"] - out["operating_margin"].shift(4)
    return out
