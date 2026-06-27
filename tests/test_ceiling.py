# tests/test_ceiling.py
from decimal import Decimal
from patur.rates import load_rates
from patur.ceiling import ceiling_status

R = load_rates(2026)  # ceiling 122833

def test_alert_at_80pct():
    s = ceiling_status(Decimal("100000"), R)
    assert s.alert is True and s.breached is False

def test_breach():
    s = ceiling_status(Decimal("130000"), R)
    assert s.breached is True

def test_quiet_below_threshold():
    assert ceiling_status(Decimal("50000"), R).alert is False

def test_alert_at_exact_80pct():
    # exactly 80% of the ceiling -> alert is True (>= boundary)
    s = ceiling_status(R.patur_ceiling * Decimal("0.8"), R)
    assert s.alert is True
    assert s.breached is False

def test_breach_also_alerts():
    s = ceiling_status(Decimal("130000"), R)
    assert s.breached is True
    assert s.alert is True
