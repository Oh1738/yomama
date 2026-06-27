from __future__ import annotations
from decimal import Decimal
from patur.rates import RatesYear

def bituach_leumi(net_income: Decimal, rates: RatesYear) -> Decimal:
    income = min(net_income, rates.bituach_income_ceiling)
    due = Decimal("0")
    lower = Decimal("0")
    for b in rates.bituach_brackets:
        if income <= lower:
            break
        top = income if b.upper is None else min(income, b.upper)
        due += (top - lower) * b.rate
        if b.upper is None:
            break
        lower = b.upper
    return due
