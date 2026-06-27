from decimal import Decimal
from patur.rates import load_rates
from patur.tax_engine.pension import pension_benefit

R = load_rates(2026)

def test_full_benefit_at_16pct_contribution():
    # net 120000: deduction 11% = 13200; credit base 5% = 6000 -> credit 6000*0.35 = 2100
    res = pension_benefit(Decimal("120000"), Decimal("19200"), R)
    assert res.deduction_amount == Decimal("13200.00")
    assert res.credit_amount == Decimal("2100.0000")
    assert res.eligible_income == Decimal("120000")
    assert res.benefited_contribution == Decimal("19200")

def test_eligible_income_capped():
    res = pension_benefit(Decimal("500000"), Decimal("100000"), R)
    assert res.eligible_income == Decimal("232800")

def test_over_contribution_warns():
    res = pension_benefit(Decimal("120000"), Decimal("50000"), R)
    assert any("יתר" in w or "over" in w.lower() for w in res.warnings)
