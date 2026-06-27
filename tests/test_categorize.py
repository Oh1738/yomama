from datetime import date
from decimal import Decimal
from patur.models import Transaction, Direction
from patur.categorize import CategoryRule, categorize

RULES = [CategoryRule("שרת", "תשתית", True, 100),
         CategoryRule("קפה", "אש\"ל", False, 0)]

def expense(desc):
    return Transaction(date=date(2026,1,1), direction=Direction.OUT,
                       amount=Decimal("10"), description=desc,
                       source="leumi", external_id=desc)

def test_matches_first_rule():
    out = categorize(expense("תשלום שרת חודשי"), RULES)
    assert out.category == "תשתית" and out.deductible is True
    assert out.business_pct == 100

def test_first_rule_wins():
    out = categorize(expense("שרת עם קפה"), RULES)
    assert out.category == "תשתית"      # rule 0, not rule 1
    assert out.deductible is True

def test_no_match_is_uncategorized():
    assert categorize(expense("משהו אחר"), RULES).category == "uncategorized"

def test_income_untouched():
    inc = Transaction(date=date(2026,1,1), direction=Direction.IN,
                      amount=Decimal("10"), description="x",
                      source="gi", external_id="gi:1", category="הכנסה")
    assert categorize(inc, RULES).category == "הכנסה"
