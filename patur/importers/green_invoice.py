from __future__ import annotations
import csv
from datetime import datetime
from decimal import Decimal
from io import StringIO
from patur.models import Transaction, Direction

def parse_green_invoice_csv(text: str) -> list[Transaction]:
    out: list[Transaction] = []
    for row in csv.DictReader(StringIO(text)):
        doc = (row.get("מספר מסמך") or "").strip()
        if not doc:
            continue
        out.append(Transaction(
            date=datetime.strptime(row["תאריך"].strip(), "%d/%m/%Y").date(),
            direction=Direction.IN, amount=Decimal((row["סכום"]).strip()),
            description=(row.get("לקוח") or "").strip(),
            source="green_invoice", external_id=f"gi:{doc}", category="הכנסה"))
    return out
