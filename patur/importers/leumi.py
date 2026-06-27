from __future__ import annotations
import csv, hashlib
from datetime import datetime
from decimal import Decimal
from io import StringIO
from patur.models import Transaction, Direction

def _id(row: dict) -> str:
    raw = "|".join(str(row.get(k, "")) for k in ("תאריך","תיאור","חובה","זכות","יתרה"))
    return "leumi:" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]

def parse_leumi_csv(text: str) -> list[Transaction]:
    out: list[Transaction] = []
    for row in csv.DictReader(StringIO(text)):
        debit = (row.get("חובה") or "").strip()
        if not debit:
            continue
        direction, amount = Direction.OUT, Decimal(debit)
        out.append(Transaction(
            date=datetime.strptime(row["תאריך"].strip(), "%d/%m/%Y").date(),
            direction=direction, amount=amount,
            description=(row.get("תיאור") or "").strip(),
            source="leumi", external_id=_id(row)))
    return out
