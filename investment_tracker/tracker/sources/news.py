"""Headlines (Google News RSS + yfinance) and a transparent headline scorer."""
from __future__ import annotations

import datetime as dt
import email.utils
import re
import xml.etree.ElementTree as ET

import requests
import yfinance as yf

RSS = "https://news.google.com/rss/search"

POS = {"beat": .6, "beats": .6, "record": .5, "surge": .6, "surges": .6, "soar": .7, "soars": .7, "rally": .5,
       "upgrade": .6, "upgrades": .6, "raises": .5, "raised": .4, "strong": .4, "outperform": .5, "wins": .4,
       "deal": .3, "contract": .3, "growth": .3, "jumps": .5, "gains": .4, "boost": .4, "demand": .2}
NEG = {"miss": -.6, "misses": -.6, "plunge": -.7, "plunges": -.7, "slump": -.6, "falls": -.4, "drop": -.4,
       "drops": -.4, "downgrade": -.6, "downgrades": -.6, "cut": -.4, "cuts": -.4, "probe": -.5, "lawsuit": -.5,
       "default": -.8, "debt": -.2, "selloff": -.5, "sell-off": -.5, "warning": -.5, "warns": -.5, "weak": -.4,
       "loss": -.4, "losses": -.4, "tumble": -.6, "tumbles": -.6, "bubble": -.4, "concerns": -.3, "fears": -.4,
       "ban": -.5, "tariff": -.3, "tariffs": -.3, "spreads": -.2, "widen": -.3}


def headlines(company: str, ticker: str, days: int) -> list[dict]:
    q = f'"{company}" when:{days}d'
    items = []
    try:
        r = requests.get(RSS, params={"q": q, "hl": "en-US", "gl": "US", "ceid": "US:en"}, timeout=30)
        r.raise_for_status()
        for it in ET.fromstring(r.content).iter("item"):
            pub = email.utils.parsedate_to_datetime(it.findtext("pubDate"))
            items.append({"date": pub.date().isoformat(), "title": it.findtext("title"),
                          "source": "Google News RSS", "url": it.findtext("link")})
    except Exception:
        pass
    cutoff = dt.date.today() - dt.timedelta(days=days)
    try:
        for n in yf.Ticker(ticker).news or []:
            c = n.get("content", n)
            d = (c.get("pubDate") or "")[:10]
            if d and dt.date.fromisoformat(d) >= cutoff:
                items.append({"date": d, "title": c.get("title"), "source": "yfinance news",
                              "url": (c.get("canonicalUrl") or {}).get("url", "")})
    except Exception:
        pass
    seen, out = set(), []
    for i in items:
        k = re.sub(r"\W+", " ", (i["title"] or "").lower()).strip()[:80]
        if k and k not in seen:
            seen.add(k); out.append(i)
    return out


def score_lexicon(title: str) -> tuple[float, str]:
    words = re.findall(r"[a-z\-]+", title.lower())
    hits = [(w, POS.get(w, NEG.get(w))) for w in words if w in POS or w in NEG]
    if not hits:
        return 0.0, "no scored terms"
    s = max(-1.0, min(1.0, sum(v for _, v in hits)))
    return round(s, 2), "terms: " + ", ".join(f"{w}({v:+.1f})" for w, v in hits)
