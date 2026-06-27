# tests/test_ledger.py
from datetime import date
from decimal import Decimal
from patur.models import Transaction, Direction
from patur.ledger import summarize

def tx(direction, amount, deductible=False, business_pct=100):
    return Transaction(date=date(2026,1,1), direction=direction,
                       amount=Decimal(amount), description="d",
                       source="s", external_id=str(id(amount))+str(amount),
                       deductible=deductible, business_pct=business_pct)

def test_net_income_with_partial_business_use():
    txs = [tx(Direction.IN, "10000"),
           tx(Direction.OUT, "1000", deductible=True, business_pct=100),
           tx(Direction.OUT, "500",  deductible=True, business_pct=50),   # counts 250
           tx(Direction.OUT, "999",  deductible=False)]                   # ignored
    s = summarize(txs)
    assert s.total_income == Decimal("10000")
    assert s.total_expenses == Decimal("1250")
    assert s.net_income == Decimal("8750")
