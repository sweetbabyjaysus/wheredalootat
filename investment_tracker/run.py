"""Re-run everything:  python run.py

Fetches data, scores the hypotheses in config/hypotheses.yaml and writes:
  tracker.xlsx, charts/*.png, snapshots/YYYY-MM-DD.json, summary.md
"""
import datetime as dt
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from tracker import analysis, claims, relationships, report, scorecard, screen  # noqa: E402
from tracker.config import ROOT, load_claims, load_hypotheses, load_settings, load_universe  # noqa: E402
from tracker.dataset import build  # noqa: E402


def previous_snapshot(today: str):
    snaps = sorted(p for p in (ROOT / "snapshots").glob("*.json") if p.stem < today)
    return json.loads(snaps[-1].read_text()) if snaps else None


def main():
    today = dt.date.today().isoformat()
    universe, hyp, settings = load_universe(), load_hypotheses(), load_settings()
    if "@" not in settings["sec_user_agent"]:
        print("WARNING: SEC_USER_AGENT not set (needs an email); SEC fundamentals will be gaps.")
    print("Fetching data...")
    ds = build(universe, hyp, settings)
    L = ds.ledger

    print("Analysing...")
    ct = analysis.company_table(ds)
    corr_co, corr_series = analysis.correlations(ds)
    ct = ct.join(corr_co)
    for tk, r in corr_co.iterrows():
        for k, v in r.items():
            L.add(tk, k, v, "computed: rolling 90d corr of local daily returns vs factor change", today, note="computed")
    prev = previous_snapshot(today)
    sc = analysis.scores(ct, settings)
    st = analysis.sentiment_trend(sc, prev)
    gc = analysis.group_comparison(ct)
    gr = analysis.group_return_table(ds)
    tr = analysis.trends(ds)
    mc = analysis.macro_changes(ds)
    results = scorecard.run(ds, ct, hyp, prev)
    cl = claims.check(load_claims(), ds)
    rel_sum, rel_events = relationships.analyse(ds, settings, L)
    scr = screen.run(ct, sc, prev)

    ev_tables = []
    for series, direction, label in (("JGB_30Y", "up", "10 largest JGB 30y up-days (move in pp)"),
                                     ("USDJPY", "down", "10 largest yen-strength days (USD/JPY % move)"),
                                     ("US_10Y", "up", "10 largest US 10y up-days (move in pp)")):
        days = analysis.event_days(ds, series, direction)
        e = analysis.event_returns(ds, days)
        if len(e):
            e.insert(0, "event", label)
            avg = e.drop(columns=["event", "date"]).mean(numeric_only=True)
            ev_tables.append(pd.concat([e, pd.DataFrame([{"event": label, "date": "AVERAGE", **avg}])]))
    events = pd.concat(ev_tables) if ev_tables else pd.DataFrame()

    cal = pd.DataFrame(ds.calendar)
    earn = pd.DataFrame([{"event": f"Earnings: {r['company']} ({tk})", "date": r["next_earnings"],
                          "detail": "yfinance (may be estimated)", "source": "yfinance"}
                         for tk, r in ds.snapshot.items() if r.get("next_earnings")])
    tsmc = [{"event": "TSMC monthly revenue (approx. date, verify)", "date": d.date().isoformat(),
             "detail": "TSMC usually reports around the 10th; date is an assumption", "source": "manual"}
            for d in pd.date_range(today, periods=3, freq="MS") + pd.Timedelta(days=9)]
    cal = pd.concat([cal, earn, pd.DataFrame(tsmc)], ignore_index=True).sort_values("date")
    upcoming = cal[(cal.date >= today)]
    next30 = upcoming[upcoming.date <= (dt.date.today() + dt.timedelta(days=30)).isoformat()]

    print("Writing outputs...")
    asof = today
    chart_paths = report.charts(ds, sc, ROOT / "charts", asof)
    (ROOT / "snapshots").mkdir(exist_ok=True)
    report.snapshot(ROOT / "snapshots" / f"{today}.json", today, results, ct, sc, mc, scr)
    report.summary_md(ROOT / "summary.md", today, results, sc, next30, cl, st, rel_sum, scr)

    summary_tab = pd.DataFrame(
        [{"item": f"{h['id']} verdict", "value": h["verdict"], "detail": f"{h['why']}; previous: {h['prev_verdict'] or 'n/a'}"} for h in results]
        + [{"item": "Companies", "value": len(universe), "detail": ", ".join(universe.ticker)},
           {"item": "Data gaps logged", "value": len(L.gaps), "detail": "see 'Data gaps and sources'"},
           {"item": "Previous snapshot", "value": prev["date"] if prev else "none", "detail": ""},
           {"item": "Charts", "value": len(chart_paths), "detail": ", ".join(p.name for p in chart_paths)}]
        + [{"item": f"Catalyst {r.date}", "value": r.event, "detail": r.detail} for r in next30.itertuples()])
    co_cols = ["company", "bucket", "group", "currency", "price", "ret_1m", "ret_3m", "ret_ytd", "ret_1y",
               "pct_from_52w_high", "pct_vs_200dma", "market_cap_usd", "enterprise_value_usd", "forward_pe",
               "ev_ebitda_yf", "ev_sales_yf", "ev_sales_ttm", "ev_sales_ttm_3y_avg", "ev_sales_vs_3y_avg",
               "ev_ebitda_ttm", "ev_ebitda_ttm_3y_avg", "ev_ebitda_vs_3y_avg", "pe_ttm", "pe_ttm_3y_avg", "pe_vs_3y_avg",
               "revenue_yoy", "gross_margin", "operating_margin", "fcf_margin_ttm", "capex_pct_revenue",
               "net_debt", "net_debt_to_ebitda", "net_debt_to_ebitda_chg_4q", "interest_coverage_ttm",
               "debt_chg_4q", "maturities_24m", "analyst_rating_key", "analyst_rating_mean", "analyst_count",
               "target_mean_price", "target_upside", "eps_revision_30d", "eps_revision_90d", "short_pct_float",
               "put_call_volume", "put_call_oi", "news_sentiment", "news_count", "next_earnings",
               "corr90_us10y", "corr90_jgb30", "corr90_usdjpy"]
    company = ct[[c for c in co_cols if c in ct]]
    sources = pd.DataFrame(L.to_records()).groupby("source").agg(fields=("field", "nunique"), values=("value", "size"),
                                                                 latest_as_of=("as_of", "max")).reset_index()
    gaps = pd.DataFrame(L.gaps)
    gaps_src = pd.concat([gaps.assign(table="DATA GAP"),
                          sources.rename(columns={"source": "reason"}).assign(table="SOURCE")], ignore_index=True)
    heads = pd.DataFrame([{**h, "ticker": tk} for tk, hs in ds.headlines.items() for h in hs])
    corr_latest = corr_series.ffill().iloc[[-1]].T.reset_index()
    corr_latest.columns = ["group", "factor", "corr90_latest"]

    yf_src = "yfinance (prices, info, analyst, options, earnings dates); SEC EDGAR companyfacts; data/fundamentals_*.csv"
    report.workbook(ROOT / "tracker.xlsx", [
        ("Summary", summary_tab, "Summary", "all sources below", asof),
        ("Hypothesis scorecard", report.scorecard_frame(results), "Hypothesis scorecard",
         "config/hypotheses.yaml tests evaluated on this run's data", asof),
        ("Screen", scr, "Evidence screen (config/screen.yaml): strongest case on paper. NOT a forecast or recommendation",
         "Companies + Sentiment matrix tabs; change = vs previous snapshot", asof, True),
        ("Group comparison", gc, "Group medians by bucket (n_ = members with data)", yf_src, asof, True),
        ("Group returns USD-THB", gr, "Group index returns in USD and THB", "yfinance closes; Yahoo THB=X", asof),
        ("Companies", company, "Company snapshot", yf_src, asof, True),
        ("Trends", tr, "Quarterly trends vs price change in the quarter (local currency)", yf_src, asof),
        ("Sentiment matrix", sc, "Sentiment vs fundamentals-momentum (z-scores; flags are inference)", yf_src + "; Google News RSS", asof, True),
        ("Sentiment trend", st, "Sentiment score vs previous snapshot", "snapshots/*.json", asof, True),
        ("Yields and FX", mc, "US & Japan yields, spreads, FX, oil (changes in series units)",
         "FRED; Japan MoF JGB CSV; Yahoo FX", asof),
        ("Rate correlations", corr_latest, "Latest rolling-90d correlation: group local returns vs factor changes",
         "computed from yfinance + FRED + MoF + Yahoo FX", asof),
        ("Event study", events, "Same-day local-currency group returns on the largest macro-move days",
         "computed from yfinance + MoF + Yahoo FX", asof),
        ("Relationships", rel_sum, "Supplier-customer links (config/relationships.csv) vs price behaviour",
         "relationship text: SEC 8-K filings (see sources column); prices: yfinance", asof),
        ("Relationship events", rel_events, "Supplier move around each customer earnings release (2-day window)",
         "customer SEC 8-K Item 2.02 dates; yfinance closes", asof),
        ("Newsletter claims", cl, "Newsletter and premise figures checked against data", "config/claims_to_verify.csv", asof),
        ("Catalyst calendar", upcoming, "Upcoming catalysts", "federalreserve.gov; boj.or.jp; FRED (BLS CPI schedule); yfinance", asof),
        ("Headlines", heads, "News headlines scored (lexicon)", "Google News RSS; yfinance news", asof),
        ("Raw data", pd.DataFrame(L.to_records()), "Every value with source and as-of", "see source column", asof),
        ("Data gaps and sources", gaps_src, "Data gaps (left empty, never estimated) and sources used", "run ledger", asof),
    ])
    print(f"Done. {len(L.data)} values, {len(L.gaps)} gaps.")
    for h in results:
        print(f"  {h['id']}: {h['verdict']} ({h['why']})")


if __name__ == "__main__":
    main()
