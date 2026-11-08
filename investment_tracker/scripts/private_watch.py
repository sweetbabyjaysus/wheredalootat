"""Daily watcher for private companies (config/private_watch.yaml).

    python3 scripts/private_watch.py

Checks public records and writes only NEW items to research/private_watch/YYYY-MM-DD.md.
Seen items are kept in data/private_watch_seen.csv. Job counts by location go to
data/private_watch_jobs.csv so hiring changes show up day to day. A source that can't be
reached is listed at the top of the note with the host to allow; the rest still run.
"""
import _path  # noqa: F401
import datetime as dt
import html
import os
import re
import xml.etree.ElementTree as ET

import pandas as pd
import requests
import yaml

from tracker.config import CONFIG, ROOT

SEEN = ROOT / "data" / "private_watch_seen.csv"
JOBS = ROOT / "data" / "private_watch_jobs.csv"
OUT = ROOT / "research" / "private_watch"
UA = {"User-Agent": os.environ.get("SEC_USER_AGENT", "wheredalootat-research tracker")}
TODAY = dt.date.today()


def _get(url, **kw):
    r = requests.get(url, headers=UA, timeout=40, **kw)
    r.raise_for_status()
    return r


def usaspending(co, cfg):
    start = (TODAY - dt.timedelta(days=cfg["lookback_days"])).isoformat()
    body = {"filters": {"recipient_search_text": co["search_names"][:1],
                        "time_period": [{"start_date": start, "end_date": TODAY.isoformat()}],
                        "award_type_codes": ["A", "B", "C", "D"]},
            "fields": ["Award ID", "Recipient Name", "Award Amount", "Awarding Agency", "Awarding Sub Agency",
                       "Start Date", "Description", "generated_internal_id"],
            "sort": "Award Amount", "order": "desc", "limit": 50, "page": 1}
    r = requests.post("https://api.usaspending.gov/api/v2/search/spending_by_award/", json=body, headers=UA, timeout=60)
    r.raise_for_status()
    for a in r.json().get("results", []):
        yield {"key": f"usa:{a.get('generated_internal_id') or a.get('Award ID')}",
               "date": a.get("Start Date"), "amount": a.get("Award Amount"),
               "title": f"{a.get('Awarding Agency')} / {a.get('Awarding Sub Agency')}: {str(a.get('Description') or '')[:160]}",
               "url": f"https://www.usaspending.gov/award/{a.get('generated_internal_id')}"}


def dod_contracts(co, cfg, _cache={}):
    if "items" not in _cache:
        feed = _get("https://www.defense.gov/DesktopModules/ArticleCS/RSS.ashx?ContentType=400&Site=945&max=10").content
        items = []
        for it in ET.fromstring(feed).iter("item"):
            link = it.findtext("link")
            try:
                text = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", _get(link).text)))
            except Exception:
                text = html.unescape(it.findtext("description") or "")
            items.append((it.findtext("title"), link, it.findtext("pubDate"), text))
        _cache["items"] = items
    for title, link, pub, text in _cache["items"]:
        for name in co["search_names"]:
            for m in re.finditer(re.escape(name), text):
                para = text[max(0, m.start() - 50): m.start() + 450]
                amt = re.search(r"\$[\d,]+(?:\.\d+)?", para)
                yield {"key": f"dod:{link}:{m.start()}", "date": pub, "amount": amt.group(0) if amt else "",
                       "title": f"{title}: {para.strip()[:300]}", "url": link}
            if re.search(re.escape(name), text):
                break


def sec_form_d(co, cfg):
    start = (TODAY - dt.timedelta(days=cfg["lookback_days"])).isoformat()
    for name in co["search_names"][:1]:
        j = _get("https://efts.sec.gov/LATEST/search-index",
                 params={"q": f'"{name}"', "forms": "D,D/A", "dateRange": "custom", "startdt": start,
                         "enddt": TODAY.isoformat()}).json()
        for h in j.get("hits", {}).get("hits", []):
            s = h.get("_source", {})
            adsh = h.get("_id", "").split(":")[0]
            cik = (s.get("ciks") or [""])[0].lstrip("0")
            yield {"key": f"secd:{adsh}", "date": s.get("file_date"), "amount": "",
                   "title": f"{s.get('form')} by {', '.join(s.get('display_names', []))[:160]}",
                   "url": f"https://www.sec.gov/Archives/edgar/data/{cik}/{adsh.replace('-', '')}/"}


def courtlistener(co, cfg):
    after = (TODAY - dt.timedelta(days=cfg["lookback_days"])).strftime("%m/%d/%Y")
    j = _get("https://www.courtlistener.com/api/rest/v4/search/",
             params={"q": f'"{co["search_names"][0]}"', "type": "r", "order_by": "dateFiled desc",
                     "filed_after": after}).json()
    for d in j.get("results", []):
        yield {"key": f"cl:{d.get('docket_id')}", "date": d.get("dateFiled"), "amount": "",
               "title": f"{d.get('caseName')} ({d.get('court')})",
               "url": "https://www.courtlistener.com" + (d.get("docket_absolute_url") or "")}


def lobbying(co, cfg):
    j = _get("https://lda.senate.gov/api/v1/filings/",
             params={"client_name": co["search_names"][0], "filing_year": TODAY.year}).json()
    for f in j.get("results", []):
        yield {"key": f"lda:{f.get('filing_uuid')}", "date": f.get("dt_posted", "")[:10],
               "amount": f.get("income") or f.get("expenses") or "",
               "title": f"{f.get('filing_type_display')} {f.get('filing_period_display')} - registrant {f.get('registrant', {}).get('name')}",
               "url": f.get("filing_document_url") or ""}


def jobs(co, cfg):
    if not co.get("greenhouse_board"):
        return []
    j = _get(f"https://boards-api.greenhouse.io/v1/boards/{co['greenhouse_board']}/jobs").json()
    counts = {}
    for job in j.get("jobs", []):
        loc = (job.get("location") or {}).get("name", "unknown")
        counts[loc] = counts.get(loc, 0) + 1
    rows = pd.DataFrame([{"date": TODAY.isoformat(), "company": co["id"], "location": k, "open_roles": v}
                         for k, v in counts.items()])
    old = pd.read_csv(JOBS) if JOBS.exists() else rows.iloc[0:0]
    prev = old[old.company == co["id"]]
    prev = prev[prev.date == prev.date.max()] if len(prev) else prev
    pd.concat([old[~((old.company == co["id"]) & (old.date == TODAY.isoformat()))], rows]).to_csv(JOBS, index=False)
    out = [{"key": f"jobs:{co['id']}:{TODAY}", "date": TODAY.isoformat(), "amount": str(sum(counts.values())),
            "title": f"{sum(counts.values())} open roles"
                     + (f" (was {int(prev.open_roles.sum())} on {prev.date.iloc[0]})" if len(prev) else " (first count)"),
            "url": f"https://boards.greenhouse.io/{co['greenhouse_board']}"}]
    if len(prev):
        p = prev.set_index("location").open_roles
        for loc, n in sorted(counts.items(), key=lambda x: -x[1]):
            d = n - int(p.get(loc, 0))
            if abs(d) >= 5 or loc not in p.index:
                out.append({"key": f"jobs:{co['id']}:{TODAY}:{loc}", "date": TODAY.isoformat(), "amount": f"{d:+d}",
                            "title": f"{loc}: {n} roles ({d:+d})", "url": ""})
    return out


SOURCES = {"usaspending": (usaspending, "api.usaspending.gov", "Federal contract awards"),
           "dod_contracts": (dod_contracts, "www.defense.gov", "DoD contract announcements"),
           "sec_form_d": (sec_form_d, "efts.sec.gov", "SEC Form D (fundraising)"),
           "courtlistener": (courtlistener, "www.courtlistener.com", "Court dockets"),
           "lobbying": (lobbying, "lda.senate.gov", "Lobbying filings"),
           "jobs": (jobs, "boards-api.greenhouse.io", "Open roles")}


def main():
    cfg = yaml.safe_load((CONFIG / "private_watch.yaml").read_text())
    seen = pd.read_csv(SEEN) if SEEN.exists() else pd.DataFrame(columns=["key", "first_seen"])
    seen_keys = set(seen.key)
    new, failed = [], {}
    for sid, (fn, host, label) in SOURCES.items():
        if not cfg["sources"].get(sid, {}).get("enabled"):
            continue
        for co in cfg["companies"]:
            try:
                for item in fn(co, cfg["sources"][sid]):
                    if item["key"] not in seen_keys:
                        seen_keys.add(item["key"])
                        new.append({**item, "company": co["name"], "source": label})
            except Exception as e:
                code = getattr(getattr(e, "response", None), "status_code", None)
                kind = ("site error, usually temporary - retried next run" if code and code >= 500
                        else "blocked: allow this host in the environment's network settings"
                        if "ProxyError" in type(e).__name__ else "error")
                failed[label] = f"{host} - {kind} ({type(e).__name__}: {str(e)[:70]})"
                break
    if new:
        pd.concat([seen, pd.DataFrame([{"key": n["key"], "first_seen": TODAY.isoformat()} for n in new])]).to_csv(SEEN, index=False)
    OUT.mkdir(parents=True, exist_ok=True)
    L = [f"# Private company watch - {TODAY}", ""]
    if failed:
        L += ["**Sources not checked this run:**", ""]
        L += [f"- {k}: {v}" for k, v in failed.items()] + [""]
    if not new:
        L.append("No new items from the reachable sources.")
    for co in cfg["companies"]:
        items = [n for n in new if n["company"] == co["name"]]
        if not items:
            continue
        L += [f"## {co['name']} ({len(items)} new)", ""]
        for n in sorted(items, key=lambda x: (x["source"], str(x["date"])), reverse=True):
            amt = f" - {n['amount']}" if n["amount"] not in ("", None) else ""
            link = f" ([link]({n['url']}))" if n["url"] else ""
            L.append(f"- **{n['source']}**, {n['date']}{amt}: {n['title']}{link}")
        L.append("")
    path = OUT / f"{TODAY}.md"
    if path.exists():   # a later run the same day: append rather than overwrite
        L[0] = f"\n---\n\n## Later run {dt.datetime.now():%H:%M}"
        path.write_text(path.read_text() + "\n".join(L) + "\n")
    else:
        path.write_text("\n".join(L) + "\n")
    print(f"{len(new)} new items; {len(failed)} sources unreachable -> {path}")
    for k, v in failed.items():
        print(f"  unreachable: {k}: {v}")


if __name__ == "__main__":
    main()
