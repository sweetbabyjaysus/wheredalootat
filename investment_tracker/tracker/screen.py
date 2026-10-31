"""Evidence screen from config/screen.yaml. Shows where the case looks strongest on paper;
it is not a forecast or a recommendation."""
from __future__ import annotations

import operator

import pandas as pd
import yaml

from .config import CONFIG

OPS = {">": operator.gt, ">=": operator.ge, "<": operator.lt, "<=": operator.le}


def load() -> dict:
    return yaml.safe_load((CONFIG / "screen.yaml").read_text())


def _test(row, c):
    v = row.get(c["metric"])
    if v is None or pd.isna(v):
        return c.get("missing_counts_as", "n/a")
    return "pass" if OPS[c["op"]](v, c["threshold"]) else "fail"


def run(ct: pd.DataFrame, scores: pd.DataFrame, prev: dict | None) -> pd.DataFrame:
    cfg = load()
    d = ct.join(scores[["sentiment_score", "fundamentals_score"]], how="left")
    rows = []
    prev_pass = (prev or {}).get("screen", {})
    for tk, r in d.iterrows():
        res = {c["id"]: _test(r, c) for c in cfg["checks"]}
        passes = sum(v == "pass" for v in res.values())
        flags = [f["label"] for f in cfg.get("flags", [])
                 if _test(r, f) == "pass" and ("also_require" not in f or _test(r, f["also_require"]) == "pass")]
        p = prev_pass.get(tk)
        rows.append({"ticker": tk, "company": r.get("company"), "bucket": r.get("bucket"),
                     "passes": passes, "of": len(cfg["checks"]),
                     "change": "" if p is None else (f"{passes - p:+d}" if passes != p else "="),
                     **{f"chk_{k}": v for k, v in res.items()},
                     **{c["metric"]: r.get(c["metric"]) for c in cfg["checks"]},
                     "ret_1m": r.get("ret_1m"), "forward_pe": r.get("forward_pe"),
                     "flags": "; ".join(flags)})
    out = pd.DataFrame(rows).set_index("ticker")
    return out.sort_values(["passes", "fundamentals_score"], ascending=False)
