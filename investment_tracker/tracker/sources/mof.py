"""Japan Ministry of Finance JGB yield curve CSVs (daily, all tenors)."""
from __future__ import annotations

import io
import re

import pandas as pd
import requests

BASE = "https://www.mof.go.jp/english/policy/jgbs/reference/interest_rate"
URLS = [f"{BASE}/historical/jgbcme_all.csv", f"{BASE}/jgbcme.csv"]  # history + current month
ERA = {"S": 1925, "H": 1988, "R": 2018}


def _parse_date(s):
    if not isinstance(s, str):
        return pd.NaT
    s = s.strip()
    m = re.match(r"^([SHR])(\d+)\.(\d+)\.(\d+)$", s)
    if m:
        return pd.Timestamp(ERA[m[1]] + int(m[2]), int(m[3]), int(m[4]))
    return pd.to_datetime(s, errors="coerce")


def _read(url: str) -> pd.DataFrame:
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    lines = r.content.decode("utf-8", errors="replace").splitlines()
    hdr = next(i for i, l in enumerate(lines) if l.lower().startswith("date"))
    df = pd.read_csv(io.StringIO("\n".join(lines[hdr:])), dtype=str)
    df.index = [_parse_date(d) for d in df.iloc[:, 0]]
    df = df.iloc[:, 1:].apply(pd.to_numeric, errors="coerce")
    df.columns = [c.strip() for c in df.columns]
    return df[df.index.notna()]


def curve(start: str) -> pd.DataFrame:
    frames = [_read(u) for u in URLS]
    df = pd.concat(frames)
    df = df[~df.index.duplicated(keep="last")].sort_index()
    return df[df.index >= pd.Timestamp(start)]


def tenor(t: str, start: str) -> pd.Series:
    return curve(start)[t].dropna().rename(f"JGB_{t}")
