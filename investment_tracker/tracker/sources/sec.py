"""SEC EDGAR companyfacts -> quarterly fundamentals.

10-Q cash-flow items are year-to-date, and Q4 is only in the 10-K, so single quarters are
derived by differencing cumulative facts that share a start date. Derived values are
marked "computed" in the ledger. 20-F filers (ASML, TSM, AER) report semi-annually or
annually in XBRL, so they often have fewer true quarters - recorded as gaps.
"""
from __future__ import annotations

import functools

import pandas as pd
import requests

from ..provenance import Ledger

TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"

# field -> candidate concepts, tried in order, across both taxonomies
CONCEPTS = {
    "revenue": ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "SalesRevenueNet", "Revenue"],
    "gross_profit": ["GrossProfit"],
    "cost_of_revenue": ["CostOfRevenue", "CostOfGoodsAndServicesSold", "CostOfSales"],
    "operating_income": ["OperatingIncomeLoss", "ProfitLossFromOperatingActivities"],
    "net_income": ["NetIncomeLoss", "ProfitLoss", "ProfitLossAttributableToOwnersOfParent"],
    "d_and_a": ["DepreciationDepletionAndAmortization", "DepreciationAndAmortization",
                "DepreciationAmortizationAndAccretionNet", "Depreciation", "DepreciationAndAmortisationExpense"],
    "interest_expense": ["InterestExpense", "InterestExpenseNonoperating", "InterestExpenseDebt", "FinanceCosts"],
    "cfo": ["NetCashProvidedByUsedInOperatingActivities", "CashFlowsFromUsedInOperatingActivities"],
    "capex": ["PaymentsToAcquirePropertyPlantAndEquipment", "PaymentsToAcquireProductiveAssets",
              "PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities"],
    # instants
    "debt_total": ["LongTermDebt", "DebtAndCapitalLeaseObligations", "LongTermDebtAndCapitalLeaseObligations",
                   "DebtInstrumentCarryingAmount"],
    "finance_lease_liability": ["FinanceLeaseLiability"],
    "debt_noncurrent": ["LongTermDebtNoncurrent", "LongTermDebtAndCapitalLeaseObligationsNoncurrent",
                        "NoncurrentPortionOfNoncurrentBorrowings"],
    "debt_current": ["LongTermDebtCurrent", "LongTermDebtAndCapitalLeaseObligationsCurrent",
                     "CurrentPortionOfNoncurrentBorrowings"],
    "short_term_borrowings": ["ShortTermBorrowings", "CommercialPaper", "CurrentBorrowings"],
    "cash": ["CashAndCashEquivalentsAtCarryingValue", "CashAndCashEquivalents"],
    "short_term_investments": ["ShortTermInvestments", "MarketableSecuritiesCurrent",
                               "AvailableForSaleSecuritiesDebtSecuritiesCurrent", "CurrentInvestments"],
    "maturity_next_12m": ["LongTermDebtMaturitiesRepaymentsOfPrincipalInNextTwelveMonths"],
    "maturity_year_2": ["LongTermDebtMaturitiesRepaymentsOfPrincipalInYearTwo"],
}
INSTANT = {"debt_total", "finance_lease_liability", "debt_noncurrent", "debt_current", "short_term_borrowings", "cash",
           "short_term_investments", "maturity_next_12m", "maturity_year_2"}
FORMS = {"10-Q", "10-K", "20-F", "6-K", "40-F", "10-K/A", "10-Q/A", "20-F/A"}


def _session(user_agent: str) -> requests.Session:
    if "@" not in user_agent:
        raise RuntimeError("SEC needs a User-Agent with an email: export SEC_USER_AGENT='Name you@example.com'")
    s = requests.Session()
    s.headers["User-Agent"] = user_agent
    return s


@functools.lru_cache(maxsize=1)
def _cik_map(user_agent: str) -> dict:
    j = _session(user_agent).get(TICKERS_URL, timeout=30).json()
    return {v["ticker"].upper(): int(v["cik_str"]) for v in j.values()}


def cik(ticker: str, user_agent: str):
    return _cik_map(user_agent).get(ticker.upper())


def companyfacts(cik_: int, user_agent: str) -> dict:
    r = _session(user_agent).get(FACTS_URL.format(cik=cik_), timeout=60)
    r.raise_for_status()
    return r.json()


def _facts(cf: dict, concept: str):
    """Return (taxonomy, unit, DataFrame) for the first taxonomy carrying the concept."""
    for tax in ("us-gaap", "ifrs-full"):
        node = cf.get("facts", {}).get(tax, {}).get(concept)
        if not node:
            continue
        unit = next(iter(node["units"]))
        df = pd.DataFrame(node["units"][unit])
        df = df[df["form"].isin(FORMS)]
        if df.empty:
            continue
        for c in ("start", "end", "filed"):
            if c in df:
                df[c] = pd.to_datetime(df[c])
        # latest filing wins for restated periods
        keys = ["start", "end"] if "start" in df else ["end"]
        df = df.sort_values("filed").drop_duplicates(keys, keep="last")
        return tax, unit, df
    return None, None, None


def _quarters_from_durations(df: pd.DataFrame) -> pd.Series:
    """Single-quarter values keyed by period end, from direct 3-month facts or YTD differences."""
    df = df.assign(days=(df["end"] - df["start"]).dt.days)
    direct = df[df.days.between(80, 100)].set_index("end")["val"]
    derived = {}
    for _, g in df.groupby("start"):
        g = g.sort_values("end")
        prev = None
        for _, r in g.iterrows():
            if prev is not None and 80 <= (r["end"] - prev["end"]).days <= 100:
                derived[r["end"]] = r["val"] - prev["val"]
            prev = r
    out = pd.Series(derived, dtype=float)
    out = out[~out.index.isin(direct.index)]
    return pd.concat([direct.astype(float), out]).sort_index(), set(out.index)


def quarterly(ticker: str, user_agent: str, ledger: Ledger, n_quarters: int = 12) -> pd.DataFrame:
    c = cik(ticker, user_agent)
    if c is None:
        ledger.gap(ticker, "sec_cik", "ticker not in SEC company_tickers.json")
        return pd.DataFrame()
    cf = companyfacts(c, user_agent)
    cols = {}
    for field, concepts in CONCEPTS.items():
        # Companies switch tags over time, so coalesce per date in priority order.
        merged, origin = pd.Series(dtype=float), {}
        for concept in concepts:
            tax, unit, df = _facts(cf, concept)
            if df is None:
                continue
            if field in INSTANT:
                s, derived = df.set_index("end")["val"].astype(float).sort_index(), set()
            else:
                if "start" not in df:
                    continue
                s, derived = _quarters_from_durations(df)
            for d in s.index.difference(merged.index):
                origin[d] = (f"SEC companyfacts {tax}:{concept} (CIK {c})", unit,
                             "computed: YTD difference" if d in derived else "")
            merged = s.combine_first(merged) if merged.empty else merged.combine_first(s)
        if merged.empty:
            ledger.gap(ticker, field, f"none of {concepts} in SEC companyfacts")
            continue
        merged = merged.sort_index().iloc[-n_quarters:]
        cols[field] = merged
        for d, v in merged.items():
            src, unit, note = origin[d]
            ledger.add(ticker, f"q:{field}", float(v), src, d.date(), unit, note)
    out = pd.DataFrame(cols).sort_index()
    if "debt_total" not in out and {"debt_noncurrent", "debt_current"} & set(out):
        out["debt_total"] = out.get("debt_noncurrent", 0).fillna(0) + out.get("debt_current", 0).fillna(0)
    if "revenue" in out and out["revenue"].notna().sum() < 8:
        ledger.gap(ticker, "fundamentals_quarters",
                   f"SEC XBRL gives {int(out['revenue'].notna().sum())} quarterly revenue points "
                   "(20-F filers report semi-annually; recent IPOs/spin-offs have short history)")
    return out
