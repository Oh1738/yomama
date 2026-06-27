# tests/test_reports.py
from datetime import date
from decimal import Decimal
from patur.models import Transaction, Direction
from patur.rates import load_rates
from patur.reports import build_report

R = load_rates(2026)

def tx(direction, amount, deductible=False):
    return Transaction(date=date(2026,1,1), direction=direction,
                       amount=Decimal(amount), description="d",
                       source="s", external_id=f"{direction}{amount}",
                       deductible=deductible)

def test_report_wires_modules():
    txs = [tx(Direction.IN, "100000"), tx(Direction.OUT, "10000", deductible=True)]
    rep = build_report(txs, Decimal("0"), Decimal("2.25"), R)
    assert rep.ledger.net_income == Decimal("90000")
    assert rep.ceiling.ytd_revenue == Decimal("100000")
    assert rep.liability.net_income == Decimal("90000")
    assert rep.liability.total_due == rep.liability.income_tax + rep.liability.bituach_leumi
