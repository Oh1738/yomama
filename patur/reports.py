# patur/reports.py
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
from patur.models import Transaction
from patur.rates import RatesYear
from patur.ledger import summarize, LedgerSummary
from patur.tax_engine.engine import compute_liability, TaxLiability
from patur.ceiling import ceiling_status, CeilingStatus

@dataclass(frozen=True)
class Report:
    ledger: LedgerSummary
    liability: TaxLiability
    ceiling: CeilingStatus

def build_report(transactions: list[Transaction], pension_contribution: Decimal,
                 credit_points: Decimal, rates: RatesYear) -> Report:
    ledger = summarize(transactions)
    liability = compute_liability(ledger.net_income, pension_contribution,
                                  credit_points, rates)
    ceiling = ceiling_status(ledger.total_income, rates)
    return Report(ledger, liability, ceiling)
