# patur — עוסק פטור Personal Accountant (v1)

A local, offline CLI that does ~90% of what an accountant does for a single Israeli
**עוסק פטור** (exempt dealer): imports your bank + invoicing data, keeps the books, and
continuously computes income tax (incl. פנסיה §47/§45א), ביטוח לאומי, your exemption-ceiling
status, filing deadlines, and a recommended monthly **מקדמה** from your trailing 3-month average.

It **prepares**; a human reviews and files. It never submits anything and never leaves your machine.

> ⚠️ **Tax rates are UNVERIFIED placeholders.** `rates/2026.json` has best-effort 2026 values
> marked `"_verified": false`. The *engine logic* is tested and correct; the *numbers* must be
> confirmed against רשות המסים / המוסד לביטוח לאומי before you trust any figure for a real filing.

## Quick start (Windows)

You need Python 3.11+ ([python.org](https://www.python.org/downloads/), tick *"Add python.exe to PATH"*).

Open **PowerShell** in this folder and run:

```powershell
py -m venv .venv
.venv\Scripts\activate
pip install -e .
pip install pytest
```

Then use it (works from any folder once installed — data files are package-anchored):

```powershell
patur import-green-invoice path\to\receipts.csv --db patur.db
patur import-leumi        path\to\bank.csv      --db patur.db
patur status   --db patur.db --year 2026 --pension 0 --points 2.25
patur advance  --db patur.db --year 2026 --months 3
```

macOS/Linux is identical except activation: `source .venv/bin/activate`.

Run the test suite anytime: `pytest -q` (49 tests).

## What goes where (v1 income model)

- **Green Invoice export → income.** Your issued קבלות are the source of truth for revenue.
- **Leumi CSV → expenses only.** Bank debits become deductible expenses (after categorization).
  Bank *credits are ignored* in v1 so income isn't double-counted. (Reconciling the two bank
  deposits against issued receipts is a v2 feature.)

### Expected CSV columns (assumptions — adjust the importer if your export differs)
- **Green Invoice:** `מספר מסמך,תאריך,סכום,לקוח` — dates `dd/mm/yyyy`.
- **Leumi:** `תאריך,תיאור,חובה,זכות,יתרה` — dates `dd/mm/yyyy`. Files are read BOM-safe (`utf-8-sig`).

Edit categorization rules in `rules/default.json` (first matching substring wins; unmatched
expenses show as *uncategorized* in `status`).

## What it computes

| Command | Output |
|---|---|
| `status`  | net income, income tax (brackets − credit points − §45א credit), ביטוח לאומי, total due, % of the 122,833 ₪ ceiling, uncategorized count, pension warnings |
| `advance` | recommended monthly מקדמה = trailing-N-month avg net → annualized → tax engine → ÷12 |

The pension benefit models both Israeli mechanisms: the **§47 ניכוי** (11% deduction, reduces
taxable income) and the **§45א זיכוי** (5% slice at a 35% credit), capped at 16.5% of eligible
income. `status --pension <amount>` shows the effect and warns if you contribute past the cap.

## Project layout

```
patur/            # the package (deterministic core — money is always Decimal, never float)
  importers/      #   leumi.py, green_invoice.py
  tax_engine/     #   income_tax.py, pension.py, bituach_leumi.py, engine.py
  ledger.py ceiling.py obligations.py reports.py advances.py categorize.py db.py rates.py cli.py
rates/2026.json   # statutory values (VERIFY before real use)
rules/default.json# expense categorization rules
tests/            # 49 tests incl. a golden-year end-to-end regression anchor
docs/specs/       # design spec   docs/superpowers/plans/ # the implementation plan
```

## Status & roadmap

**v1 (this build):** import → categorize → ledger → tax engine (income tax + פנסיה + ביטוח לאומי)
→ ceiling watchdog → obligations → reports → מקדמות advice, as a local CLI over SQLite.

**Deferred to v2:** receipt photo/PDF OCR (`extract-doc`), bank↔receipt reconciliation, draft
filing assembly (הצהרה/1301), conversational advisor, year-end deduction audit, live open-banking.

*Not tax or legal advice. A licensed accountant should review before you file.*
