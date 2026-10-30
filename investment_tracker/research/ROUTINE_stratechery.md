# Daily Stratechery check: runbook

Run by a scheduled routine once a day, and also runnable by hand. Research only, not trading advice.

1. Work in the repo `sweetbabyjaysus/wheredalootat` on branch `claude/awesome-goodall-qub0rn`.
   `cd investment_tracker && python3 -m pip install -q -r requirements.txt`, and run every script with `python3`
   (plain `pip`/`python` may point at different interpreters).
2. `python3 scripts/stratechery_scan.py` (incremental). It fetches new posts from the public
   WordPress API, scores them against `config/stratechery_watch.yaml` and the companies in
   `config/universe.csv`, and updates `data/stratechery_index.csv` and `research/stratechery_digest.md`.
3. For each new post scoring >= 15 (see the "New since the last scan" section of the digest):
   - **Free (full text)**: read `output/stratechery/<id>.txt`. Write 3-6 bullets in a dated note:
     the thesis, claims that bear on H1, H2, Alphabet, Broadcom or other universe names (short quotes
     under 25 words, never long passages), and anything checkable against the tracker's data.
   - **Paid Update (teaser only)**: record the title, link and teaser, and what it likely bears on.
     Mark any interpretation as **Inference**. Never try to get around the paywall.
4. Write the note to `research/stratechery_daily/YYYY-MM-DD.md`. Skip the file if nothing new
   scored >= 15, and say so in the run summary.
5. If a post makes a specific, checkable claim about a company or series in the tracker, propose a row
   for `config/claims_to_verify.csv` in the note. Don't add it automatically; the owner decides.
6. Commit only `data/stratechery_index.csv`, `research/stratechery_digest.md` and
   `research/stratechery_daily/`. Use the message "Stratechery daily scan YYYY-MM-DD" and push to the
   branch above. Never commit `output/` (it contains full article text).
7. End with a short summary: number of new posts, the relevant ones with links, and one line on why
   each matters to the analysis.
