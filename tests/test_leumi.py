from decimal import Decimal
from patur.models import Direction
from patur.importers.leumi import parse_leumi_csv

CSV = "תאריך,תיאור,חובה,זכות,יתרה\n" \
      "05/01/2026,העברה מלקוח,,1000.00,1000.00\n" \
      "06/01/2026,תשלום שרת,150.00,,850.00\n"

def test_parses_debit_only():
    txs = parse_leumi_csv(CSV)
    assert len(txs) == 1
    assert txs[0].direction == Direction.OUT
    assert txs[0].amount == Decimal("150.00")
    assert txs[0].source == "leumi"

def test_external_id_is_stable():
    assert parse_leumi_csv(CSV)[0].external_id == parse_leumi_csv(CSV)[0].external_id

def test_skips_rows_with_no_amount():
    csv_with_empty = ("תאריך,תיאור,חובה,זכות,יתרה\n"
                      "07/01/2026,פריט ריק,,,900.00\n")
    assert parse_leumi_csv(csv_with_empty) == []
