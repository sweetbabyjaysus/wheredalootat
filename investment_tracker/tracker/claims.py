"""Check newsletter / premise figures in claims_to_verify.csv against the data."""
from __future__ import annotations

import pandas as pd


def _params(s):
    return dict(kv.split("=", 1) for kv in s.split(";") if "=" in kv)


def check(claims: pd.DataFrame, ds) -> pd.DataFrame:
    rows = []
    for _, c in claims.iterrows():
        p, res = _params(c.params), {"claim_id": c.claim_id, "subject": c.subject, "claim": c.claim,
                                     "source_of_claim": c.source_of_claim,
                                     "check_type": c.check_type}
        try:
            res.update(_one(c, p, ds))
        except Exception as e:
            res.update(status="error", actual=None, detail=f"{type(e).__name__}: {e}")
        rows.append(res)
    return pd.DataFrame(rows)


def _one(c, p, ds):
    if c.check_type == "manual":
        return {"status": "manual", "actual": None, "detail": c.params}
    if c.check_type == "move_in_window":
        # Newsletter "sell-off" moves often span several sessions and time zones, so test both the
        # closest single-day move inside the window and the cumulative move over the window.
        px = ds.prices.get(c.subject)
        a, b = (pd.Timestamp(x) for x in p["window"].split(":"))
        if px is None:
            return {"status": "no data", "actual": None, "detail": "no prices"}
        r = px.pct_change(fill_method=None)
        w = r[(r.index >= a) & (r.index <= b)].dropna()
        pre = px[px.index < a]
        if w.empty or pre.empty:
            return {"status": "no data", "actual": None, "detail": f"no closes in {a.date()}..{b.date()}"}
        exp, tol = float(p["expected"]), float(p["tol"])
        day = (w - exp).abs().idxmin()
        cum = px[px.index <= b].iloc[-1] / pre.iloc[-1] - 1
        days = ", ".join(f"{d:%m-%d} {v:+.1%}" for d, v in w.items())
        if abs(w[day] - exp) <= tol:
            return {"status": "matches", "actual": float(w[day]), "detail": f"single day {day.date()}; daily: {days}"}
        if abs(cum - exp) <= max(tol, 0.02):
            return {"status": "matches", "actual": float(cum),
                    "detail": f"cumulative {pre.index[-1].date()}..{b.date()} (not one day); daily: {days}"}
        return {"status": "differs", "actual": float(w[day]),
                "detail": f"closest day {day.date()}; cumulative {cum:+.1%}; daily: {days}"}
    if c.check_type == "latest_quarter_yoy":
        f = ds.fund.get(c.subject)
        col = p["concept"]
        s = f[col].dropna() if f is not None and col in f else pd.Series(dtype=float)
        if len(s) < 5:
            return {"status": "no data", "actual": None, "detail": f"need 5 quarters of {col}"}
        from .metrics import lag
        prior = lag(s, 4).iloc[-1]
        actual = s.iloc[-1] / prior - 1
        ok = abs(actual - float(p["expected"])) <= float(p["tol"])
        return {"status": "matches" if ok else "differs", "actual": actual,
                "detail": f"{col} quarter ending {s.index[-1].date()} vs a year earlier"}
    if c.check_type == "series_yoy":
        s = ds.macro[p["series"]].dropna()
        prior = s[s.index <= s.index[-1] - pd.DateOffset(months=12)].iloc[-1]
        actual = s.iloc[-1] / prior - 1
        ok = abs(actual - float(p["expected"])) <= float(p["tol"])
        return {"status": "matches" if ok else "differs", "actual": actual, "detail": f"{p['series']} YoY to {s.index[-1].date()}"}
    if c.check_type == "series_level":
        s = ds.macro[p["series"]].dropna()
        ok = s.iloc[-1] > float(p["threshold"]) if p["op"] == ">" else s.iloc[-1] < float(p["threshold"])
        return {"status": "matches" if ok else "differs", "actual": s.iloc[-1],
                "detail": f"{p['series']} on {s.index[-1].date()}; 1y max {s[s.index >= s.index[-1] - pd.Timedelta(days=365)].max():.2f}"}
    if c.check_type == "series_at_max":
        s = ds.macro[p["series"]].dropna()
        if p.get("lookback") == "all" and p["series"].startswith("JGB_"):
            from .cache import cached
            from .sources import mof
            tenor = p["series"].split("_")[1]
            s = cached(f"mof:{tenor}:all", mof.tenor, tenor, "1970-01-01").dropna()
        mx, at = s.max(), s.idxmax()
        ok = s.iloc[-1] >= mx - 1e-9 or (s.index[-1] - at).days <= 30
        return {"status": "matches" if ok else "differs", "actual": s.iloc[-1],
                "detail": f"series max {mx:.3f} on {at.date()} over data since {s.index[0].date()}"}
    return {"status": "unknown check", "actual": None, "detail": c.check_type}
