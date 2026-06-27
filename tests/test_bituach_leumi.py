from decimal import Decimal
from patur.rates import load_rates, RatesYear, BituachBracket
from patur.tax_engine.bituach_leumi import bituach_leumi

def rates_with(brackets, ceiling):
    base = load_rates(2026)
    return RatesYear(**{**base.__dict__,
                        "bituach_brackets": brackets,
                        "bituach_income_ceiling": ceiling})

def test_two_tier_progressive():
    R = rates_with([BituachBracket(Decimal("100000"), Decimal("0.05")),
                    BituachBracket(None, Decimal("0.10"))], Decimal("400000"))
    # 100000*0.05 + (150000-100000)*0.10 = 5000 + 5000 = 10000
    assert bituach_leumi(Decimal("150000"), R) == Decimal("10000.00")

def test_income_ceiling_applied():
    R = rates_with([BituachBracket(None, Decimal("0.10"))], Decimal("100000"))
    assert bituach_leumi(Decimal("999999"), R) == Decimal("10000.0")
