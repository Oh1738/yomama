from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
from patur.rates import RatesYear

@dataclass(frozen=True)
class PensionResult:
    eligible_income: Decimal
    deduction_amount: Decimal
    credit_amount: Decimal
    benefited_contribution: Decimal
    warnings: list[str]

def pension_benefit(net_income: Decimal, contribution: Decimal,
                    rates: RatesYear) -> PensionResult:
    eligible = min(net_income, rates.pension_eligible_income_cap)
    deduction_cap = rates.pension_deduction_pct * eligible
    credit_cap = rates.pension_credit_pct * eligible
    total_cap = rates.pension_total_cap_pct * eligible

    deduction = min(contribution, deduction_cap)
    credit_base = min(max(contribution - deduction, Decimal("0")), credit_cap)
    credit = credit_base * rates.pension_credit_rate
    benefited = deduction + credit_base

    warnings: list[str] = []
    if contribution > total_cap:
        warnings.append("הפקדה ביתר: מעבר לתקרת ההטבה — החלק העודף אינו מזכה בהטבת מס")
    return PensionResult(
        eligible_income=eligible,
        deduction_amount=deduction,
        credit_amount=credit,
        benefited_contribution=benefited,
        warnings=warnings,
    )
