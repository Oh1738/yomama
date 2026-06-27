# patur/advances.py
from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from patur.models import Transaction
from patur.rates import RatesYear
from patur.ledger import summarize
from patur.tax_engine.engine import compute_liability

@dataclass(frozen=True)
class AdvanceRecommendation:
    months: int
    window_net: Decimal
    avg_monthly_net: Decimal
    projected_annual_net: Decimal
    projected_annual_income_tax: Decimal
    monthly_advance: Decimal

def _window_start(as_of: date, months: int) -> date:
    idx = as_of.year * 12 + (as_of.month - 1) - (months - 1)
    return date(idx // 12, idx % 12 + 1, 1)

def recommend_advance(transactions: list[Transaction], as_of: date, rates: RatesYear,
                      pension_contribution: Decimal, credit_points: Decimal,
                      months: int = 3) -> AdvanceRecommendation:
    start = _window_start(as_of, months)
    window = [t for t in transactions if start <= t.date <= as_of]
    window_net = summarize(window).net_income
    avg_monthly = window_net / Decimal(months)
    projected_annual = avg_monthly * Decimal("12")
    liability = compute_liability(projected_annual, pension_contribution,
                                  credit_points, rates)
    monthly_advance = (liability.income_tax / Decimal("12")).quantize(Decimal("0.01"))
    return AdvanceRecommendation(months, window_net, avg_monthly, projected_annual,
                                 liability.income_tax, monthly_advance)
