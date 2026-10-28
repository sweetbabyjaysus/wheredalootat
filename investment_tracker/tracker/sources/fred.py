"""FRED via the keyless fredgraph CSV endpoint."""
from __future__ import annotations

import io

import pandas as pd
import requests

URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"


def series(series_id: str, start: str) -> pd.Series:
    r = requests.get(URL, params={"id": series_id, "cosd": start}, timeout=30)
    r.raise_for_status()
    df = pd.read_csv(io.StringIO(r.text))
    df.columns = ["date", "value"]
    s = pd.to_numeric(df["value"], errors="coerce")
    s.index = pd.to_datetime(df["date"])
    return s.dropna().rename(series_id)
