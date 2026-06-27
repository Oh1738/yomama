from __future__ import annotations
import io
import os
from datetime import date
from decimal import Decimal

from flask import Flask, render_template_string, request, redirect, url_for, flash
from patur import db as dbmod
from patur.importers.leumi import parse_leumi_csv
from patur.importers.green_invoice import parse_green_invoice_csv
from patur.categorize import load_rules, categorize
from patur.rates import load_rates
from patur.reports import build_report
from patur.advances import recommend_advance

app = Flask(__name__)
app.secret_key = "patur-local-ui"

DB_PATH = "patur.db"

HTML = """
<!DOCTYPE html>
<html dir="rtl" lang="he">
<head>
<meta charset="utf-8">
<title>עוסק פטור — לוח בקרה</title>
<style>
  body { font-family: Arial, sans-serif; max-width: 860px; margin: 40px auto; padding: 0 20px; background: #f5f5f5; color: #222; }
  h1 { color: #1a5276; border-bottom: 2px solid #1a5276; padding-bottom: 8px; }
  h2 { color: #1a5276; margin-top: 32px; }
  .card { background: white; border-radius: 8px; padding: 24px; margin-bottom: 24px; box-shadow: 0 2px 6px rgba(0,0,0,0.1); }
  .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
  label { display: block; margin-bottom: 4px; font-weight: bold; font-size: 0.9em; }
  input[type=text], input[type=number], input[type=file] { width: 100%; padding: 8px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; margin-bottom: 12px; }
  button { background: #1a5276; color: white; border: none; padding: 10px 24px; border-radius: 4px; cursor: pointer; font-size: 1em; }
  button:hover { background: #154360; }
  .stat { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #eee; font-size: 1.05em; }
  .stat:last-child { border-bottom: none; }
  .stat .val { font-weight: bold; }
  .alert { background: #fdecea; border: 1px solid #e74c3c; border-radius: 4px; padding: 10px 16px; margin-top: 12px; color: #c0392b; }
  .warn  { background: #fef9e7; border: 1px solid #f39c12; border-radius: 4px; padding: 10px 16px; margin-top: 12px; color: #7d6608; }
  .ok    { background: #eafaf1; border: 1px solid #27ae60; border-radius: 4px; padding: 10px 16px; margin-top: 12px; color: #1e8449; }
  .flash-msg { padding: 10px 16px; border-radius: 4px; margin-bottom: 16px; background: #d6eaf8; border: 1px solid #2e86c1; color: #1a5276; }
</style>
</head>
<body>
<h1>🧾 עוסק פטור — לוח בקרה</h1>

{% for msg in get_flashed_messages() %}
<div class="flash-msg">{{ msg }}</div>
{% endfor %}

<div class="grid">

  <div class="card">
    <h2>ייבוא נתונים</h2>
    <form method="post" action="/import-green-invoice" enctype="multipart/form-data">
      <label>Green Invoice CSV (הכנסות)</label>
      <input type="file" name="file" accept=".csv" required>
      <button type="submit">ייבא חשבוניות ▶</button>
    </form>
    <hr style="margin:20px 0">
    <form method="post" action="/import-leumi" enctype="multipart/form-data">
      <label>בנק לאומי CSV (הוצאות)</label>
      <input type="file" name="file" accept=".csv" required>
      <button type="submit">ייבא בנק ▶</button>
    </form>
  </div>

  <div class="card">
    <h2>הגדרות</h2>
    <form method="post" action="/status">
      <label>שנת מס</label>
      <input type="number" name="year" value="2026" min="2024" max="2030">
      <label>פנסיה ששולמה (₪)</label>
      <input type="text" name="pension" value="0">
      <label>נקודות זיכוי</label>
      <input type="text" name="points" value="2.25">
      <label>חודשים לחישוב מקדמה</label>
      <input type="number" name="months" value="3" min="1" max="12">
      <button type="submit">חשב סטטוס ▶</button>
    </form>
  </div>

</div>

{% if result %}
<div class="card">
  <h2>סטטוס מס</h2>
  <div class="stat"><span>הכנסה נטו</span><span class="val">{{ result.net_income }} ₪</span></div>
  <div class="stat"><span>מס הכנסה</span><span class="val">{{ result.income_tax }} ₪</span></div>
  <div class="stat"><span>ביטוח לאומי</span><span class="val">{{ result.bituach_leumi }} ₪</span></div>
  <div class="stat"><span><strong>סה"כ לתשלום</strong></span><span class="val"><strong>{{ result.total_due }} ₪</strong></span></div>
  <div class="stat"><span>ניצול תקרת פטור</span><span class="val">{{ result.ceiling_pct }}%</span></div>
  <div class="stat"><span>תנועות לא מסווגות</span><span class="val">{{ result.uncat }}</span></div>

  {% if result.ceiling_alert %}
  <div class="alert">⚠️ עברת 80% מתקרת הפטור (₪122,833)!</div>
  {% endif %}

  {% for w in result.pension_warnings %}
  <div class="warn">⚠️ {{ w }}</div>
  {% endfor %}

  {% if result.advance %}
  <hr style="margin:20px 0">
  <h2>מקדמה מומלצת</h2>
  <div class="stat"><span>ממוצע חודשי נטו</span><span class="val">{{ result.advance.avg }} ₪</span></div>
  <div class="stat"><span>תחזית שנתית</span><span class="val">{{ result.advance.annual }} ₪</span></div>
  <div class="stat"><span><strong>מקדמה חודשית מומלצת</strong></span><span class="val"><strong>{{ result.advance.monthly }} ₪</strong></span></div>
  {% endif %}
</div>
{% endif %}

</body>
</html>
"""

def _q(x):
    return x.quantize(Decimal("0.01"))

def _get_conn():
    conn = dbmod.connect(DB_PATH)
    dbmod.init_schema(conn)
    return conn

@app.route("/")
def index():
    return render_template_string(HTML, result=None)

@app.route("/import-green-invoice", methods=["POST"])
def import_green_invoice():
    f = request.files.get("file")
    if not f:
        flash("לא נבחר קובץ")
        return redirect(url_for("index"))
    text = f.read().decode("utf-8-sig")
    conn = _get_conn()
    rules = load_rules()
    txs = [categorize(t, rules) for t in parse_green_invoice_csv(text)]
    n = dbmod.insert_transactions(conn, txs)
    flash(f"יובאו {n} חשבוניות חדשות מ-Green Invoice")
    return redirect(url_for("index"))

@app.route("/import-leumi", methods=["POST"])
def import_leumi():
    f = request.files.get("file")
    if not f:
        flash("לא נבחר קובץ")
        return redirect(url_for("index"))
    text = f.read().decode("utf-8-sig")
    conn = _get_conn()
    rules = load_rules()
    txs = [categorize(t, rules) for t in parse_leumi_csv(text)]
    n = dbmod.insert_transactions(conn, txs)
    flash(f"יובאו {n} תנועות חדשות מבנק לאומי")
    return redirect(url_for("index"))

@app.route("/status", methods=["POST"])
def status():
    year = int(request.form.get("year", 2026))
    pension = Decimal(request.form.get("pension", "0"))
    points = Decimal(request.form.get("points", "2.25"))
    months = int(request.form.get("months", 3))

    conn = _get_conn()
    txs = dbmod.all_transactions(conn)
    rates = load_rates(year)
    rep = build_report(txs, pension, points, rates)
    uncat = sum(1 for t in txs if t.category == "uncategorized")

    advance = None
    try:
        rec = recommend_advance(txs, date.today(), rates, pension, points, months)
        advance = {
            "avg": _q(rec.avg_monthly_net),
            "annual": _q(rec.projected_annual_net),
            "monthly": _q(rec.monthly_advance),
        }
    except Exception:
        pass

    result = {
        "net_income": _q(rep.ledger.net_income),
        "income_tax": _q(rep.liability.income_tax),
        "bituach_leumi": _q(rep.liability.bituach_leumi),
        "total_due": _q(rep.liability.total_due),
        "ceiling_pct": (rep.ceiling.pct_used * 100).quantize(Decimal("0.1")),
        "ceiling_alert": rep.ceiling.alert,
        "uncat": uncat,
        "pension_warnings": rep.liability.pension.warnings,
        "advance": advance,
    }
    return render_template_string(HTML, result=result)

if __name__ == "__main__":
    app.run(debug=False, port=5050)
