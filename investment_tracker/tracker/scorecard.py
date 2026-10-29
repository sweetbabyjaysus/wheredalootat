"""Evaluate hypotheses.yaml tests and signals against the run's data."""
from __future__ import annotations

import math
import operator

import pandas as pd

from . import analysis

OPS = {">": operator.gt, ">=": operator.ge, "<": operator.lt, "<=": operator.le, "==": operator.eq, "!=": operator.ne}


class Context:
    def __init__(self, ds, ct: pd.DataFrame, cfg: dict):
        self.ds, self.ct, self.cfg = ds, ct, cfg
        self.returns = analysis.daily_returns(ds.prices)

    def members(self, alias):
        return self.ct[self.ct.bucket == self.cfg["groups"][alias]]

    def group_median(self, metric, alias):
        g = self.members(alias)
        if metric not in g:
            return None, f"metric {metric} not computed"
        vals = pd.to_numeric(g[metric], errors="coerce").dropna()
        need = min(len(g), max(2, math.ceil(len(g) / 2)))
        if len(vals) < need:
            return None, f"{len(vals)}/{len(g)} members have {metric} (need {need})"
        return float(vals.median()), f"median of {len(vals)}/{len(g)}: " + ", ".join(f"{t} {v:.3g}" for t, v in vals.items())

    def series_change(self, name, days, pct=False):
        s = self.ds.macro.get(name)
        if s is None or s.dropna().empty:
            return None, f"series {name} unavailable"
        s = s.dropna()
        last = s.index[-1]
        base = s[s.index <= last - pd.Timedelta(days=days)]
        if base.empty:
            return None, f"{name} has no value {days}d before {last.date()}"
        v = s.iloc[-1] / base.iloc[-1] - 1 if pct else s.iloc[-1] - base.iloc[-1]
        return float(v), f"{name} {base.iloc[-1]:.4g} ({base.index[-1].date()}) -> {s.iloc[-1]:.4g} ({last.date()})"

    def event_mean(self, c):
        days = analysis.event_days(self.ds, c["event"]["series"], c["event"]["direction"], c.get("n", 10))
        if days.empty:
            return None, "event series unavailable"
        r = self.returns

        def mean_for(tickers):
            vals = [r.loc[d, tickers].mean() for d in days.index if d in r.index]
            vals = [v for v in vals if pd.notna(v)]
            return (sum(vals) / len(vals), len(vals)) if vals else (None, 0)

        tick = [c["ticker"]] if "ticker" in c else list(self.members(c["group"]).index)
        v, n = mean_for([t for t in tick if t in r])
        if v is None:
            return None, "no returns on event days"
        detail = f"{'/'.join(tick) if 'ticker' in c else c['group']} mean {v:+.2%} over {n} days"
        if "relative_to" in c:
            b, nb = mean_for([t for t in self.members(c["relative_to"]).index if t in r])
            if b is None:
                return None, "no benchmark returns"
            detail += f" minus {c['relative_to']} {b:+.2%}"
            v -= b
        return float(v), detail


def evaluate(c: dict, ctx: Context) -> dict:
    if c.get("kind") == "manual":
        return {"status": "manual", "value": None, "detail": c.get("how", "check by hand")}
    t = c["type"]
    if t == "all_of":
        subs = [evaluate(s, ctx) for s in c["conditions"]]
        st = [s["status"] for s in subs]
        status = "fail" if "fail" in st else "pass" if all(s == "pass" for s in st) else "n/a"
        return {"status": status, "value": None, "subs": subs,
                "detail": " AND ".join(f"[{s['status']}] {s.get('label', '')}" for s in subs)}
    if t == "group_value":
        v, d = ctx.group_median(c["metric"], c["group"])
        label = f"median {c['metric']} ({c['group']})"
    elif t == "group_diff":
        a, da = ctx.group_median(c["metric"], c["group_a"])
        b, db = ctx.group_median(c["metric"], c["group_b"])
        v = a - b if a is not None and b is not None else None
        d = f"{c['group_a']}: {da} | {c['group_b']}: {db}"
        label = f"{c['metric']}: {c['group_a']} - {c['group_b']}"
    elif t in ("series_change", "series_change_pct"):
        v, d = ctx.series_change(c["series"], c["window_days"], pct=t.endswith("pct"))
        label = f"{c['series']} {'%' if t.endswith('pct') else ''}change {c['window_days']}d"
    elif t == "series_level":
        s = ctx.ds.macro.get(c["series"])
        v = float(s.dropna().iloc[-1]) if s is not None else None
        d, label = f"latest {c['series']}", f"{c['series']} level"
    elif t == "event_mean":
        v, d = ctx.event_mean(c)
        label = f"{c.get('ticker', c.get('group'))} on top {c.get('n', 10)} {c['event']['series']} {c['event']['direction']} days"
    else:
        raise ValueError(t)
    if v is None:
        return {"status": "n/a", "value": None, "detail": d, "label": label, "op": c["op"], "threshold": c["threshold"]}
    ok = OPS[c["op"]](v, c["threshold"])
    return {"status": "pass" if ok else "fail", "value": v, "detail": d, "label": label,
            "op": c["op"], "threshold": c["threshold"]}


def verdict(results: list[dict], rule: dict) -> tuple[str, str]:
    ev = [r for r in results if r["status"] in ("pass", "fail")]
    p = sum(r["status"] == "pass" for r in ev)
    if len(ev) < rule["min_evaluable"]:
        return "Unclear", f"only {len(ev)} test(s) had data"
    frac = p / len(ev)
    why = f"{p}/{len(ev)} evaluable tests pass"
    if frac >= rule["supported_if_pass_fraction_gte"]:
        return "Supported", why
    if frac <= rule["not_supported_if_pass_fraction_lte"]:
        return "Not supported", why
    return rule.get("otherwise", "Unclear"), why


def run(ds, ct, cfg, prev_snapshot: dict | None = None) -> list[dict]:
    ctx = Context(ds, ct, cfg)
    out = []
    prev_v = {h["id"]: h for h in (prev_snapshot or {}).get("hypotheses", [])}
    for h in cfg["hypotheses"]:
        rule = {**cfg["verdict_rule"], **h.get("verdict_rule", {})}
        tests = [{"id": t["id"], "name": t["name"], **evaluate(t, ctx)} for t in h["tests"]]
        v, why = verdict(tests, rule)
        sigs = []
        for kind in ("confirm_signals", "kill_signals"):
            for s in h.get(kind, []):
                r = evaluate(s, ctx)
                sigs.append({"id": s["id"], "kind": kind.split("_")[0], "name": s["name"], **r,
                             "live": r["status"] == "pass"})
        p = prev_v.get(h["id"])
        out.append({"id": h["id"], "name": h["name"], "statement": " ".join(h["statement"].split()),
                    "verdict": v, "why": why, "tests": tests, "signals": sigs,
                    "prev_verdict": p["verdict"] if p else None, "prev_date": (prev_snapshot or {}).get("date")})
    return out
