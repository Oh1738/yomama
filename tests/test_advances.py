# tests/test_advances.py
from datetime import date
from decimal import Decimal
from patur.models import Transaction, Direction
from patur.rates import load_rates
from patur.tax_engine.engine import compute_liability
from patur.advances import recommend_advance, _window_start

R = load_rates(2026)

def inc(d, amt):
    return Transaction(date=d, direction=Direction.IN, amount=Decimal(amt),
                       description="x", source="gi", external_id=f"{d}{amt}")

def test_window_start_three_months():
    assert _window_start(date(2026, 6, 30), 3) == date(2026, 4, 1)

def test_window_start_crosses_year():
    # 3-month window ending Feb 2026 -> starts Dec 2025
    assert _window_start(date(2026, 2, 15), 3) == date(2025, 12, 1)

def test_trailing_average_annualizes_then_divides():
    txs = [inc(date(2026,4,10),"10000"), inc(date(2026,5,10),"10000"),
           inc(date(2026,6,10),"10000")]
    rec = recommend_advance(txs, date(2026,6,30), R, Decimal("0"), Decimal("2.25"))
    assert rec.avg_monthly_net == Decimal("10000")
    assert rec.projected_annual_net == Decimal("120000")
    expected = (compute_liability(Decimal("120000"), Decimal("0"), Decimal("2.25"), R)
                .income_tax / Decimal("12")).quantize(Decimal("0.01"))
    assert rec.monthly_advance == expected

def test_only_window_counts():
    txs = [inc(date(2026,1,10),"99999"),          # outside the 3-month window
           inc(date(2026,4,10),"6000"), inc(date(2026,5,10),"6000"),
           inc(date(2026,6,10),"6000")]
    rec = recommend_advance(txs, date(2026,6,30), R, Decimal("0"), Decimal("2.25"))
    assert rec.window_net == Decimal("18000")

def test_advance_cli(tmp_path):
    from typer.testing import CliRunner
    from patur.cli import app
    db = tmp_path / "t.db"; gi = tmp_path / "gi.csv"
    gi.write_text("מספר מסמך,תאריך,סכום,לקוח\n"
                  "1,10/04/2026,10000.00,a\n2,10/05/2026,10000.00,b\n"
                  "3,10/06/2026,10000.00,c\n", encoding="utf-8")
    runner = CliRunner()
    assert runner.invoke(app, ["import-green-invoice", str(gi), "--db", str(db)]).exit_code == 0
    r = runner.invoke(app, ["advance", "--db", str(db), "--year", "2026",
                            "--as-of", "2026-06-30"])
    assert r.exit_code == 0, r.output
    assert "מקדמה" in r.output
