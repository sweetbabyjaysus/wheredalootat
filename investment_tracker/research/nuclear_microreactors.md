# Pocket reactors: microreactors and SMRs (2026-11-05)

Microreactors (about 1-20 MWe, factory-built, often transportable) and small modular reactors (SMRs, up to about 300 MWe).
Prices are from yfinance (close 2026-11-04). Program facts come from web research summaries; items marked [weak] rely on
secondary sources, and [unverified] items could not be confirmed. Lines marked **Inference** are interpretation.

## Where the technology actually is

| Milestone | Status |
| --- | --- |
| Reactor goes critical (zero power) | **Yes, five in 2026** under DOE's Reactor Pilot Program: Antares Mark-0 (Jun 4), Valar Ward250 (Jun 18), Deployable Energy Unity (~Jul 1), Aalo (Jul 4), Oklo Groves isotope reactor (Aug 5) |
| Producing useful power | Not yet. Valar claims a GPU demonstration at ~37% power on Jul 1 (company claim) |
| NRC operating license for any microreactor | **None.** Every criticality ran under DOE authorization |
| Powering a data center | **None yet.** Aalo targets 2027 |
| Military power on a base | Target **Sept 2028** (Army Janus, Navy Crane); Project Pele demo slipped to **2028** |
| Fuel (HALEU) at commercial scale | Binding constraint until about **2028-29** (Centrus expansion ~2029, TRISO-X plant early 2028) |

**Inference:** the physics works and the timeline is now set by licensing and fuel, not technology. Commercial power
arrives about 2028-2030. That gap is why the pre-revenue stocks have fallen 70-86% from their highs.

## Military programs (the "tested by the military" part)

- **Army Janus** (Aug 26, 2026): five vendor/base pairs, up to **$2.2bn** in total, milestone-paid, contractor-owned and contractor-operated, first power targeted Sept 2028:
  - Antares at Fort Bragg
  - BWXT (BANR 20 MWe) at Fort Campbell
  - **General Atomics (GA-TES ~5 MWe) at Fort Hood**
  - Radiant (up to $750m, 15 units) at Fort Benning
  - Westinghouse (eVinci) at Fort Drum
- **Air Force ANPI**: down-selected Antares, Radiant and Westinghouse, for Buckley and Malmstrom, with Joint Base San Antonio a possible third site.
- **Eielson AFB**: Oklo, 5 MWe. Environmental review started in summer 2026; the power purchase agreement depends on an NRC license.
- **Navy**: Naval Weapons Station Crane, Indiana, by Sept 2028. Vendor not named.
- **Project Pele** (BWXT): core built in 2026, not yet shipped to INL. Demo in 2028.
- **Airlift**: in Feb 2026, C-17s flew an unfueled Valar Ward250 between bases.
- **Policy**: EO 14299 requires an Army reactor operating by Sept 30, 2028. EO 14300 sets 18-month NRC review deadlines.

## Data-center / AI deals

| Buyer | Vendor | Size / timing |
| --- | --- | --- |
| Meta | TerraPower; Oklo | Up to 8 Natrium plants, first two by 2032; Oklo 1.2 GW Ohio campus with prepayment |
| Google | Kairos | Up to 500 MW, first ~2030 [prior] |
| Amazon | X-energy | >5 GW by 2039 [prior/weak] |
| Switch | Oklo | 12 GW, **non-binding** (Oklo 10-Q) |
| Equinix | Oklo; Radiant | 500 MW ($25m prepaid); 20 Kaleidos units |
| Microsoft | Constellation (TMI restart) | 835 MW, ~2027; no SMR deal found |

## The players

### Listed: companies with revenue and military contracts

| Company | Ticker | Price | Mkt cap | From high | What matters |
| --- | --- | --- | --- | --- | --- |
| BWX Technologies | BWXT | $121.50 | $11.1bn | −49% | Pele; Janus at Fort Campbell; TRISO fuel; Q3 revenue $953m (+10%); 2026 EPS $4.72-4.77 |
| GE Vernova | GEV | $832.83 | $220bn | −29% | BWRX-300 (TVA Clinch River permit [weak]; Darlington ~2029-30). Also gas turbines for data centers |
| Rolls-Royce | RR.L | 1,286p | £105bn | −18% | 470 MWe SMR; not researched for 2026 |
| Cameco | CCJ | $71.68 | $31bn | −47% | Co-owns Westinghouse (eVinci at Fort Drum; ANPI) + uranium |

### Listed: fuel chokepoint (the nuclear equivalent of H1's bottleneck)

| Company | Ticker | Price | From high | What matters |
| --- | --- | --- | --- | --- |
| Centrus Energy | LEU | $92.58 | −73% | Only US HALEU enrichment; $900m DOE task order; ~2029 expansion; deals with Radiant and Antares |
| Standard Nuclear | STDN | $12.16 | −27% | TRISO fuel maker, IPO Jul 2026 |
| X-energy | XE | $10.05 | −72% | Xe-100 + TRISO-X (first NRC HALEU fuel license, Feb 2026); Amazon; IPO Apr 2026 at $23 |

### Listed: pre-revenue reactor developers

| Company | Ticker | Price | From high | What matters | Next |
| --- | --- | --- | --- | --- | --- |
| Oklo | OKLO | $22.12 | −82% | Aurora 15-75 MWe; Groves critical Aug 2026; Meta, Equinix, Switch (non-binding); Eielson | **Q3 results Nov 6** |
| NuScale | SMR | $5.13 | −86% | NRC design approvals; ENTRA1/TVA 6 GW pending | ENTRA1 PPA by end-2026 |
| NANO Nuclear | NNE | $10.95 | −75% | KRONOS construction permit application under NRC review | Construction 2H 2027 at earliest |
| Deep Fission | FISN | $2.21 | −85% | Borehole reactor; date slipped | — |
| Terrestrial Energy | IMSR | $2.87 | −82% | Molten salt | — |
| Terra Innovatum | NKLR | $2.34 | −70% | 1 MWe SOLO | — |
| Lightbridge | LTBR | $4.46 | −81% | Metallic fuel | — |

### Private: the ones actually going critical or winning military work

| Company | Design | Why watch |
| --- | --- | --- |
| Radiant | Kaleidos 1.2 MWe | Janus (Benning) + ANPI + Equinix; DOE full-power safety approval Oct 29, 2026; fueling at INL next |
| Antares | R1 ~1 MWe | First to criticality (Jun 4); Janus (Bragg) + ANPI |
| Valar Atomics | Ward250 ≤5 MWe | Critical Jun 18; **backed by Palmer Luckey** (Anduril's founder); $2bn valuation (Bloomberg) |
| Aalo | 10-50 MWe sodium | Critical Jul 4; 2027 data-center reactor |
| Westinghouse | eVinci ~5 MWe | Janus (Drum) + ANPI; owned by Brookfield/Cameco |
| **General Atomics** | GA-TES ~5 MWe | Janus at Fort Hood (see `monitoring_private_defense.md`) |
| Kairos | KP-FHR | Google; Hermes construction permits; completion by 2029 |
| TerraPower | Natrium 345 MWe | Meta; first non-light-water construction permit in 40+ years (Mar 2026) |

## How this connects to the tracker (Inference)

1. **Same pattern as AI.** The pre-revenue developers are long-dated and cash-burning, and they fund themselves with equity. That is the "leveraged buildout" risk profile, and in 2026 they sold off the same way.
2. **The bottleneck idea transfers.** HALEU/TRISO fuel (Centrus, Standard Nuclear, BWXT, X-energy's TRISO-X) is the nuclear chokepoint, as TSMC is for chips.
3. **The military is the first customer.** Contracts with dated milestones (Janus 2028, ANPI 2030) give BWXT, Radiant, Antares, Westinghouse and General Atomics revenue visibility that data-center PPAs (often non-binding) don't.
4. **Power and compute.** Firm power on site removes the grid-permitting wait that Thompson calls a top constraint ("not just power... but zoning"). That only matters after about 2028.

## Next dated catalysts

- **Nov 6, 2026:** Oklo Q3 results.
- **Pending:** Radiant DOME fueling and criticality.
- **Late 2026:** Last Energy pilot criticality; NuScale/ENTRA1 PPA; Dow/X-energy Long Mott construction permit.
- **2028:** Janus first power (Sept 30, EO deadline); Pele demo; TRISO-X production.

## Sources (from the research pass)

- [National Defense: 2028 goal](https://www.nationaldefensemagazine.org/articles/2026/8/31/small-nuclear-reactors-on-horizon-as-pentagon-programs-eye-2028-goal)
- [DefenseScoop: Janus bases](https://defensescoop.com/2026/08/26/army-annouces-initiial-bases-to-host-nuclear-microreactors/)
- [WNN: five Janus vendors](https://www.world-nuclear-news.org/articles/us-army-selects-five-microreactor-vendors-to-power-bases)
- [ExecutiveGov: $2.2bn Janus](https://www.executivegov.com/articles/army-janus-nuclear-microreactors)
- [DIU ANPI](https://www.diu.mil/latest/DOD-selects-eligible-companies-for-the-Advanced-Nuclear-Power-for-Installations-Program)
- [ANS: Air Force picks three](https://www.ans.org/news/article-7972/air-force-selects-three-microreactor-developers-for-anpi/)
- [Navy Times: Crane](https://www.navytimes.com/news/your-navy/2026/09/10/navy-installing-advanced-nuclear-microreactor-at-indiana-command/)
- [DOE Reactor Pilot Program](https://www.energy.gov/ne/us-department-energy-reactor-pilot-program)
- [ANS: pilot deadline check-in](https://www.ans.org/news/article-8178/the-deadline-arrives-checking-in-on-the-reactor-pilot-program/)
- [WNN: Valar criticality](https://www.world-nuclear-news.org/articles/valar-atomics-achieves-criticality-in-doe-reactor-pilot-program)
- [WNN: Aalo, fourth criticality](https://www.world-nuclear-news.org/articles/criticality-for-fourth-us-microreactor-meets-deadline)
- [Radiant: DOE full-power approval](https://www.financialcontent.com/article/bizwire-2026-10-29-radiant-achieves-industry-milestone-as-the-only-microreactor-design-to-secure-doe-safety-analysis-approval-for-full-power-operations)
- [NRC: TerraPower permit](https://www.nrc.gov/sites/default/files/cdn/doc-collection-news/2026/26-028.pdf)
- [Centrus 10-Q](https://www.sec.gov/Archives/edgar/data/0001065059/000162828026053863/leu-20260630.htm)
- [NucNet: Centrus $900m](https://www.nucnet.org/news/centrus-finalises-usd900-million-haleu-enrichment-contract-with-us-doe-7-5-2026)
- [ANS: TRISO-X license](https://www.ans.org/news/article-7762/nrc-grants-license-for-trisox-fuel-manufacturing-using-haleu/)
- [BWXT Q3 2026 8-K](https://www.sec.gov/Archives/edgar/data/0001486957/000148695726000053/bwxt_93026xerexhibit991.htm)
- [Bloomberg Law: Valar $2bn](https://news.bloomberglaw.com/private-equity/luckey-backed-nuclear-startup-valar-lands-2-billion-valuation)
- [Axios: Meta nuclear deals](https://www.axios.com/2026/01/09/meta-nuclear-deal-vistra-terrapower-oklo)
- [Oklo 10-Q (Switch non-binding)](https://www.sec.gov/Archives/edgar/data/1849056/000162828026054571/oklo-20260630.htm)
- [X-energy IPO](https://x-energy.com/news/x-energy-announces-pricing-of-upsized-initial-public-offering/)
- [Standard Nuclear IPO](https://www.orrick.com/en/News/2026/07/Standard-Nuclear-Announces-IPO)
