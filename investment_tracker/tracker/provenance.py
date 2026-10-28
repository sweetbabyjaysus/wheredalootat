"""Every number carries its source and as-of date. Missing numbers become gaps, never guesses."""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class Datum:
    entity: str          # ticker or series id
    field: str
    value: Any
    source: str          # e.g. "yfinance:info.forwardPE", "SEC companyfacts us-gaap:Revenues"
    as_of: str           # date the value refers to (ISO)
    unit: str = ""
    note: str = ""       # "computed", "proxy", "inference", ...


@dataclass
class Ledger:
    data: list[Datum] = field(default_factory=list)
    gaps: list[dict] = field(default_factory=list)

    def add(self, entity, field_, value, source, as_of, unit="", note=""):
        if value is None or (isinstance(value, float) and value != value):
            self.gap(entity, field_, f"{source} returned no value")
            return None
        if isinstance(as_of, (dt.date, dt.datetime)):
            as_of = as_of.date().isoformat() if isinstance(as_of, dt.datetime) else as_of.isoformat()
        self.data.append(Datum(entity, field_, value, source, str(as_of), unit, note))
        return value

    def gap(self, entity, field_, reason):
        self.gaps.append({"entity": entity, "field": field_, "reason": reason,
                          "logged": dt.date.today().isoformat()})

    def get(self, entity, field_):
        for d in reversed(self.data):
            if d.entity == entity and d.field == field_:
                return d.value
        return None

    def to_records(self):
        return [asdict(d) for d in self.data]
