# Investment hypothesis tracker

Research tool for testing investment hypotheses against market, filing and macro data.

Hypotheses, companies and thresholds live in `config/`. The code only fetches data and evaluates
the test types listed at the top of `config/hypotheses.yaml`, so new ideas don't need code changes.

## Run it

```bash
pip install -r requirements.txt
export SEC_USER_AGENT="Your Name you@example.com"   # SEC requires a contact email
python scripts/check_connectivity.py                # optional: every source host must answer
python run.py                                       # one command, about 5-10 minutes on a cold cache
```

Each run writes:

| Output | What it is |
| --- | --- |
| `tracker.xlsx` | Summary, Hypothesis scorecard, Group comparison, Group returns USD-THB, Companies, Trends, Sentiment matrix, Sentiment trend, Yields and FX, Rate correlations, Event study, Newsletter claims, Catalyst calendar, Headlines, Raw data, Data gaps and sources |
| `charts/*.png` | Group indexes (USD and THB), sentiment vs fundamentals, yields vs the leveraged group, USD/JPY vs SoftBank |
| `snapshots/YYYY-MM-DD.json` | Key metrics, scores and verdicts. The next run compares against the latest earlier snapshot |
| `summary.md` | One page: verdicts and changes, top divergences, the next 30 days of catalysts, newsletter figures the data contradicts |

Responses are cached per day in `output/cache/` (ignored by git), so a second run the same day is fast.
Delete today's cache folder to force fresh data.

## Add a company

Add a row to `config/universe.csv`:

- `bucket`: the comparison group the tests use (Bottleneck, Compute leader, Hyperscaler, Leveraged buildout, or a new one).
- `ticker`: the main Yahoo symbol. `alt_tickers`: other listings, separated by `;`.
- `fundamentals_source`: `sec` if the company files 10-Q/10-K with XBRL, otherwise `yfinance_quarterly`.

A new bucket also needs an alias under `groups:` in `hypotheses.yaml` before tests can refer to it.
Run `python scripts/ticker_check.py` to confirm the symbol, exchange and currency.

## Add a supplier-customer link

Add a row to `config/relationships.csv` (supplier, customer, relationship, evidence, source_url, as_of).
Both tickers must be in `universe.csv`. Each run reports, in the `Relationships` and
`Relationship events` tabs:
- 90-day and 1-year correlation and beta of supplier returns on customer returns.
- The supplier's move around each of the customer's last 8 earnings releases. Dates come from
  the customer's SEC 8-K Item 2.02 filings, and the window runs from the close before the filing to
  the close after it. US filers only.

## Add a hypothesis

Add a block under `hypotheses:` in `config/hypotheses.yaml` with `id`, `name`, `statement`, 2-4
`tests`, `confirm_signals`, `kill_signals` and `catalysts`. Each test is one of:

| type | Meaning |
| --- | --- |
| `group_value` | median of `metric` across `group` `op` `threshold` |
| `group_diff` | median(`metric`, `group_a`) - median(`metric`, `group_b`) `op` `threshold` |
| `series_change` / `series_change_pct` | change in a macro `series` over `window_days` |
| `series_level` | latest value of a macro series |
| `event_mean` | mean same-day return of a `group` or `ticker` on the `n` largest moves of `event.series` in `event.direction`; optional `relative_to` group |
| `all_of` | list of `conditions`; pass only if all pass |
| `kind: manual` | can't be checked from free data; listed as "check by hand" |

The loader validates types, operators, group aliases, tickers and series, and stops with a clear
error. The verdict rule (`verdict_rule:`) counts the tests that have data: Supported at >= 75% passing,
Not supported at <= 34%, otherwise Unclear, and Unclear if fewer than 2 tests have data.
A hypothesis can override the rule.

To add a macro series, put it under `series:` as `fred:<ID>`, `mof:<tenor>` or `yahoo:<symbol>`.
Sources are tried in order, and a fallback is logged as a data gap.

### Metric names usable in tests

Prices: `ret_1m`, `ret_3m`, `ret_ytd`, `ret_1y`, `pct_from_52w_high`, `pct_vs_200dma`.
Valuation: `forward_pe`, `ev_ebitda_yf`, `ev_sales_yf`, `ev_sales_ttm`, `ev_ebitda_ttm`, `pe_ttm`,
`ev_sales_vs_3y_avg`, `ev_ebitda_vs_3y_avg`, `pe_vs_3y_avg`.
Fundamentals (latest quarter): `revenue_yoy`, `revenue_yoy_chg_2q`, `gross_margin`, `operating_margin`,
`operating_margin_chg_4q`, `fcf_margin_ttm`, `capex_pct_revenue`, `net_debt_to_ebitda`,
`net_debt_to_ebitda_chg_4q`, `interest_coverage_ttm`, `debt_chg_4q`, `maturities_24m`.
Sentiment: `analyst_rating_mean`, `target_upside`, `eps_revision_30d`, `eps_revision_90d`,
`short_pct_float`, `put_call_volume`, `news_sentiment`.
Rates: `corr90_us10y`, `corr90_jgb30`, `corr90_usdjpy`.

## Data sources and how they're combined

| Data | Source |
| --- | --- |
| Prices, info, analyst ratings and targets, EPS trend, short interest, options, earnings dates, recent quarterly statements | yfinance |
| US filer fundamentals | SEC EDGAR companyfacts (XBRL). Year-to-date filings are turned into single quarters by differencing, marked `computed` |
| Non-US fundamentals | yfinance (latest ~5 quarters) + `data/fundamentals_manual.csv` (backfilled from filings, each row with its document URL) + `data/fundamentals_store.csv` (every yfinance quarter seen on earlier runs, so history builds up) |
| US rates, breakevens, HY spread, Fed target, CPI, diesel, Brent | FRED |
| JGB yields | Japan Ministry of Finance JGB yield CSV (FRED monthly only as fallback) |
| FX | Yahoo `JPY=X`, `THB=X`, etc. |
| FOMC / BoJ / CPI dates | federalreserve.gov, boj.or.jp, FRED's copy of the BLS CPI schedule (bls.gov blocks scripts) |
| News | Google News RSS + yfinance news, scored with a transparent word list (each headline keeps the matched words) |

Rules the code follows:

- Every value is stored with its source and as-of date (`Raw data` tab).
- A missing value is left empty and logged in `Data gaps and sources`. Nothing is estimated.
- Values derived from others (YTD differences, TTM sums, ratios, z-scores) are marked `computed`. Proxies are labelled as proxies.
- For each company and field, the source with the most quarters is the backbone. Other sources only
  fill dates it lacks, and each value keeps its own source.

## Method notes (read before interpreting)

- **Group index**: equal money in each member at the start (buy-and-hold), rebalanced only when a
  new member lists. Daily rebalancing was rejected because with volatile members it inflates
  returns. The leveraged group would show about 4.9x instead of 3.0x over two years.
- **Group comparison** uses medians across members. A test needs at least half the members (min 2) to have data.
- **EBITDA** = operating income + D&A for every company. Vendor "EBITDA" lines include one-off gains.
- **Net debt** = total debt (excl. leases where the source separates them) - cash - short-term investments.
- **Trailing multiples vs 3-year average** use quarter-end EV = price x shares (listing in the
  reporting currency, so no ADR ratio issues) + net debt. Forward P/E has no free history, so its
  3-year average is a logged gap.
- **EPS revisions** use the next-fiscal-year consensus (yfinance `+1y`) as the 12-month proxy,
  divided by the absolute value so a cut is negative even when EPS is negative.
- **Rate correlations and event studies** use local-currency returns, so yen moves aren't
  mechanically inside Japanese stocks' USD returns. Asian and European closes come before US data on the same date.
- **Sentiment score** = z-score blend of analyst rating (inverted), 90-day EPS revision, short interest (inverted) and news.
  **Fundamentals-momentum score** = z-blend of revenue YoY, 4-quarter operating-margin change and TTM FCF margin.
  Both need at least 2 inputs. The divergence flags are **inference**, not data.
- **Credit spreads**: there's no free feed of neocloud bond spreads, so the ICE BofA US HY OAS is used as a labelled proxy.
