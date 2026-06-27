# patur/ledger.py
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
from patur.models import Transaction, Direction

@dataclass(frozen=True)
class LedgerSummary:
    total_income: Decimal
    total_expenses: Decimal
    net_income: Decimal

def summarize(transactions: list[Transaction]) -> LedgerSummary:
    income = sum((t.amount for t in transactions if t.direction == Direction.IN),
                 Decimal("0"))
    expenses = sum(
        (t.amount * Decimal(t.business_pct) / Decimal("100")
         for t in transactions if t.direction == Direction.OUT and t.deductible),
        Decimal("0"))
    return LedgerSummary(income, expenses, income - expenses)
