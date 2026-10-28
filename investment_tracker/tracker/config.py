"""Load and validate the config files."""
from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config"

UNIVERSE_COLS = ["bucket", "group", "company", "ticker", "alt_tickers", "exchange", "currency",
                 "fundamentals_source", "fiscal_year_end", "rationale"]
TEST_TYPES = {"group_value", "group_diff", "series_change", "series_change_pct", "series_level",
              "series_pctile", "event_mean", "all_of"}
OPS = {">", ">=", "<", "<=", "==", "!="}


def load_universe() -> pd.DataFrame:
    df = pd.read_csv(CONFIG / "universe.csv", dtype=str).fillna("")
    missing = set(UNIVERSE_COLS) - set(df.columns)
    if missing:
        raise ValueError(f"universe.csv missing columns: {sorted(missing)}")
    if df["ticker"].duplicated().any():
        raise ValueError(f"duplicate tickers: {df.loc[df.ticker.duplicated(), 'ticker'].tolist()}")
    return df


def load_settings() -> dict:
    s = yaml.safe_load((CONFIG / "settings.yaml").read_text())
    s["sec_user_agent"] = os.environ.get(s.get("sec_user_agent_env", "SEC_USER_AGENT"), "")
    return s


def load_hypotheses() -> dict:
    cfg = yaml.safe_load((CONFIG / "hypotheses.yaml").read_text())
    validate_hypotheses(cfg, load_universe())
    return cfg


def load_claims() -> pd.DataFrame:
    return pd.read_csv(CONFIG / "claims_to_verify.csv", dtype=str).fillna("")


def _check_condition(c: dict, where: str, cfg: dict, buckets: set, tickers: set, errors: list):
    if c.get("kind") == "manual":
        return
    t = c.get("type")
    if t not in TEST_TYPES:
        errors.append(f"{where}: unknown type {t!r}")
        return
    if t == "all_of":
        for i, sub in enumerate(c.get("conditions", [])):
            _check_condition(sub, f"{where}[{i}]", cfg, buckets, tickers, errors)
        return
    if c.get("op") not in OPS:
        errors.append(f"{where}: bad op {c.get('op')!r}")
    if not isinstance(c.get("threshold"), (int, float)):
        errors.append(f"{where}: threshold must be a number")
    for k in ("group", "group_a", "group_b", "relative_to"):
        if k in c and cfg["groups"].get(c[k]) not in buckets:
            errors.append(f"{where}: group alias {c[k]!r} does not map to a bucket in universe.csv")
    if "ticker" in c and c["ticker"] not in tickers:
        errors.append(f"{where}: ticker {c['ticker']!r} not in universe.csv")
    series = [c.get("series")] + ([c["event"]["series"]] if "event" in c else [])
    for s in filter(None, series):
        if s not in cfg["series"]:
            errors.append(f"{where}: series {s!r} not defined under `series:`")


def validate_hypotheses(cfg: dict, universe: pd.DataFrame):
    errors = []
    buckets, tickers = set(universe.bucket), set(universe.ticker)
    ids = [h["id"] for h in cfg["hypotheses"]]
    if len(ids) != len(set(ids)):
        errors.append("duplicate hypothesis ids")
    for h in cfg["hypotheses"]:
        n = len(h.get("tests", []))
        if not 2 <= n <= 4:
            errors.append(f"{h['id']}: has {n} tests; expected 2-4")
        for t in h.get("tests", []):
            _check_condition(t, t.get("id", h["id"]), cfg, buckets, tickers, errors)
        for s in h.get("confirm_signals", []) + h.get("kill_signals", []):
            _check_condition(s, s.get("id", h["id"]), cfg, buckets, tickers, errors)
    if errors:
        raise ValueError("hypotheses.yaml invalid:\n  " + "\n  ".join(errors))
