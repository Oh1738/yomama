from decimal import Decimal
from patur.rates import load_rates, TaxBracket

def test_loads_2026_core_values():
    r = load_rates(2026)
    assert r.year == 2026
    assert r.patur_ceiling == Decimal("122833")
    assert r.pension_eligible_income_cap == Decimal("232800")
    assert r.pension_deduction_pct == Decimal("0.11")
    assert r.pension_credit_pct == Decimal("0.05")
    assert r.pension_credit_rate == Decimal("0.35")
    assert isinstance(r.income_tax_brackets[0], TaxBracket)
    # top income-tax bracket is open-ended
    assert r.income_tax_brackets[-1].upper is None
    # top bituach bracket is also open-ended
    assert r.bituach_brackets[-1].upper is None

def test_decimals_not_floats():
    r = load_rates(2026)
    assert all(isinstance(b.rate, Decimal) for b in r.income_tax_brackets)
    assert all(isinstance(b.rate, Decimal) for b in r.bituach_brackets)

def test_loads_remaining_scalar_values():
    r = load_rates(2026)
    assert r.credit_point_value == Decimal("2976")
    assert r.pension_total_cap_pct == Decimal("0.165")
    assert r.bituach_income_ceiling == Decimal("594828")
