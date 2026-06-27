from datetime import date
from decimal import Decimal
from patur import db
from patur.models import Transaction, Direction

def tx(eid, amount="100.00", direction=Direction.IN):
    return Transaction(date=date(2026,1,1), direction=direction,
                       amount=Decimal(amount), description="d",
                       source="leumi", external_id=eid)

def test_insert_and_read_roundtrip():
    conn = db.connect(":memory:"); db.init_schema(conn)
    n = db.insert_transactions(conn, [tx("a"), tx("b")])
    assert n == 2
    rows = db.all_transactions(conn)
    assert {r.external_id for r in rows} == {"a", "b"}
    assert rows[0].amount == Decimal("100.00")  # Decimal preserved

def test_dedupe_on_source_external_id():
    conn = db.connect(":memory:"); db.init_schema(conn)
    db.insert_transactions(conn, [tx("a")])
    n = db.insert_transactions(conn, [tx("a"), tx("c")])
    assert n == 1  # "a" ignored, "c" inserted
    assert len(db.all_transactions(conn)) == 2
