"""Index stratechery.com and score every post against our companies and themes.

    python scripts/stratechery_scan.py            # incremental: fetch posts newer than the index
    python scripts/stratechery_scan.py --full     # re-index the whole site (about 30 requests)
    python scripts/stratechery_scan.py --rescore  # re-score the index after editing the watch list (no fetching)

Uses only what the public WordPress API serves without logging in: full text for free articles
(and some interviews), title + teaser for paid Updates. It never tries to get around the paywall.

Writes (committed): data/stratechery_index.csv - one row per post: id, date, url, title, access
(full/teaser), score, topics, companies, hypotheses. No article text is stored in the repo; full
text is cached under output/stratechery/ (git-ignored) for reading.
Writes research/stratechery_digest.md: new relevant posts since the last scan + the top posts overall.
"""
import _path  # noqa: F401
import argparse
import datetime as dt
import html
import re
import time

import pandas as pd
import requests
import yaml

from tracker.config import CONFIG, ROOT, load_universe

INDEX = ROOT / "data" / "stratechery_index.csv"
DIGEST = ROOT / "research" / "stratechery_digest.md"
CACHE = ROOT / "output" / "stratechery"
HEADERS = {"User-Agent": "wheredalootat-research (personal investment research tracker)"}
FIELDS = "id,date,link,title,excerpt,content,categories"


def text(h: str) -> str:
    h = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", h, flags=re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h))).strip()


def load_watch():
    w = yaml.safe_load((CONFIG / "stratechery_watch.yaml").read_text())
    topics = {k: v for k, v in w["topics"].items()}
    u = load_universe()
    for _, r in u.iterrows():
        names = {r.company, r.ticker.split(".")[0]} - {""}
        if r.company == "Alphabet":
            names |= {"Google"}
        topics[f"co:{r.ticker}"] = {"weight": 3, "informs": [r.ticker], "terms": sorted(names)}
    pats = {k: re.compile(r"\b(" + "|".join(re.escape(t) for t in v["terms"]) + r")\b", re.I) for k, v in topics.items()}
    return w, topics, pats


def score(title: str, body: str, topics, pats):
    hits, total, informs = {}, 0.0, set()
    for k, p in pats.items():
        n_title = len(p.findall(title))
        n_body = len(p.findall(body))
        if n_title or n_body:
            hits[k] = n_title + n_body
            # title hits count most; body hits taper (log-like) so long posts don't dominate
            total += topics[k]["weight"] * (3 * n_title + min(n_body, 10) ** 0.5)
            informs |= set(topics[k]["informs"])
    return round(total, 1), hits, informs


def fetch(after: str | None, cfg):
    s = requests.Session(); s.headers.update(HEADERS)
    page, out = 1, []
    while True:
        params = {"per_page": 100, "page": page, "_fields": FIELDS, "orderby": "date", "order": "desc"}
        if after:
            params["after"] = after
        r = s.get(cfg["source"]["api"], params=params, timeout=60)
        if r.status_code == 400 and page > 1:
            break                                  # past the last page
        r.raise_for_status()
        batch = r.json()
        out += batch
        if page >= int(r.headers.get("X-WP-TotalPages", 1)):
            break
        page += 1
        time.sleep(1.0)                            # polite pacing
    return out


def main(full: bool):
    cfg, topics, pats = load_watch()
    old = pd.read_csv(INDEX) if INDEX.exists() and not full else pd.DataFrame()
    after = None if old.empty else (pd.to_datetime(old.date).max() - pd.Timedelta(days=2)).isoformat()
    posts = fetch(after, cfg)
    CACHE.mkdir(parents=True, exist_ok=True)
    rows = []
    for p in posts:
        title, teaser, body = text(p["title"]["rendered"]), text(p["excerpt"]["rendered"]), text(p["content"]["rendered"])
        access = "full" if len(body.split()) >= cfg["source"]["min_public_words"] else "teaser"
        if access == "full":
            (CACHE / f"{p['id']}.txt").write_text(f"{title}\n{p['link']}\n{p['date']}\n\n{body}")
        sc, hits, informs = score(title, teaser + " " + (body if access == "full" else ""), topics, pats)
        rows.append({"id": p["id"], "date": p["date"][:10], "url": p["link"], "title": title, "access": access,
                     "words_public": len(body.split()) if access == "full" else 0, "score": sc,
                     "topics": ";".join(sorted(k for k in hits if not k.startswith("co:"))),
                     "companies": ";".join(sorted(k[3:] for k in hits if k.startswith("co:"))),
                     "informs": ";".join(sorted(informs)), "teaser": teaser[:300],
                     "first_seen": dt.date.today().isoformat()})
    new = pd.DataFrame(rows)
    if not old.empty:
        new = new[~new.id.isin(old.id)]
        allp = pd.concat([old, new])
    else:
        allp = new
    allp = allp.drop_duplicates("id").sort_values(["date", "id"], ascending=False, kind="stable")
    INDEX.parent.mkdir(exist_ok=True)
    allp.to_csv(INDEX, index=False)
    write_digest(allp, new)
    print(f"{len(posts)} fetched, {len(new)} new, {len(allp)} indexed; "
          f"{int((new.score >= 15).sum()) if len(new) else 0} new posts scored >= 15")
    for _, r in new.sort_values("score", ascending=False).head(15).iterrows():
        print(f"  {r.date} {r.score:5.1f} [{r.access}] {r.title}  ({r.companies or r.topics})")


def rescore():
    _, topics, pats = load_watch()
    allp = pd.read_csv(INDEX)
    for i, r in allp.iterrows():
        cached = CACHE / f"{r.id}.txt"
        body = cached.read_text() if r.access == "full" and cached.exists() else ""
        sc, hits, informs = score(r.title, f"{r.teaser if isinstance(r.teaser, str) else ''} {body}", topics, pats)
        allp.loc[i, ["score", "topics", "companies", "informs"]] = [
            sc, ";".join(sorted(k for k in hits if not k.startswith("co:"))),
            ";".join(sorted(k[3:] for k in hits if k.startswith("co:"))), ";".join(sorted(informs))]
    allp.to_csv(INDEX, index=False)
    write_digest(allp, allp.iloc[0:0])
    print(f"rescored {len(allp)}")


def write_digest(allp: pd.DataFrame, new: pd.DataFrame, top_n: int = 25):
    def line(r):
        tag = "free, full text" if r.access == "full" else "paid Update, teaser only"
        what = ", ".join(x for x in (r.companies, r.informs) if isinstance(x, str) and x)
        return f"- {r.date} **[{r.title}]({r.url})** - score {r.score:g}, {tag}; relates to {what}"
    L = [f"# Stratechery scan - {dt.date.today().isoformat()}", "",
         f"{len(allp)} posts indexed from stratechery.com. Scores weight matches on our companies and themes "
         "(`config/stratechery_watch.yaml`); titles count most. Paid Updates are scored on title + teaser only.", ""]
    rel_new = new[new.score >= 15].sort_values("score", ascending=False) if len(new) else new
    L += ["## New since the last scan", ""] + ([line(r) for _, r in rel_new.iterrows()] or ["- none above score 15"])
    yr = pd.to_datetime(allp.date) >= pd.Timestamp.today() - pd.Timedelta(days=365)
    recent, older = allp[yr], allp[~yr]
    L += ["", f"## Free articles and interviews, last 12 months (top {top_n})", ""]
    L += [line(r) for _, r in recent[recent.access == "full"].sort_values("score", ascending=False).head(top_n).iterrows()]
    L += ["", f"## Paid Updates, last 12 months (top {top_n}; scored on title + teaser)", ""]
    L += [line(r) for _, r in recent[recent.access == "teaser"].sort_values("score", ascending=False).head(top_n).iterrows()]
    L += ["", "## Older background (top 15)", ""]
    L += [line(r) for _, r in older.sort_values("score", ascending=False).head(15).iterrows()]
    DIGEST.write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--rescore", action="store_true")
    a = ap.parse_args()
    rescore() if a.rescore else main(a.full)
