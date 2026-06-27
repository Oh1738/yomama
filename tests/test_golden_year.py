from decimal import Decimal
from pathlib import Path
from patur.importers.green_invoice import parse_green_invoice_csv
from patur.categorize import load_rules, categorize
from patur.rates import load_rates
from patur.reports import build_report

def test_golden_year_end_to_end():
    fixture = Path(__file__).parent / "fixtures" / "golden_year_2026.csv"
    text = fixture.read_text(encoding="utf-8")
    rules = load_rules()
    txs = [categorize(t, rules) for t in parse_green_invoice_csv(text)]
    rep = build_report(txs, Decimal("0"), Decimal("2.25"), load_rates(2026))
    # 4 invoices of 25,000 = 100,000 income, no expenses
    assert rep.ledger.total_income == Decimal("100000.00")
    assert rep.ledger.net_income == Decimal("100000.00")
    assert rep.ceiling.alert is True          # 100000/122833 = 81.4%
    assert rep.liability.total_due > Decimal("0")
    # regression anchor: snapshot current engine output (update only on intended change)
    assert rep.liability.income_tax == Decimal("3939.2000")
