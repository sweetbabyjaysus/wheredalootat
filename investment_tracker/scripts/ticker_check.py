"""Check every ticker in universe.csv resolves on yfinance and matches the config.

Writes output/ticker_check.csv. Flags: unknown ticker, currency/exchange mismatch,
name mismatch, history shorter than 2 years, SEC CIK presence for `sec` rows.
"""
import _path  # noqa: F401
import datetime as dt
import re

import pandas as pd
import yfinance as yf

from tracker.config import ROOT, load_settings, load_universe
from tracker.sources import sec

# yfinance exchange codes -> our labels
EXCH = {"NMS": "NASDAQ", "NGM": "NASDAQ", "NCM": "NASDAQ", "NYQ": "NYSE", "KSC": "KRX", "JPX": "TSE",
        "TYO": "TSE", "GER": "XETRA", "ETR": "XETRA", "TAI": "TWSE", "AMS": "AEX", "PNK": "OTC"}


def norm(s):
    return set(re.findall(r"[a-z]{3,}", s.lower())) - {"inc", "ltd", "corp", "co", "group", "holdings", "the", "plc"}


def main():
    u, settings = load_universe(), load_settings()
    rows, two_years_ago = [], dt.date.today() - dt.timedelta(days=730)
    for _, r in u.iterrows():
        for tk in [r.ticker] + [t for t in r.alt_tickers.split(";") if t]:
            primary = tk == r.ticker
            row = {"company": r.company, "ticker": tk, "primary": primary, "issues": []}
            try:
                info = yf.Ticker(tk).info or {}
                hist = yf.Ticker(tk).history(period="2y")
            except Exception as e:
                info, hist = {}, pd.DataFrame()
                row["issues"].append(f"fetch error {type(e).__name__}")
            if not info.get("regularMarketPrice") and hist.empty:
                row["issues"].append("NOT FOUND on yfinance")
            row.update(yf_name=info.get("longName"), yf_exchange=EXCH.get(info.get("exchange"), info.get("exchange")),
                       yf_currency=info.get("currency"), quote_type=info.get("quoteType"),
                       last_price=info.get("regularMarketPrice"),
                       first_bar=hist.index[0].date().isoformat() if not hist.empty else None)
            if primary:
                if row["yf_currency"] and row["yf_currency"] != r.currency:
                    row["issues"].append(f"currency {row['yf_currency']} != config {r.currency}")
                if row["yf_exchange"] and row["yf_exchange"] != r.exchange:
                    row["issues"].append(f"exchange {row['yf_exchange']} != config {r.exchange}")
                if row["yf_name"] and not (norm(row["yf_name"]) & norm(r.company)):
                    row["issues"].append(f"name '{row['yf_name']}' does not match '{r.company}'")
                if row["first_bar"] and dt.date.fromisoformat(row["first_bar"]) > two_years_ago + dt.timedelta(days=7):
                    row["issues"].append(f"history starts {row['first_bar']} (<2y)")
                if r.fundamentals_source == "sec":
                    try:
                        c = sec.cik(tk, settings["sec_user_agent"])
                        row["sec_cik"] = c
                        if c is None:
                            row["issues"].append("no SEC CIK; switch fundamentals_source")
                    except Exception as e:
                        row["issues"].append(f"SEC lookup failed: {str(e)[:60]}")
            row["issues"] = "; ".join(row["issues"]) or "OK"
            rows.append(row)
    df = pd.DataFrame(rows)
    out = ROOT / "output" / "ticker_check.csv"
    out.parent.mkdir(exist_ok=True)
    df.to_csv(out, index=False)
    with pd.option_context("display.width", 200, "display.max_colwidth", 70):
        print(df[["company", "ticker", "yf_name", "yf_exchange", "yf_currency", "first_bar", "issues"]].to_string(index=False))
    print(f"\nwritten {out}")


if __name__ == "__main__":
    main()
