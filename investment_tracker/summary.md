# Hypothesis tracker - 2026-11-05

_Items marked **Inference** are interpretation, not data._

## Verdicts
- **H1 AI stress hits credit first: Unclear** (2/3 evaluable tests pass; unchanged since 2026-11-04)
  - H1.T1 PASS: Credit - leveraged balance sheets worse and rising, spreads widening 
  - H1.T2 PASS: Drawdown - leveraged group further below 52-week high -0.105 vs < -0.1
  - H1.T3 FAIL: Fundamentals - bottleneck growth holding while multiples compress 
  - Live signals: confirm H1.C1 Credit spreads keep widening (proxy); manual checks: H1.C2, H1.C3, H1.C4, H1.C5, H1.K2
- **H2 Rising US and Japan yields make high-multiple and leveraged AI names fragile: Not supported** (0/3 evaluable tests pass; unchanged since 2026-11-04)
  - H2.T1 FAIL: Rate sensitivity - leveraged more negatively correlated with US 10-year changes -0.0946 vs < -0.1
  - H2.T2 FAIL: Japan transmission - JGB 30y spikes and yen strength line up with leveraged and SoftBank drawdowns 
  - H2.T3 FAIL: Credit spillover - HY spread widening alongside rising long-end yields 
  - Live signals: none auto-detected; manual checks: H2.C2

## Three biggest sentiment-vs-fundamentals divergences (Inference)
- **Nebius (NBIS)**: fundamentals ahead of sentiment; fundamentals z +1.03, sentiment z -0.82.
- **IREN (IREN)**: fundamentals ahead of sentiment; fundamentals z -0.26, sentiment z -1.71.
- **CoreWeave (CRWV)**: fundamentals ahead of sentiment; fundamentals z +0.12, sentiment z -1.11.
- Sentiment moves since 2026-11-04: biggest up Alphabet +0.47, biggest down SK Hynix -1.06.

## Supplier-customer links
- **AVGO -> GOOGL** (supplier): 1y correlation 0.29, beta 0.39; around GOOGL's 2026-10-28 results GOOGL moved -11.5%, AVGO +0.8% (same direction in 62% of the last 8 releases)
- **TSLA -> SPCX** (supplier / affiliate): 1y correlation 0.27, beta 0.16; around SPCX's 2026-10-20 results SPCX moved +7.7%, TSLA +5.0% (same direction in 100% of the last 2 releases)
- **SPCX -> GOOGL** (supplier (compute)): 1y correlation 0.28, beta 0.61; around GOOGL's 2026-10-28 results GOOGL moved -11.5%, SPCX -3.2% (same direction in 100% of the last 2 releases)
- **TSLA -> GOOGL** (competitor (robotaxi vs Waymo)): 1y correlation 0.36, beta 0.47; around GOOGL's 2026-10-28 results GOOGL moved -11.5%, TSLA -1.0% (same direction in 75% of the last 8 releases)

## Evidence screen (top names)

- Sandisk (SNDK): 6/6, +3 vs last run - flags: Very low forward P/E: market may be pricing a cyclical peak; Falling hard: down more than 15% in a month
- SK Hynix (000660.KS): 6/6, +1 vs last run - flags: Very low forward P/E: market may be pricing a cyclical peak; Falling hard: down more than 15% in a month; Target upside above 100%: analyst targets look stale or extreme
- SpaceX (SPCX): 6/6, +1 vs last run - flags: Falling hard: down more than 15% in a month; Negative free cash flow (TTM)
- Samsung Electronics (005930.KS): 6/6 - flags: Very low forward P/E: market may be pricing a cyclical peak; Falling hard: down more than 15% in a month; Target upside above 100%: analyst targets look stale or extreme
- NVIDIA (NVDA): 6/6 - flags: Falling hard: down more than 15% in a month
- Broadcom (AVGO): 5/6
- Changes since last run: SNDK +3, 000660.KS +1, SPCX +1, ASML -1, TSM -1, CRWV +1, LRCX -1, NBIS -1

## Catalysts in the next 30 days
- 2026-11-05: Earnings: IREN (IREN)
- 2026-11-05: Earnings: NuScale Power (SMR)
- 2026-11-06: Earnings: Oklo (OKLO)
- 2026-11-10: Earnings: SoftBank Group (9984.T)
- 2026-11-10: US CPI release
- 2026-11-10: Earnings: CoreWeave (CRWV)
- 2026-11-10: Earnings: Infineon (IFX.DE)
- 2026-11-12: Earnings: Nebius (NBIS)
- 2026-11-12: Earnings: X-energy (XE)
- 2026-11-12: Earnings: Standard Nuclear (STDN)
- 2026-11-17: Earnings: NVIDIA (NVDA)

## Newsletter figures that differ from the data
- IREN: "IREN fell 25% in the sell-off". Data: -12.2% (closest day 2026-10-14; cumulative -22.4%; daily: 10-13 +0.0%, 10-14 -12.2%, 10-15 -0.6%, 10-16 -11.2%)
- MACRO: "US 10-year above 5.2%". Data: 4.95 (US_10Y on 2026-11-03; 1y max 5.31)

Full detail: `tracker.xlsx`; charts in `charts/`.
