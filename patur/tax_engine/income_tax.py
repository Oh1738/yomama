from __future__ import annotations
from decimal import Decimal
from patur.rates import TaxBracket

def income_tax(taxable: Decimal, brackets: list[TaxBracket]) -> Decimal:
    tax = Decimal("0")
    lower = Decimal("0")
    for b in brackets:
        if taxable <= lower:
            break
        top = taxable if b.upper is None else min(taxable, b.upper)
        tax += (top - lower) * b.rate
        if b.upper is None:
            break
        lower = b.upper
    return tax

def apply_credit_points(tax: Decimal, points: Decimal, point_value: Decimal) -> Decimal:
    return max(tax - points * point_value, Decimal("0"))
