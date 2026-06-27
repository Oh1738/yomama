import pytest
from datetime import date
from decimal import Decimal
from patur.models import Transaction, Direction, replace_tx

def make_tx(**kw):
    base = dict(date=date(2026, 1, 5), direction=Direction.IN,
                amount=Decimal("100.00"), description="x",
                source="leumi", external_id="a1")
    base.update(kw)
    return Transaction(**base)

def test_defaults():
    tx = make_tx()
    assert tx.category is None and tx.deductible is False and tx.business_pct == 100

def test_replace_returns_new_with_change():
    tx = make_tx()
    out = replace_tx(tx, category="ציוד", deductible=True)
    assert out.category == "ציוד" and out.deductible is True
    assert tx.category is None  # original unchanged (frozen)

def test_negative_amount_rejected():
    with pytest.raises(ValueError):
        make_tx(amount=Decimal("-1.00"))

def test_zero_amount_rejected():
    with pytest.raises(ValueError):
        make_tx(amount=Decimal("0"))

def test_business_pct_out_of_range_rejected():
    with pytest.raises(ValueError):
        make_tx(business_pct=101)
