from __future__ import annotations
from datetime import date
from decimal import Decimal
import typer
from rich.console import Console
from patur import db as dbmod
from patur.importers.leumi import parse_leumi_csv
from patur.importers.green_invoice import parse_green_invoice_csv
from patur.categorize import load_rules, categorize
from patur.rates import load_rates
from patur.reports import build_report
from patur.advances import recommend_advance

app = typer.Typer(help="עוסק פטור personal accountant")
console = Console()

def _ingest(path: str, db: str, parser) -> int:
    conn = dbmod.connect(db)
    dbmod.init_schema(conn)
    rules = load_rules()
    txs = [categorize(t, rules) for t in parser(open(path, encoding="utf-8-sig").read())]
    n = dbmod.insert_transactions(conn, txs)
    console.print(f"[green]Imported {n} new transactions.[/green]")
    return n

@app.command("import-leumi")
def import_leumi(path: str, db: str = "patur.db"):
    _ingest(path, db, parse_leumi_csv)

@app.command("import-green-invoice")
def import_green_invoice(path: str, db: str = "patur.db"):
    _ingest(path, db, parse_green_invoice_csv)

@app.command("status")
def status(db: str = "patur.db", year: int = 2026,
           pension: str = "0", points: str = "2.25"):
    conn = dbmod.connect(db)
    dbmod.init_schema(conn)
    txs = dbmod.all_transactions(conn)
    rep = build_report(txs, Decimal(pension), Decimal(points), load_rates(year))
    uncat = sum(1 for t in txs if t.category == "uncategorized")
    def _ils(x):
        return x.quantize(Decimal("0.01"))
    console.print(f"הכנסה נטו (net income):   {_ils(rep.ledger.net_income)}")
    console.print(f"מס הכנסה (income tax):    {_ils(rep.liability.income_tax)}")
    console.print(f"ביטוח לאומי:              {_ils(rep.liability.bituach_leumi)}")
    console.print(f"[bold]סה\"כ לתשלום (total due): {_ils(rep.liability.total_due)}[/bold]")
    pct = (rep.ceiling.pct_used * 100).quantize(Decimal('0.1'))
    flag = "  ⚠️" if rep.ceiling.alert else ""
    console.print(f"ניצול תקרת פטור:          {pct}%{flag}")
    if uncat:
        console.print(f"[yellow]{uncat} תנועות לא מסווגות (uncategorized)[/yellow]")
    for w in rep.liability.pension.warnings:
        console.print(f"[yellow]⚠️  {w}[/yellow]")

@app.command("advance")
def advance(db: str = "patur.db", year: int = 2026, as_of: str = "",
            pension: str = "0", points: str = "2.25", months: int = 3):
    conn = dbmod.connect(db); dbmod.init_schema(conn)
    txs = dbmod.all_transactions(conn)
    ref = date.fromisoformat(as_of) if as_of else date.today()
    rec = recommend_advance(txs, ref, load_rates(year), Decimal(pension),
                            Decimal(points), months)
    console.print(f"ממוצע {months} חודשים (avg monthly net):  {rec.avg_monthly_net}")
    console.print(f"תחזית שנתית (projected annual net):     {rec.projected_annual_net}")
    console.print(f"[bold]מקדמה חודשית מומלצת (monthly advance): {rec.monthly_advance}[/bold]")
