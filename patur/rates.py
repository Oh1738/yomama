from __future__ import annotations
import json
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

@dataclass(frozen=True)
class TaxBracket:
    upper: Decimal | None
    rate: Decimal

@dataclass(frozen=True)
class BituachBracket:
    upper: Decimal | None
    rate: Decimal

@dataclass(frozen=True)
class RatesYear:
    year: int
    patur_ceiling: Decimal
    income_tax_brackets: list[TaxBracket]
    credit_point_value: Decimal
    pension_eligible_income_cap: Decimal
    pension_deduction_pct: Decimal
    pension_credit_pct: Decimal
    pension_credit_rate: Decimal
    pension_total_cap_pct: Decimal
    bituach_brackets: list[BituachBracket]
    bituach_income_ceiling: Decimal

def _d(x: str | None) -> Decimal | None:
    return None if x is None else Decimal(x)

def load_rates(year: int, rates_dir: str | None = None) -> RatesYear:
    base = Path(rates_dir) if rates_dir is not None else Path(__file__).resolve().parent.parent / "rates"
    data = json.loads((base / f"{year}.json").read_text(encoding="utf-8"))
    return RatesYear(
        year=int(data["year"]),
        patur_ceiling=Decimal(data["patur_ceiling"]),
        income_tax_brackets=[TaxBracket(_d(b["upper"]), Decimal(b["rate"]))
                             for b in data["income_tax_brackets"]],
        credit_point_value=Decimal(data["credit_point_value"]),
        pension_eligible_income_cap=Decimal(data["pension_eligible_income_cap"]),
        pension_deduction_pct=Decimal(data["pension_deduction_pct"]),
        pension_credit_pct=Decimal(data["pension_credit_pct"]),
        pension_credit_rate=Decimal(data["pension_credit_rate"]),
        pension_total_cap_pct=Decimal(data["pension_total_cap_pct"]),
        bituach_brackets=[BituachBracket(_d(b["upper"]), Decimal(b["rate"]))
                          for b in data["bituach_brackets"]],
        bituach_income_ceiling=Decimal(data["bituach_income_ceiling"]),
    )
