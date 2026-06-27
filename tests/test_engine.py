# tests/test_engine.py
from decimal import Decimal
from patur.rates import load_rates
from patur.tax_engine.engine import compute_liability

R = load_rates(2026)

def test_pension_reduces_taxable_and_tax():
    no_p = compute_liability(Decimal("120000"), Decimal("0"), Decimal("2.25"), R)
    with_p = compute_liability(Decimal("120000"), Decimal("19200"), Decimal("2.25"), R)
    assert with_p.taxable_income < no_p.taxable_income
    assert with_p.total_due <= no_p.total_due

def test_total_is_income_tax_plus_bituach():
    res = compute_liability(Decimal("120000"), Decimal("19200"), Decimal("2.25"), R)
    assert res.total_due == res.income_tax + res.bituach_leumi
