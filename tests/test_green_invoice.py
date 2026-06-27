from decimal import Decimal
from patur.models import Direction
from patur.importers.green_invoice import parse_green_invoice_csv

CSV = "מספר מסמך,תאריך,סכום,לקוח\n" \
      "1001,10/01/2026,2500.00,חברת אבג\n"

def test_income_rows():
    txs = parse_green_invoice_csv(CSV)
    assert len(txs) == 1
    t = txs[0]
    assert t.direction == Direction.IN and t.amount == Decimal("2500.00")
    assert t.source == "green_invoice" and t.external_id == "gi:1001"
    assert t.category == "הכנסה"
    assert t.description == "חברת אבג"

def test_empty_doc_skipped():
    csv_skip = ("מספר מסמך,תאריך,סכום,לקוח\n"
                ",10/01/2026,100.00,אנון\n"
                "1002,10/01/2026,500.00,חברת בגד\n")
    txs = parse_green_invoice_csv(csv_skip)
    assert len(txs) == 1
    assert txs[0].external_id == "gi:1002"
