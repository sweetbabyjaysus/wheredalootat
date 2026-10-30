# "The Google Capital Company": Ben Thompson, Stratechery, 2026-06-02

Source: https://stratechery.com/2026/the-google-capital-company/ (free essay, read in full on 2026-10-30).
Figures below come from Alphabet's 8-K results releases (Q1, Q2, Q3 2026) and the tracker's price data.
Lines marked **Inference** are interpretation, not data. Research only, not trading advice.

## The argument in brief

- Google Services is the "most beautiful business model of all time": free supply, advertisers
  bidding up prices, high margins, very little capital needed. In Buffett's terms it's **See's Candies**.
- Google Cloud is the capital-hungry business, like **BNSF Railway**. Its margins are lower, but
  its absolute profits could be far larger, because AI could reach much more of the economy than advertising does.
- The trigger was Alphabet's **$80bn equity package**: a $40bn at-the-market (ATM) program, $30bn of
  underwritten shares and mandatory convertible preferred, and $10bn from Berkshire Hathaway.
- **Why equity rather than debt?** Thompson gives two readings and a test to tell them apart:
  - Bull (his "Occam's Razor"): demand for compute is underestimated, so Google will also issue a lot more debt.
  - Bear: Google is unsure about the return on its capex and wants to share the risk.
  - Test: "If there isn't a substantial debt issuance down the road then this might be the right answer"
    (the bear one).
- **Why Google?** It has optionality across Services, Gemini and selling capacity to frontier labs. Its
  TPUs give it a lasting cost advantage, so if compute becomes a commodity, Google is "poised to
  make the most profit".
- **Big picture:** if compute runs short, whoever brings the most cash gets the most compute, and that
  advantage compounds. Berkshire is betting that this company is Google.

## Scorecard against the data (tracked in `config/claims_to_verify.csv`, prefix `STRAT_`)

| Claim | What the data shows | Status |
| --- | --- | --- |
| Debt ~$81bn vs ~$126bn cash (before the raise) | Total debt $80.3bn at 2026-03-31; cash and securities $126.8bn at 2025-12-31 | Matches |
| Q1 2026: Services $89.6bn revenue / $40.6bn profit; Cloud $20.0bn / $6.6bn | Exactly as in the Q1 2026 8-K | Matches |
| $40bn ATM starting in Q3 | Q3: $12.4bn issued, $27.6bn remaining, so a $40bn program. 6.25% mandatory convertible preferred outstanding | Matches |
| Bull test: "a lot more debt" | Total debt $80.3bn -> $127.5bn (+59%) from March to September; $28.7bn of notes issued in Q3 | Bull reading, by his own test |
| Cloud margins worse but rising faster | Gap between Services and Cloud margins: 12.3pp (Q1) -> 6.2pp (Q2) -> 4.5pp (Q3) | Holding |
| Berkshire bought near the high | June 1 close $375.90, 6.5% below the $402.12 high (May 13) | Matches |

### Cloud is catching up with Services (8-K segment tables)

| Quarter | Services margin | Cloud margin | Cloud revenue as % of Services | Cloud profit as % of Services |
| --- | --- | --- | --- | --- |
| Q1 2026 | 45.3% | 32.9% | 22% | 16% |
| Q2 2026 | 41.8% | 35.6% | 26% | 22% |
| Q3 2026 | 40.7% | 36.2% | 32% | 28% |

Services margins usually peak in Q1, so compare year on year: Q3 Services margin was 40.7%, against 38.5% in Q3 2025.

## What the market says (Q3 results, 2026-10-28)

- GOOGL is down 24.5% since Berkshire's deal (June 1 close $375.90 -> $283.82 on Oct 29), including
  a 12.6% one-day drop, its worst ever.
- Free cash flow turned negative (Q2 -$5.9bn, Q3 -$9.1bn) as Q3 capex reached $51.4bn, 40% of revenue.
- **Inference:** the market is valuing Google more like the railway and less like See's Candies.
  Thompson welcomes that shift; the market has so far been discounting it. The data backs the
  operating half of his thesis: Cloud is scaling, margins are converging, and debt issuance came as
  his bull case predicted. What isn't proven yet is the return on capital: no free cash flow, and
  external funding of about $41bn in Q3 alone (debt plus ATM).
- **Inference (Berkshire):** at the June 1 close, a $10bn stake would be worth about $7.5bn now. Berkshire's
  actual purchase price wasn't disclosed in the sources read, so this is an approximation.

## What would settle it

- **For the thesis:** Cloud margins pass Services; Cloud profit keeps rising as a share of Services;
  TPU capacity sold to outside labs (e.g. Anthropic via Broadcom; see `config/relationships.csv`).
- **Against it:** free cash flow stays negative after the 2027 capex step-up; Cloud margins stall;
  more equity raised beyond the $40bn ATM; outside TPU demand depends on one customer's
  "continued commercial success" (Broadcom 8-K language about Anthropic).

## Implication for H1 (Inference)

H1 puts Alphabet in the "cash-rich hyperscaler" group as the safe side of the trade. On Thompson's
framing, and on the Q3 balance sheet (debt up 59% in six months, equity being issued, free cash flow
negative), Google is moving toward the debt-funded builder model, though from a position of net cash.
Consider whether it still belongs in a separate bucket from the leveraged buildout layer.
