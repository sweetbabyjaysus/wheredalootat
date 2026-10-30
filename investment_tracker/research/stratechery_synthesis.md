# Stratechery vs. our analysis: synthesis (2026-10-30)

**Scope.** I indexed all 2,974 posts on stratechery.com through its public API (`data/stratechery_index.csv`;
the ranked list is in `stratechery_digest.md`). I read 16 free articles and interviews in full, from Nov 2025 to Oct 2026, plus
"The Google Capital Company" (see `thompson_google_capital_company.md`). Paid Updates are judged on title and teaser
only. Quotes are short and taken from the text. Lines marked **Inference** are interpretation. Research only, not trading advice.

## The one-paragraph version

Over the year Thompson's worry moved from *demand* to *financing*. Nov 2025: "this is a bubble", a
beneficial one. Mar 2026: "I don't think we're in a bubble". Aug 2026: a "danger zone" as hyperscalers
"blow through the debt markets". Sep 2026: "there is a limit to available capital, and finding that limit will end badly
for everyone depending on outside capital." That is H1's mechanism, stress showing up in credit first, in his
own words. Two things complicate H1 as we've set it up, though: (1) Alphabet is no longer self-funding, and (2) the
bottleneck vendors themselves (Nvidia, and on our reading Broadcom) are taking on the buildout's credit risk. He
says nothing about rates, JGBs or the yen, so H2 gets no support from this source.

## H1: AI stress hits credit first

**Supports**
- Credit stress has been visible since August: "spreads are rising, and 86% of the bonds issued this year are already trading at
  higher yields than at issuance". Cover for new issues "has fallen to less than 2x, from 5x in February".
  Hyperscaler issuance: $108bn in all of 2025, $194bn by July 7, 2026. *Nvidia's Risky Business, 2026-08-11*
- Risk is building out of sight: the risk is "unmarked, unlike equity" and "considerably higher". *2026-08-11*
- Dot-com precedent: "the loss was mostly equity, not debt. Where debt was a problem was in telecom." That maps to
  our debt-funded builders. *The Benefits of Bubbles, 2025-11-05*
- Neoclouds are named as dependent on revenue that hasn't arrived: "both Anthropic and OpenAI and the hyperscalers and neoclouds
  need AI revenue to increase dramatically." *Frontier Overhangs, 2026-09-21*
- Collateral risk: GPUs are depreciated over five years, "and that may be generous". That matters for neocloud collateral and lease
  residual values. *2025-11-05*

**Complicates**
- **Bottleneck vendors carry credit risk too.** Nvidia offers "up to 25% residual-value based financing" and $500bn
  financing platforms. This "preserves Nvidia's margins by finding new pools of capital willing to bear risk". *2026-08-11*
  **Inference:** Broadcom's ~$43bn AI-rack lease backstop (8-K, 2026-10-27) has the same shape. The "bottleneck"
  group isn't insulated from a credit event.
- **In the near term neoclouds have pricing power, not distress:** Anthropic will buy compute from "hyperscalers and neoclouds,
  and paying dearly for the privilege". *Mythos, Muse, 2026-04-13*. Neoclouds also appear as TPU buyers.
  *Google, Nvidia, and OpenAI, 2025-12-01*
- **H1's kill signal (hyperscalers cut capex) appears nowhere in a year of posts:** "there is no sign of anyone slowing
  down" (Nov 2025); capex plans "blow away expectations" (Mar 2026); "The CapEx Train Keeps Rolling" (Aug 2026).

## Which bottlenecks last (H1's bottleneck group)

| Bottleneck | Thompson / interviewees | Durability |
| --- | --- | --- |
| **TSMC leading edge** | "the TSMC brake isn't going anywhere — if anything, it's being pressed harder than ever" (Jan 2026); new fabs add "almost none" in 2026, with real capacity in 2028-29; relief only from Samsung/Intel competition | Most durable |
| **Power / turbines / siting** | Power was "so far, so good" in January. By May "one of the biggest constraints is not just power (expected), but zoning (unexpected)"; turbine makers don't build ahead (Arm's Haas, Mar 2026) | Durable, slow-moving |
| **Memory / HBM** | Most acute in March ("if there was more memory could we sell more? Yes"; Sandisk "bananas"), but Haas expects "the memory will be solved". Thompson (May): agentic inference favours "slower and cheaper memory — like traditional DRAM", a direct risk to HBM pricing | Most likely to be relieved |
| **Compute pricing overall** | "a price umbrella that is downstream of the lack of compute" (Sep 2026): prices compress once supply catches up | Risk to H1.T3 ("revenue holding") |

The binding constraint moved over the year: chips (Jan) → memory (Mar) → power and zoning (May) → **capital**
(Jun to Sep). **Inference:** our bottleneck basket trades about 22% above its 3-year average EV/sales on the chip and
memory constraints. Thompson's latest view is that the binding constraint is now capital, which no company in the basket supplies.

## Alphabet

- **Thesis support:** Google is "the hyperscaler that is poised to make the most profit" (TPU cost advantage). He repeated this
  in August after the equity raise. Kurian (Apr 2026): 16bn tokens a minute, up from 10bn in Dec/Jan; Broadcom is the
  "partner who manufactures the TPUs with us"; "there's always a shortage, there's never enough".
- **Funding:** "Microsoft, alone amongst the hyperscalers, still boasts substantial free cash flow". Google is
  "bringing everything to bear — first its cash flow, then its debt, and now its equity" (Aug 2026). That matches Q3:
  negative FCF, $28.7bn of bonds and $12.4bn of shares sold through the at-the-market program. His equity figure moved from $80bn (June, quoting Bloomberg) to $85bn (August).
- **Capex justified?** February: "Google's plans make perfect sense given the nature of the business and their results". April: questions
  about the capex "feel like… completely erased". None of the free posts cover the Q3 sell-off. The paid Update
  "Anthropic S-1, The Cost of Compute, Who Is Paying?" (Oct 27) is the closest and is teaser-only.
- **Search:** AI's threat to Search is acknowledged (Dec 2025), but Google is already monetising AI Overviews. The Oct 26 essay "The End
  of the Internet" argues AI takes content "without giving any of the traffic back that Google did". That is a long-run risk to
  the open web Search depends on. Q3 Search +12% fits "not yet".
- **Kurian's counterpoint:** TPUs placed in customers' own data centres "drive cash flow in a different way than putting CapEx".
  That route could ease the free-cash-flow strain (testable through capex/revenue and Broadcom revenue).

## Broadcom / TPUs

- TPUs as a product sold outside Google, an alternative to Nvidia ("what if Google sold its TPUs as an alternative to Nvidia?",
  Dec 2025). The long-run threat to Nvidia is "margin dilution".
- Anthropic's TPU deal "is ultimately an example of taking supply from Google" (TSMC-limited). That means more volume for Broadcom, but
  outside customers compete with Google's own use. More than 20% of TPU shipments from 3Q26 to 4Q27 go to Anthropic (Thompson citing
  SemiAnalysis, Aug 2026). That is concentration risk, and it matches the 8-K's "dependent on Anthropic's continued commercial success".
- Kurian on the press reports about the deal: "I would not assume everything you read in the press is true."

## H2: rates, Japan, yen

Not covered in any post read. The closest links are indirect: falling bond-issue cover, rising spreads, the Panic of 1873
analogy (worldwide credit tightening), and the call that SpaceX's ~$2tn IPO valuation is "nuts". H2 needs other sources.

## Claims we could add to the tracker (proposed, not added)

| Proposed claim | Check |
| --- | --- |
| Hyperscaler bond spreads keep rising (Aug 2026) | Add FRED `BAMLC0A0CM` (US investment-grade spread) and test the change since 2026-08-11 |
| Only Microsoft still has substantial FCF | Add MSFT/AMZN/META to the universe or a side table; test FCF > 0 |
| TSMC capex 2026 $52-56bn, capacity relief only in 2028-29 | TSMC capex from its 6-K; capex growth vs hyperscaler capex growth |
| Memory constraint gets relieved | Memory makers' margin trend and revenue growth deceleration (already in Trends tab) |
| TPU/Anthropic concentration (>20% of shipments) | Broadcom revenue concentration disclosures (10-K customer concentration) |

## Paid Updates to read if you subscribe (teaser-only here, high relevance)

- 2026-10-27: Anthropic S-1, The Cost of Compute, Who Is Paying? <https://stratechery.com/2026/anthropic-s-1-the-cost-of-compute-who-is-paying/>
- 2026-08-05: Google Earnings, The Frontier Case, Amazon Earnings <https://stratechery.com/2026/google-earnings-the-frontier-case-amazon-earnings/>
- 2026-06-08: Google Buys Compute From SpaceX, Broadcom's Outlook, Apple's AI Politics <https://stratechery.com/2026/google-buys-compute-from-spacex-broadcoms-outlook-apples-ai-politics/>
- 2026-04-07: Anthropic's New TPU Deal, Anthropic's Computing Crunch, The Anthropic-Google Alliance <https://stratechery.com/2026/anthropics-new-tpu-deal-anthropics-computing-crunch-the-anthropic-google-alliance/>
- 2026-03-11: Oracle Earnings, Oracle's Cloud Growth, Oracle's Software Defense <https://stratechery.com/2026/oracle-earnings-oracles-cloud-growth-oracles-software-defense/>
- 2026-01-21: TSMC Earnings, The TSMC Brake Revisited, Why AI Needs Foundry Competition <https://stratechery.com/2026/tsmc-earnings-the-tsmc-brake-revisited-why-ai-needs-foundry-competition/>

## Posts read in full

The Benefits of Bubbles (2025-11-05) · Google, Nvidia, and OpenAI (2025-12-01) · TSMC Risk (2026-01-26) ·
Aggregators and AI (2026-02-13) · Agents Over Bubbles (2026-03-16) · Interview: Jensen Huang (2026-03-17) ·
Interview: Rene Haas (2026-03-26) · Mythos, Muse, and the Opportunity Cost of Compute (2026-04-13) ·
Interview: Thomas Kurian (2026-04-23) · Amazon's Durability (2026-05-05) · The SpaceX IPO and Data Centers in Space
(2026-05-27) · The Google Capital Company (2026-06-02) · Power Shifts (2026-06-05) · Nvidia's Risky Business (2026-08-11) ·
The CapEx Train Keeps Rolling (2026-08-14) · Frontier Overhangs (2026-09-21) · The End of the Internet (2026-10-26).
All at stratechery.com; links in `stratechery_digest.md`.
