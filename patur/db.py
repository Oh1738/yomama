from __future__ import annotations
import sqlite3
from datetime import date
from decimal import Decimal
from patur.models import Transaction, Direction

def connect(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn

def init_schema(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            direction TEXT NOT NULL,
            amount TEXT NOT NULL,
            description TEXT NOT NULL,
            source TEXT NOT NULL,
            external_id TEXT NOT NULL,
            category TEXT,
            deductible INTEGER NOT NULL DEFAULT 0,
            business_pct INTEGER NOT NULL DEFAULT 100,
            UNIQUE(source, external_id)
        )""")
    conn.commit()

def insert_transactions(conn: sqlite3.Connection, txs: list[Transaction]) -> int:
    inserted = 0
    for t in txs:
        cur = conn.execute(
            """INSERT OR IGNORE INTO transactions
               (date,direction,amount,description,source,external_id,
                category,deductible,business_pct)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (t.date.isoformat(), t.direction.value, str(t.amount), t.description,
             t.source, t.external_id, t.category, int(t.deductible), t.business_pct))
        inserted += cur.rowcount
    conn.commit()
    return inserted

def all_transactions(conn: sqlite3.Connection) -> list[Transaction]:
    rows = conn.execute("SELECT * FROM transactions ORDER BY id").fetchall()
    return [Transaction(
        date=date.fromisoformat(r["date"]),
        direction=Direction(r["direction"]),
        amount=Decimal(r["amount"]),
        description=r["description"],
        source=r["source"],
        external_id=r["external_id"],
        category=r["category"],
        deductible=bool(r["deductible"]),
        business_pct=r["business_pct"],
    ) for r in rows]
