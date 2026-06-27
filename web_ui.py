from __future__ import annotations
import base64
import io
import json
import os
from datetime import date, datetime
from decimal import Decimal

from flask import Flask, render_template_string, request, redirect, url_for, flash
from patur import db as dbmod
from patur.importers.leumi import parse_leumi_csv
from patur.importers.green_invoice import parse_green_invoice_csv
from patur.categorize import load_rules, categorize
from patur.rates import load_rates
from patur.reports import build_report
from patur.advances import recommend_advance
from patur.models import Transaction, Direction

app = Flask(__name__)
app.secret_key = "patur-local-ui"

DB_PATH = "patur.db"
CONFIG_PATH = "patur_config.json"

def _load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    return {}

def _save_config(cfg):
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f)

HTML = """
<!DOCTYPE html>
<html dir="rtl" lang="he">
<head>
<meta charset="utf-8">
<title>עוסק פטור — לוח בקרה</title>
<style>
  body { font-family: Arial, sans-serif; max-width: 900px; margin: 40px auto; padding: 0 20px; background: #f5f5f5; color: #222; }
  h1 { color: #1a5276; border-bottom: 2px solid #1a5276; padding-bottom: 8px; }
  h2 { color: #1a5276; margin-top: 32px; }
  .card { background: white; border-radius: 8px; padding: 24px; margin-bottom: 24px; box-shadow: 0 2px 6px rgba(0,0,0,0.1); }
  .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
  label { display: block; margin-bottom: 4px; font-weight: bold; font-size: 0.9em; }
  input[type=text], input[type=number], input[type=file], input[type=password] { width: 100%; padding: 8px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; margin-bottom: 12px; }
  button { background: #1a5276; color: white; border: none; padding: 10px 24px; border-radius: 4px; cursor: pointer; font-size: 1em; }
  button:hover { background: #154360; }
  .btn-ai { background: #7d3c98; }
  .btn-ai:hover { background: #6c3483; }
  .stat { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #eee; font-size: 1.05em; }
  .stat:last-child { border-bottom: none; }
  .stat .val { font-weight: bold; }
  .alert { background: #fdecea; border: 1px solid #e74c3c; border-radius: 4px; padding: 10px 16px; margin-top: 12px; color: #c0392b; }
  .warn  { background: #fef9e7; border: 1px solid #f39c12; border-radius: 4px; padding: 10px 16px; margin-top: 12px; color: #7d6608; }
  .ok    { background: #eafaf1; border: 1px solid #27ae60; border-radius: 4px; padding: 10px 16px; margin-top: 12px; color: #1e8449; }
  .flash-msg { padding: 10px 16px; border-radius: 4px; margin-bottom: 16px; background: #d6eaf8; border: 1px solid #2e86c1; color: #1a5276; }
  .ai-badge { display: inline-block; background: #7d3c98; color: white; font-size: 0.75em; padding: 2px 8px; border-radius: 10px; margin-right: 6px; vertical-align: middle; }
  .parsed-preview { background: #f9f0ff; border: 1px solid #c39bd3; border-radius: 4px; padding: 12px; margin-top: 12px; font-size: 0.9em; }
  .key-hint { font-size: 0.8em; color: #888; margin-top: -8px; margin-bottom: 12px; }
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

<!-- AI Vision Section -->
<div class="card">
  <h2><span class="ai-badge">AI</span> סריקת מסמכים חכמה</h2>
  <p style="color:#555; margin-top:0">העלה תמונת קבלה, חשבונית, PDF או אימייל — הבינה המלאכותית תחלץ את הנתונים ותוסיף אותם אוטומטית.</p>

  <!-- API Key settings -->
  <form method="post" action="/save-api-key" style="margin-bottom:20px">
    <label>מפתח API של Anthropic</label>
    <input type="password" name="api_key" placeholder="sk-ant-..." value="{{ api_key_set and '••••••••' or '' }}">
    <div class="key-hint">המפתח נשמר באופן מקומי בקובץ patur_config.json בלבד. <a href="https://console.anthropic.com/settings/keys" target="_blank">קבל מפתח</a></div>
    <button type="submit">שמור מפתח</button>
  </form>

  <!-- Document upload -->
  <form method="post" action="/parse-document" enctype="multipart/form-data">
    <label>העלה מסמך (תמונה / PDF / טקסט)</label>
    <input type="file" name="file" accept="image/*,.pdf,.txt,.eml" required {{ not api_key_set and 'disabled' or '' }}>
    {% if not api_key_set %}
    <div class="warn">⚠️ הגדר מפתח API לפני שימוש בסריקה חכמה</div>
    {% endif %}
    <br>
    <button type="submit" class="btn-ai" {{ not api_key_set and 'disabled' or '' }}>🤖 סרוק וייבא ▶</button>
  </form>

  {% if parsed_result %}
  <div class="parsed-preview">
    <strong>תוצאת סריקה:</strong><br>
    {% for item in parsed_result %}
    ✓ {{ item.date }} | {{ item.description }} | {{ item.direction }} | ₪{{ item.amount }}<br>
    {% endfor %}
  </div>
  {% endif %}
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
    cfg = _load_config()
    return render_template_string(HTML, result=None, parsed_result=None,
                                  api_key_set=bool(cfg.get("anthropic_api_key")))

@app.route("/save-api-key", methods=["POST"])
def save_api_key():
    key = request.form.get("api_key", "").strip()
    if key and not key.startswith("•"):
        cfg = _load_config()
        cfg["anthropic_api_key"] = key
        _save_config(cfg)
        flash("מפתח API נשמר בהצלחה ✓")
    return redirect(url_for("index"))

@app.route("/parse-document", methods=["POST"])
def parse_document():
    cfg = _load_config()
    api_key = cfg.get("anthropic_api_key")
    if not api_key:
        flash("לא הוגדר מפתח API")
        return redirect(url_for("index"))

    f = request.files.get("file")
    if not f:
        flash("לא נבחר קובץ")
        return redirect(url_for("index"))

    filename = f.filename.lower()
    raw = f.read()

    try:
        import anthropic
    except ImportError:
        flash("חסר חבילת anthropic — הרץ: pip install anthropic")
        return redirect(url_for("index"))

    client = anthropic.Anthropic(api_key=api_key)

    PROMPT = """You are an Israeli bookkeeping assistant. Extract ALL financial transactions from this document.
For each transaction return a JSON array where each item has:
- "date": "DD/MM/YYYY"
- "description": short Hebrew or English description
- "amount": numeric string (positive number only)
- "direction": "IN" for income/credit, "OUT" for expense/debit

Return ONLY valid JSON array, no explanation. Example:
[{"date":"15/06/2026","description":"תשלום לקוח","amount":"1500","direction":"IN"}]

If no transactions found, return [].
"""

    # Build message content based on file type
    content: list = []

    if filename.endswith((".jpg", ".jpeg", ".png", ".gif", ".webp")):
        media_type = "image/jpeg" if filename.endswith((".jpg", ".jpeg")) else \
                     "image/png" if filename.endswith(".png") else \
                     "image/gif" if filename.endswith(".gif") else "image/webp"
        b64 = base64.standard_b64encode(raw).decode()
        content = [
            {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": b64}},
            {"type": "text", "text": PROMPT},
        ]
    elif filename.endswith(".pdf"):
        b64 = base64.standard_b64encode(raw).decode()
        content = [
            {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": b64}},
            {"type": "text", "text": PROMPT},
        ]
    else:
        # plain text / email
        text_content = raw.decode("utf-8", errors="replace")
        content = [{"type": "text", "text": f"{PROMPT}\n\nDocument content:\n{text_content}"}]

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            messages=[{"role": "user", "content": content}],
            betas=["pdfs-2024-09-25"] if filename.endswith(".pdf") else [],
        )
        raw_json = response.content[0].text.strip()
        # strip markdown code fences if present
        if raw_json.startswith("```"):
            raw_json = raw_json.split("```")[1]
            if raw_json.startswith("json"):
                raw_json = raw_json[4:]
        items = json.loads(raw_json)
    except Exception as e:
        flash(f"שגיאה בסריקה: {e}")
        return redirect(url_for("index"))

    if not items:
        flash("לא נמצאו תנועות במסמך")
        return redirect(url_for("index"))

    conn = _get_conn()
    rules = load_rules()
    txs = []
    ext_prefix = os.path.splitext(filename)[0][:20]
    for i, item in enumerate(items):
        try:
            d = datetime.strptime(item["date"].strip(), "%d/%m/%Y").date()
            amt = Decimal(str(item["amount"]).replace(",", ""))
            direction = Direction.IN if item["direction"] == "IN" else Direction.OUT
            tx = Transaction(
                date=d,
                direction=direction,
                amount=amt,
                description=item.get("description", "").strip(),
                source="ai_vision",
                external_id=f"ai:{ext_prefix}:{i}",
                category="הכנסה" if direction == Direction.IN else "הוצאה",
            )
            txs.append(categorize(tx, rules))
        except Exception:
            continue

    n = dbmod.insert_transactions(conn, txs)

    parsed_display = [
        {"date": t.date.strftime("%d/%m/%Y"),
         "description": t.description,
         "direction": "הכנסה" if t.direction == Direction.IN else "הוצאה",
         "amount": str(t.amount)}
        for t in txs
    ]

    flash(f"סריקה הצליחה — נוספו {n} תנועות חדשות מהמסמך 🤖")
    cfg2 = _load_config()
    return render_template_string(HTML, result=None,
                                  parsed_result=parsed_display,
                                  api_key_set=bool(cfg2.get("anthropic_api_key")))

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
    cfg = _load_config()
    return render_template_string(HTML, result=result, parsed_result=None,
                                  api_key_set=bool(cfg.get("anthropic_api_key")))

if __name__ == "__main__":
    app.run(debug=False, port=5050)
