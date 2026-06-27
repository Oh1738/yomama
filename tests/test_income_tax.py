from decimal import Decimal
from patur.rates import TaxBracket
from patur.tax_engine.income_tax import income_tax, apply_credit_points

B = [TaxBracket(Decimal("84120"), Decimal("0.10")),
     TaxBracket(Decimal("120720"), Decimal("0.14")),
     TaxBracket(None, Decimal("0.20"))]

def test_progressive_within_first_bracket():
    assert income_tax(Decimal("50000"), B) == Decimal("5000.00")

def test_spans_brackets():
    # 84120*0.10 + (100000-84120)*0.14 = 8412 + 2223.20 = 10635.20
    assert income_tax(Decimal("100000"), B) == Decimal("10635.20")

def test_open_ended_top_bracket():
    # 84120*0.10 + (120720-84120)*0.14 + (150000-120720)*0.20
    # = 8412 + 5124 + 5856 = 19392
    assert income_tax(Decimal("150000"), B) == Decimal("19392")

def test_income_at_bracket_boundary():
    # exactly at the first ceiling: belongs entirely to the 10% bracket
    assert income_tax(Decimal("84120"), B) == Decimal("8412")

def test_zero_income():
    assert income_tax(Decimal("0"), B) == Decimal("0")

def test_credit_points_floor_at_zero():
    assert apply_credit_points(Decimal("1000"), Decimal("2.25"),
                               Decimal("2976")) == Decimal("0")
