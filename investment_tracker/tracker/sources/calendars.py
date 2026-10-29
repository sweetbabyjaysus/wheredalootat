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
    """MPMs are two-day meetings; the decision comes on day two. The page's other columns
    (Outlook Report, Summary of Opinions, minutes) are single dates, so only pairs match."""
    text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " | ", requests.get(BOJ_URL, timeout=30).text))
    out = []
    for yblock in re.finditer(r"Table : (20\d\d)(.*?)(?=Table : 20\d\d|Note:|$)", text):
        year = int(yblock[1])
        for m in re.finditer(r"\b(Jan|Feb|Mar|Apr|May|June?|July?|Aug|Sept?|Oct|Nov|Dec)\.? (\d{1,2}) \(\w+\.?\), "
                             r"(?:(Jan|Feb|Mar|Apr|May|June?|July?|Aug|Sept?|Oct|Nov|Dec)\.? )?(\d{1,2}) \(\w+\.?\)",
                             yblock[2]):
            month = MONTHS[(m[3] or m[1])[:3].lower()]
            out.append({"event": "BoJ MPM decision", "date": pd.Timestamp(year, month, int(m[4])).date().isoformat(),
                        "detail": m[0], "source": BOJ_URL})
    return sorted({d["date"]: d for d in out}.values(), key=lambda d: d["date"])


# BLS blocks scripted requests (HTTP 403); FRED mirrors the official BLS CPI release schedule.
CPI_CAL_URL = "https://fred.stlouisfed.org/releases/calendar?rid=10&y={year}"


def bls_cpi() -> list[dict]:
    out = []
    this = pd.Timestamp.today().year
    for year in (this, this + 1):
        url = CPI_CAL_URL.format(year=year)
        text = re.sub(r"<[^>]+>", " | ", requests.get(url, timeout=60).text)
        for m in re.finditer(r"(?:Monday|Tuesday|Wednesday|Thursday|Friday) ([A-Z][a-z]+) (\d{1,2}), (20\d\d)", text):
            d = pd.Timestamp(int(m[3]), MONTHS[m[1][:3].lower()], int(m[2])).date().isoformat()
            out.append({"event": "US CPI release", "date": d, "detail": "BLS schedule via FRED", "source": url})
    return sorted({d["date"]: d for d in out}.values(), key=lambda d: d["date"])
