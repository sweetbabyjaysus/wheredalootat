"""Official meeting calendars, parsed from the Fed and BoJ websites (never assumed)."""
from __future__ import annotations

import re

import pandas as pd
import requests

FOMC_URL = "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"
BOJ_URL = "https://www.boj.or.jp/en/mopo/mpmsche_minu/index.htm"
MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}


def fomc() -> list[dict]:
    html = requests.get(FOMC_URL, timeout=30).text
    out = []
    for ym in re.finditer(r"(\d{4}) FOMC Meetings(.*?)(?=\d{4} FOMC Meetings|$)", html, re.S):
        year, block = int(ym[1]), ym[2]
        for m in re.finditer(r'fomc-meeting__month[^>]*>\s*<strong>([A-Za-z/]+)</strong>.*?'
                             r'fomc-meeting__date[^>]*>([^<]+)<', block, re.S):
            month = MONTHS[m[1].split("/")[-1][:3].lower()]
            last_day = int(re.findall(r"\d+", m[2])[-1])
            out.append({"event": "FOMC decision", "date": pd.Timestamp(year, month, last_day).date().isoformat(),
                        "detail": m[2].strip(), "source": FOMC_URL})
    return out


def boj() -> list[dict]:
    html = re.sub(r"<[^>]+>", " ", requests.get(BOJ_URL, timeout=30).text)
    html = re.sub(r"\s+", " ", html)
    out = []
    # e.g. "2026 ... Dec. 18 (Thu.), 19 (Fri.)" - year headings precede rows
    for yblock in re.finditer(r"(20\d\d)(.*?)(?=20\d\d|$)", html):
        year = int(yblock[1])
        for m in re.finditer(r"\b(Jan|Feb|Mar|Apr|May|June?|July?|Aug|Sept?|Oct|Nov|Dec)\.? (\d{1,2}) \(\w+\.?\)"
                             r"(?:, (\d{1,2}) \(\w+\.?\))?", yblock[2]):
            day = int(m[3] or m[2])
            out.append({"event": "BoJ MPM decision",
                        "date": pd.Timestamp(year, MONTHS[m[1][:3].lower()], day).date().isoformat(),
                        "detail": m[0], "source": BOJ_URL})
    return sorted({d["date"]: d for d in out}.values(), key=lambda d: d["date"])
