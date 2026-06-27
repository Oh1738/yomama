from pathlib import Path
from typer.testing import CliRunner
from patur.cli import app

runner = CliRunner()

def test_import_handles_bom(tmp_path):
    db = tmp_path / "bom.db"
    gi = tmp_path / "gi_bom.csv"
    # encoding="utf-8-sig" writes a leading BOM, as real Windows exports do
    gi.write_text("מספר מסמך,תאריך,סכום,לקוח\n"
                  "7001,10/03/2026,60000.00,לקוח\n", encoding="utf-8-sig")
    r1 = runner.invoke(app, ["import-green-invoice", str(gi), "--db", str(db)])
    assert r1.exit_code == 0, r1.output
    r2 = runner.invoke(app, ["status", "--db", str(db), "--year", "2026"])
    assert r2.exit_code == 0, r2.output
    assert "60000" in r2.output.replace(",", "")

def test_import_then_status(tmp_path: Path):
    # Income comes from Green Invoice; Leumi provides expenses only (Fix 1).
    db = tmp_path / "t.db"
    gi = tmp_path / "gi.csv"
    gi.write_text("מספר מסמך,תאריך,סכום,לקוח\n"
                  "8001,05/01/2026,100000.00,לקוח\n", encoding="utf-8")
    r1 = runner.invoke(app, ["import-green-invoice", str(gi), "--db", str(db)])
    assert r1.exit_code == 0, r1.output
    r2 = runner.invoke(app, ["status", "--db", str(db), "--year", "2026"])
    assert r2.exit_code == 0, r2.output
    assert "100000" in r2.output.replace(",", "")
