"""Same-day disk cache and polite retry, so re-runs don't hammer free APIs."""
from __future__ import annotations

import datetime as dt
import hashlib
import pickle
import time

from .config import ROOT

CACHE = ROOT / "output" / "cache"
PAUSE_S = 0.4          # pause after every live call


def _path(key: str):
    d = CACHE / dt.date.today().isoformat()
    d.mkdir(parents=True, exist_ok=True)
    return d / (hashlib.sha1(key.encode()).hexdigest()[:20] + ".pkl")


def cached(key: str, fn, *args, retries: int = 4, **kwargs):
    p = _path(key)
    if p.exists():
        return pickle.loads(p.read_bytes())
    for attempt in range(retries + 1):
        try:
            val = fn(*args, **kwargs)
            break
        except Exception as e:  # rate limits surface as varied exception types
            msg = str(e).lower()
            if attempt == retries or not any(w in msg for w in ("429", "rate", "too many", "timed out", "timeout")):
                raise
            time.sleep(5 * 2 ** attempt)
    time.sleep(PAUSE_S)
    try:
        p.write_bytes(pickle.dumps(val))
    except Exception:
        pass  # unpicklable result: just don't cache it
    return val
