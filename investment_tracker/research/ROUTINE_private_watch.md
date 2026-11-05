# Daily private-company watch: runbook

Watches Anduril, General Atomics, Valar Atomics and Radiant (`config/private_watch.yaml`) in public
records: federal contract awards, DoD contract announcements, SEC Form D fundraising, court dockets,
lobbying filings, and job-board counts by location.

1. Work in the repo `sweetbabyjaysus/wheredalootat` on branch `claude/awesome-goodall-qub0rn`.
   `cd investment_tracker && python3 -m pip install -q -r requirements.txt`.
2. Run `python3 scripts/private_watch.py`. It writes `research/private_watch/YYYY-MM-DD.md` with only
   new items, and updates `data/private_watch_seen.csv` and `data/private_watch_jobs.csv`.
3. Read the note. For any new contract award, Form D, lawsuit or big hiring change, add 1-3 bullets
   under a "Why it matters" heading at the end of the note: link it to the defense-tech or nuclear themes
   (`research/monitoring_private_defense.md`, `research/nuclear_microreactors.md`). Label interpretation as **Inference**.
4. Commit only `data/private_watch_seen.csv`, `data/private_watch_jobs.csv` and `research/private_watch/`
   with the message "Private company watch YYYY-MM-DD", and push to the branch. If the push is rejected,
   `git pull --rebase` and push again.
5. End with a short summary: new items per company with links, plus any sources listed as unreachable.
