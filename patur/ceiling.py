# patur/ceiling.py
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
from patur.rates import RatesYear

@dataclass(frozen=True)
class CeilingStatus:
    ytd_revenue: Decimal
    ceiling: Decimal
    pct_used: Decimal
    alert: bool
    breached: bool

def ceiling_status(ytd_revenue: Decimal, rates: RatesYear,
                   warn_at: Decimal = Decimal("0.8")) -> CeilingStatus:
    pct = ytd_revenue / rates.patur_ceiling
    return CeilingStatus(ytd_revenue, rates.patur_ceiling, pct,
                         pct >= warn_at, ytd_revenue > rates.patur_ceiling)
