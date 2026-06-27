# patur/obligations.py
from __future__ import annotations
from dataclasses import dataclass
from datetime import date

@dataclass(frozen=True)
class Obligation:
    name: str
    due: date

def obligations_for_year(year: int) -> list[Obligation]:
    return [
        Obligation("הצהרת מחזור שנתית", date(year + 1, 1, 31)),
        Obligation("דוח שנתי (1301)", date(year + 1, 4, 30)),
    ]
