from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from patur.models import Transaction, Direction, replace_tx

@dataclass(frozen=True)
class CategoryRule:
    pattern: str
    category: str
    deductible: bool
    business_pct: int = 100

def load_rules(path: str | None = None) -> list[CategoryRule]:
    resolved = Path(path) if path is not None else Path(__file__).resolve().parent.parent / "rules" / "default.json"
    data = json.loads(resolved.read_text(encoding="utf-8"))
    return [CategoryRule(d["pattern"], d["category"], d["deductible"],
                         d.get("business_pct", 100)) for d in data]

def categorize(tx: Transaction, rules: list[CategoryRule]) -> Transaction:
    if tx.direction == Direction.IN:
        return tx
    desc = tx.description.lower()
    for r in rules:
        if r.pattern.lower() in desc:
            return replace_tx(tx, category=r.category,
                              deductible=r.deductible, business_pct=r.business_pct)
    return replace_tx(tx, category="uncategorized")
