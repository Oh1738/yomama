from __future__ import annotations
from dataclasses import dataclass, replace
from datetime import date
from decimal import Decimal
from enum import Enum

class Direction(str, Enum):
    IN = "in"
    OUT = "out"

@dataclass(frozen=True)
class Transaction:
    date: date
    direction: Direction
    amount: Decimal
    description: str
    source: str
    external_id: str
    category: str | None = None
    deductible: bool = False
    business_pct: int = 100

    def __post_init__(self) -> None:
        if self.amount <= 0:
            raise ValueError(f"amount must be positive, got {self.amount!r}")
        if not (0 <= self.business_pct <= 100):
            raise ValueError(f"business_pct must be 0-100, got {self.business_pct}")

def replace_tx(tx: Transaction, **changes) -> Transaction:
    return replace(tx, **changes)
