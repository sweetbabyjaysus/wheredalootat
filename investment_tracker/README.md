# Investment hypothesis tracker

Research tool, not trading advice. Hypotheses, companies and thresholds live in `config/`;
the code only knows how to fetch data and evaluate the test types listed at the top of
`config/hypotheses.yaml`.

## Status: step 1 (framework + data layer). Analysis, xlsx, charts and `run.py` come next.

## Setup
```bash
pip install -r requirements.txt
export SEC_USER_AGENT="Your Name you@example.com"   # SEC requires a contact email
python scripts/check_connectivity.py                # every source host must be reachable
python scripts/ticker_check.py                      # -> output/ticker_check.csv
python scripts/sample_pull.py CRWV                  # one company, every field with source + as-of
```

Hosts the run needs: query1/query2.finance.yahoo.com, fc.yahoo.com, guce.yahoo.com,
www.sec.gov, data.sec.gov, fred.stlouisfed.org, www.mof.go.jp, www.federalreserve.gov,
www.boj.or.jp, www.bls.gov, news.google.com.

## Config files
| File | What it holds |
| --- | --- |
| `config/universe.csv` | One row per company: bucket (used by tests), group, tickers, exchange, currency, where fundamentals come from (`sec` or `yfinance_quarterly`), fiscal year end, rationale |
| `config/hypotheses.yaml` | Verdict rule, group aliases, hypotheses (tests, confirm/kill signals, catalysts), macro series and their sources |
| `config/claims_to_verify.csv` | Newsletter and premise figures, each with a machine check where possible |
| `config/settings.yaml` | Windows, score weights, news scorer |

## Adding things
- **Company**: add a row to `universe.csv`. If `bucket` is new, add an alias under `groups:`.
- **Hypothesis**: add a block under `hypotheses:` with 2-4 `tests`. The loader validates
  types, operators, groups, tickers and series, and stops on errors.
- **Macro series**: add it under `series:` as `fred:<ID>`, `mof:<tenor>` or `yahoo:<symbol>`.

## Rules the code follows
- Every value is stored with its source and as-of date (`tracker/provenance.py`).
- A missing value is left empty and logged as a gap. Nothing is estimated.
- Computed values (YTD differencing, TTM sums, ratios) are marked `computed`; proxies are marked `proxy`.
