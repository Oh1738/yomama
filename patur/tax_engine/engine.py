# patur/tax_engine/engine.py
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
from patur.rates import RatesYear
from patur.tax_engine.income_tax import income_tax, apply_credit_points
from patur.tax_engine.pension import pension_benefit, PensionResult
from patur.tax_engine.bituach_leumi import bituach_leumi

@dataclass(frozen=True)
class TaxLiability:
    net_income: Decimal
    taxable_income: Decimal
    income_tax: Decimal
    bituach_leumi: Decimal
    pension: PensionResult
    total_due: Decimal

def compute_liability(net_income: Decimal, pension_contribution: Decimal,
                      credit_points: Decimal, rates: RatesYear) -> TaxLiability:
    pension = pension_benefit(net_income, pension_contribution, rates)
    taxable = net_income - pension.deduction_amount
    tax = income_tax(taxable, rates.income_tax_brackets)
    tax = apply_credit_points(tax, credit_points, rates.credit_point_value)
    tax = max(tax - pension.credit_amount, Decimal("0"))
    bl = bituach_leumi(net_income, rates)
    return TaxLiability(net_income, taxable, tax, bl, pension, tax + bl)
