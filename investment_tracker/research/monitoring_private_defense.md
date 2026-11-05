# Watching private defense companies: Anduril and General Atomics

Neither company reports results. Public records still show where money, people and buildings are going.
Ordered by signal per hour of effort. "Auto" means it can be pulled by script once the host is allowed
in the environment's network settings.

## 1. Government money (strongest signal)

| Source | What it shows | Auto |
| --- | --- | --- |
| **USAspending.gov** (api.usaspending.gov) | Every federal contract, grant and other-transaction award by recipient, with amounts, agency, place of performance and modifications. Search by recipient UEI | Yes, free API |
| **DoD daily contract announcements** (defense.gov/News/Contracts) | Every award of $7.5m or more, published at 5pm ET each business day | Yes, RSS/HTML |
| **SAM.gov** (api.sam.gov) | Entity registrations (new subsidiaries and sites), contract opportunities, award notices | Yes, free API key |
| **GAO bid protests** (gao.gov/legal/bid-protests) | Lost or contested competitions, e.g. robotic wingman jets, drones, Janus | Yes |
| **SBIR.gov** | Small research awards: early hints of new product lines | Yes |
| **Service budget books** (comptroller.defense.gov, program elements) | Funding for programs they're on: CCA, MQ-9, Janus, counter-drone | Manual, yearly |
| **Allied tenders**: UK Contracts Finder, Australia AusTender, EU TED | Anduril UK/Australia (Ghost Shark); GA-ASI exports | Yes |

## 2. Money raised and corporate moves

| Source | What it shows | Auto |
| --- | --- | --- |
| **SEC Form D** (efts.sec.gov full-text search) | Anduril files a Form D for each raise: amount sold and date, often before the press does. Special purpose vehicles (SPVs) that buy Anduril shares file Form Ds too | Yes |
| **EDGAR full-text search** for "Anduril" / "General Atomics" | Public suppliers and partners naming them in 10-Ks, 8-Ks and contracts | Yes |
| **FTC early-termination notices (HSR)** | Large acquisitions before they close | Yes |
| **UCC filings** (California bizfile; Delaware) | Secured loans and equipment financing against their assets | Manual |
| **State incentive deals** (Ohio Tax Credit Authority / JobsOhio for Anduril's Arsenal-1 in Columbus) | Committed jobs, payroll and investment figures, plus later compliance reports | Manual |
| **Municipal bond disclosures** (EMMA, msrb.org) | Industrial revenue bonds tied to their plants | Manual |

## 3. Buildings and land

| Source | What it shows | Auto |
| --- | --- | --- |
| **City/county permit portals**: Columbus/Franklin County (Arsenal-1, Rickenbacker); Costa Mesa (Anduril HQ); Poway, San Diego, Palmdale and El Mirage CA (GA-ASI) | New buildings, size and cost of work, occupancy dates | Partly (some portals have APIs) |
| **County recorder / assessor** | Land purchases and leases | Manual |
| **Satellite imagery**: Sentinel-2 via Copernicus EO Browser (free, 10 m, every ~5 days); Google Earth Pro historical imagery; Planet (paid, daily) | Construction progress at Arsenal-1, test-site activity, parked aircraft | Sentinel-2 yes |
| **Environmental permits** (EPA ECHO, state air-quality boards) | New manufacturing processes and plant expansions | Yes |

Google Maps only shows one recent image. Google Earth Pro's time slider and Sentinel-2 give dated history, which is what you need to measure progress.

## 4. Testing and operations

| Source | What it shows | Auto |
| --- | --- | --- |
| **FCC Experimental Licensing System** (apps.fcc.gov/oetcf/els) | Radio and radar test licences: locations, frequencies, sometimes program names. One of the best early hints | Yes |
| **FAA registry** (N-numbers) and airspace TFRs/NOTAMs | New aircraft and drones registered; flight-test windows near their sites | Yes |
| **NRC ADAMS** (General Atomics nuclear filings) and **Army Janus milestones** | GA-TES microreactor at Fort Hood: licensing documents, schedule | Yes |

## 5. People

| Source | What it shows | Auto |
| --- | --- | --- |
| **Job postings**: Anduril's Greenhouse board (boards-api.greenhouse.io); GA careers | Open roles by city and function: where they're expanding next | Yes |
| **DOL H-1B wage filings (LCA data)** | Worksite locations and salary levels | Yes, quarterly |
| **State WARN notices** | Layoffs or site closures | Yes |
| **OSHA establishment search** | Active sites and inspections | Yes |

## 6. Legal and political

| Source | What it shows | Auto |
| --- | --- | --- |
| **CourtListener / PACER** | Lawsuits: contract disputes, IP, employment | Yes (CourtListener API) |
| **Senate lobbying disclosures** (lda.senate.gov) | Lobbying spend and the bills/programs they're working on, quarterly | Yes |
| **Patents**: PatentsView / Google Patents, by assignee | New technology areas | Yes |

## Hosts to allow for automation

api.usaspending.gov, www.defense.gov, api.sam.gov, efts.sec.gov, www.gao.gov, apps.fcc.gov,
boards-api.greenhouse.io, www.courtlistener.com, lda.senate.gov, search.patentsview.org,
www.federalregister.gov, adams.nrc.gov, dataspace.copernicus.eu (sec.gov is already allowed).
