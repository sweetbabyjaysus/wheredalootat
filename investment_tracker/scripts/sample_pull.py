"""Pull everything the pipeline needs for ONE company and print it with sources.

    python scripts/sample_pull.py CRWV
Writes output/sample_<TICKER>.json (values + source + as-of) and lists every gap.
"""
import _path  # noqa: F401
import json
import sys

import pandas as pd

from tracker.config import ROOT, load_settings, load_universe
from tracker.metrics import fundamentals_table
from tracker.provenance import Ledger
from tracker.sources import news, sec, yahoo


def main(ticker: str):
    u, s = load_universe(), load_settings()
    row = u.set_index("ticker").loc[ticker]
    L = Ledger()

    px = yahoo.history(ticker, s["fetch_history_years"], L)
    yahoo.info(ticker, L)
    yahoo.price_metrics(ticker, px, L)
    yahoo.analyst(ticker, L)
    yahoo.put_call(ticker, L)
    yahoo.next_earnings(ticker, L)

    if row.fundamentals_source == "sec":
        q = sec.quarterly(ticker, s["sec_user_agent"], L)
    else:
        q = yahoo.quarterly_statements(ticker, L)
    f = fundamentals_table(q).tail(s["quarters"]) if not q.empty else pd.DataFrame()
    src = "SEC companyfacts" if row.fundamentals_source == "sec" else "yfinance quarterly"
    for d, r in f.iterrows():
        for k, v in r.items():
            if pd.notna(v):
                L.add(ticker, f"q:{k}", float(v), f"computed from {src}", d.date(), note="computed")

    heads = news.headlines(row.company, ticker, s["news_days"])
    for h in heads:
        h["score"], h["rationale"] = news.score_lexicon(h["title"])
    if heads:
        avg = sum(h["score"] for h in heads) / len(heads)
        L.add(ticker, "news_sentiment_30d", round(avg, 3), f"lexicon score over {len(heads)} headlines",
              pd.Timestamp.today().date(), "[-1,1]", "computed")
    else:
        L.gap(ticker, "news_sentiment_30d", "no headlines fetched")

    out = ROOT / "output" / f"sample_{ticker.replace('.', '_')}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps({"ticker": ticker, "data": L.to_records(), "gaps": L.gaps,
                               "headlines": heads}, indent=1, default=str))

    pd.set_option("display.width", 200)
    print(f"=== {row.company} ({ticker}) ===\n")
    snap = pd.DataFrame([d for d in L.to_records() if not d["field"].startswith("q:")])
    print(snap[["field", "value", "unit", "as_of", "source"]].to_string(index=False))
    if not f.empty:
        print("\n--- last quarters (derived) ---")
        cols = ["revenue", "revenue_yoy", "gross_margin", "operating_margin", "fcf", "capex_pct_revenue",
                "net_debt", "net_debt_to_ebitda", "interest_coverage_ttm", "debt_chg_4q"]
        print(f[[c for c in cols if c in f]].T.to_string(float_format=lambda x: f"{x:,.3f}"))
    print(f"\n--- headlines: {len(heads)} (top 5) ---")
    for h in heads[:5]:
        print(f"{h['date']} {h['score']:+.2f} {h['title'][:90]}  [{h['rationale']}]")
    print(f"\n--- data gaps ({len(L.gaps)}) ---")
    for g in L.gaps:
        print(f"{g['field']}: {g['reason']}")
    print(f"\nwritten {out}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "CRWV")
